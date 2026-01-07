import logging
import os
import secrets
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Generator, Sequence, Tuple

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy import Engine, create_engine, select
from sqlalchemy.engine.row import Row
from sqlalchemy.orm import Session

from biokb_coconut.api import schemas
from biokb_coconut.api.query_tools import SASearchResults, build_dynamic_query
from biokb_coconut.api.tags import Tag
from biokb_coconut.constants import (
    DB_DEFAULT_CONNECTION_STR,
    NEO4J_PASSWORD,
    NEO4J_URI,
    NEO4J_USER,
    ZIPPED_TTLS_PATH,
)
from biokb_coconut.db import manager, models
from biokb_coconut.rdf.neo4j_importer import Neo4jImporter
from biokb_coconut.rdf.turtle import TurtleCreator

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

USERNAME = os.environ.get("API_USERNAME", "admin")
PASSWORD = os.environ.get("API_PASSWORD", "admin")


def get_engine() -> Engine:
    conn_url = os.environ.get("CONNECTION_STR", DB_DEFAULT_CONNECTION_STR)
    engine: Engine = create_engine(conn_url)
    return engine


def get_session() -> Generator[Session, None, None]:
    engine: Engine = get_engine()
    session = Session(bind=engine)
    try:
        yield session
    finally:
        session.close()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize app resources on startup and cleanup on shutdown."""
    engine = get_engine()
    manager.DbManager(engine)
    yield
    # Clean up resources if needed
    pass


description = (
    """A RESTful API for Coconut. Reference: https://coconut.naturalproducts.net/"""
)

app = FastAPI(
    title="RESTful API for Coconut",
    description=description,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


def run_server(host: str = "0.0.0.0", port: int = 8000) -> None:
    uvicorn.run(
        app="biokb_coconut.api.main:app",
        host=host,
        port=port,
        log_level="warning",
    )


def verify_credentials(
    credentials: HTTPBasicCredentials = Depends(HTTPBasic()),
) -> None:
    is_correct_username = secrets.compare_digest(credentials.username, USERNAME)
    is_correct_password = secrets.compare_digest(credentials.password, PASSWORD)
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


# tag: Database Management
# ========================


@app.post(
    path="/import_data/",
    response_model=dict[str, int],
    tags=[Tag.DBMANAGE],
)
async def import_data(
    credentials: HTTPBasicCredentials = Depends(verify_credentials),
    force_download: bool = Query(
        False,
        description=(
            "Whether to re-download data files even if they already exist,"
            " ensuring the newest version."
        ),
    ),
    keep_files: bool = Query(
        True,
        description=(
            "Whether to keep the downloaded files"
            " after importing them into the database."
        ),
    ),
) -> dict[str, int]:
    """Download data (if not exists) and load in database.

    Can take up to 15 minutes to complete.
    """
    try:
        dbm = manager.DbManager()
        result = dbm.import_data(force_download=force_download, keep_files=keep_files)
    except Exception as e:
        logger.error(f"Error importing data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error importing data. {e}",
        ) from e
    return result


@app.get("/export_ttls/", tags=[Tag.DBMANAGE])
async def get_report(
    credentials: HTTPBasicCredentials = Depends(verify_credentials),
    force_create: bool = Query(
        False,
        description="Whether to re-generate the TTL files even if they already exist.",
    ),
) -> FileResponse:

    file_path = ZIPPED_TTLS_PATH
    if not os.path.exists(file_path) or force_create:
        try:
            TurtleCreator().create_ttls()
        except Exception as e:
            logger.error(f"Error generating TTL files: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error generating TTL files. Data already imported?",
            ) from e
    return FileResponse(
        path=file_path, filename="chebi_ttls.zip", media_type="application/zip"
    )


@app.get("/import_neo4j/", tags=[Tag.DBMANAGE])
async def import_neo4j(
    credentials: HTTPBasicCredentials = Depends(verify_credentials),
    uri: str | None = Query(
        NEO4J_URI,
        description="The Neo4j URI. If not provided, "
        "the default from environment variable is used.",
    ),
    user: str | None = Query(
        NEO4J_USER,
        description="The Neo4j user. If not provided,"
        " the default from environment variable is used.",
    ),
    password: str | None = Query(
        NEO4J_PASSWORD,
        description="The Neo4j password. If not provided,"
        " the default from environment variable is used.",
    ),
) -> dict[str, str]:
    """Import RDF turtle files in Neo4j."""
    try:
        if not os.path.exists(ZIPPED_TTLS_PATH):
            raise HTTPException(
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                detail=(
                    "Zipped TTL files not found. Please "
                    "generate them first using /export_ttls/ endpoint."
                ),
            )
        importer = Neo4jImporter(neo4j_uri=uri, neo4j_user=user, neo4j_pwd=password)
        importer.import_ttls()
    except Exception as e:
        logger.error(f"Error importing data into Neo4j: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error importing data into Neo4j: {e}",
        ) from e
    return {"status": "Neo4j import completed successfully."}


# tag: Compound
# ========================


@app.get(
    "/compounds/", response_model=schemas.CompoundSearchResult, tags=[Tag.COMPOUND]
)
async def search_compounds(
    search: schemas.CompoundSearch = Depends(),
    session: Session = Depends(get_session),
) -> SASearchResults | dict[str, str]:
    """
    Search compounds. Returns a list of compounds with their DOIs,
    synonyms, organisms, collections, and CAS numbers.
    """
    return build_dynamic_query(
        search_obj=search,
        model_cls=models.Compound,
        db=session,
    )


@app.get("/compound/", response_model=schemas.CompoundBase, tags=[Tag.COMPOUND])
async def get_compound(
    session: Session = Depends(get_session),
    identifier: str = Query(..., description="Compound identifier"),
) -> models.Compound | None:
    """
    Search compounds. Returns a list of compounds with their DOIs,
    synonyms, organisms, collections, and CAS numbers.
    """
    return (
        session.query(models.Compound)
        .where(models.Compound.identifier == identifier)
        .first()
    )


@app.get("/dois/", response_model=schemas.DOISearchResult, tags=[Tag.COMPOUND])
async def search_dois(
    search: schemas.DOISearch = Depends(),
    session: Session = Depends(get_session),
) -> SASearchResults | dict[str, str]:
    """
    Search DOIs. Returns a list of DOIs with their compounds.
    """
    return build_dynamic_query(
        search_obj=search,
        model_cls=models.DOI,
        db=session,
    )


@app.get(
    "/organisms/", response_model=schemas.OrganismSearchResult, tags=[Tag.COMPOUND]
)
async def search_organisms(
    search: schemas.OrganismSearch = Depends(),
    session: Session = Depends(get_session),
) -> SASearchResults | dict[str, str]:
    """
    Search organisms. Returns a list of organisms with their compounds.
    """
    return build_dynamic_query(
        search_obj=search,
        model_cls=models.Organism,
        db=session,
    )


@app.get("/synonyms/", response_model=schemas.SynonymSearchResult, tags=[Tag.COMPOUND])
async def search_synonyms(
    search: schemas.SynonymSearch = Depends(),
    session: Session = Depends(get_session),
) -> SASearchResults | dict[str, str]:
    """
    Search synonyms. Returns a list of synonyms with their compounds.
    """
    return build_dynamic_query(
        search_obj=search,
        model_cls=models.Synonym,
        db=session,
    )


@app.get(
    "/collections/", response_model=schemas.CollectionSearchResult, tags=[Tag.COMPOUND]
)
async def search_collections(
    search: schemas.CollectionSearch = Depends(),
    session: Session = Depends(get_session),
) -> SASearchResults | dict[str, str]:
    """
    Search collections. Returns a list of collections with their compound identifiers.
    """
    return build_dynamic_query(
        search_obj=search,
        model_cls=models.Collection,
        db=session,
    )


@app.get("/collections/names", response_model=list[schemas.Name], tags=[Tag.COMPOUND])
async def get_collection_names(
    session: Session = Depends(get_session),
    id: int | None = Query(
        None, description="Optional collection ID to filter results"
    ),
    name: str | None = Query(
        None, description="Optional collection name to filter results"
    ),
) -> Sequence[Row[Tuple[int, str]]]:
    """
    Returns a list of collection names.
    """
    stmt = select(models.Collection.id, models.Collection.name)
    if id:
        stmt = stmt.where(models.Collection.id == id)
    if not id and name:
        stmt = stmt.where(models.Collection.name.ilike(name))
    result: Sequence[Row[Tuple[int, str]]] = session.execute(stmt).all()
    return result


@app.get("/cas/", response_model=schemas.CASSearchResult, tags=[Tag.COMPOUND])
async def search_cas(
    search: schemas.CASSearch = Depends(),
    session: Session = Depends(get_session),
) -> SASearchResults | dict[str, str]:
    """
    Search CAS numbers. Returns a list of CAS numbers with their compounds.
    """
    return build_dynamic_query(
        search_obj=search,
        model_cls=models.CAS,
        db=session,
    )


@app.get(
    "/chemical_class/",
    response_model=schemas.ChemicalClassSearchResult,
    tags=[Tag.COMPOUND],
)
async def search_chemical_class(
    search: schemas.ChemicalClassSearch = Depends(),
    session: Session = Depends(get_session),
) -> SASearchResults | dict[str, str]:
    """
    Search CAS numbers. Returns a list of CAS numbers with their compounds.
    """
    return build_dynamic_query(
        search_obj=search,
        model_cls=models.ChemicalClass,
        db=session,
    )


@app.get(
    "/chemical_class/names", response_model=list[schemas.Name], tags=[Tag.COMPOUND]
)
async def get_chemical_class_names(
    session: Session = Depends(get_session),
    id: int | None = Query(
        None, description="Optional chemical class ID to filter results"
    ),
    name: str | None = Query(
        None, description="Optional chemical class name to filter results"
    ),
) -> Sequence[Row[Tuple[int, str]]]:
    """
    Returns a list of chemical class names.
    """
    stmt = select(models.ChemicalClass.id, models.ChemicalClass.name)
    if id:
        stmt = stmt.where(models.ChemicalClass.id == id)
    if not id and name:
        stmt = stmt.where(models.ChemicalClass.name.ilike(name))
    result: Sequence[Row[Tuple[int, str]]] = session.execute(stmt).all()
    return result


@app.get(
    "/chemical_sub_class/",
    response_model=schemas.ChemicalSubClassSearchResult,
    tags=[Tag.COMPOUND],
)
async def search_chemical_sub_class(
    search: schemas.ChemicalSubClassSearch = Depends(),
    session: Session = Depends(get_session),
) -> SASearchResults | dict[str, str]:
    """
    Search chemical sub classes. Returns a list of chemical sub classes
    with their compounds.
    """
    return build_dynamic_query(
        search_obj=search,
        model_cls=models.ChemicalSubClass,
        db=session,
    )


@app.get(
    "/chemical_sub_class/names", response_model=list[schemas.Name], tags=[Tag.COMPOUND]
)
async def get_chemical_sub_class_names(
    session: Session = Depends(get_session),
    id: int | None = Query(
        None, description="Optional chemical sub class ID to filter results"
    ),
    name: str | None = Query(
        None, description="Optional chemical sub class name to filter results"
    ),
) -> Sequence[Row[Tuple[int, str]]]:
    """
    Returns a list of chemical sub class names.
    """
    stmt = select(models.ChemicalSubClass.id, models.ChemicalSubClass.name)
    if id:
        stmt = stmt.where(models.ChemicalSubClass.id == id)
    if not id and name:
        stmt = stmt.where(models.ChemicalSubClass.name.ilike(name))
    result: Sequence[Row[Tuple[int, str]]] = session.execute(stmt).all()
    return result


@app.get(
    "/direct_parent_classification/",
    response_model=schemas.DirectParentClassificationSearchResult,
    tags=[Tag.COMPOUND],
)
async def search_direct_parent_classification(
    search: schemas.DirectParentClassificationSearch = Depends(),
    session: Session = Depends(get_session),
) -> SASearchResults | dict[str, str]:
    """
    Search direct parent classifications. Returns a list of direct parent
    classifications with their compounds.
    """
    return build_dynamic_query(
        search_obj=search,
        model_cls=models.DirectParentClassification,
        db=session,
    )


@app.get(
    "/direct_parent_classification/names",
    response_model=list[schemas.Name],
    tags=[Tag.COMPOUND],
)
async def get_direct_parent_classification_names(
    session: Session = Depends(get_session),
    id: int | None = Query(
        None, description="Optional direct parent classification ID to filter results"
    ),
    name: str | None = Query(
        None, description="Optional direct parent classification name to filter results"
    ),
) -> Sequence[Row[Tuple[int, str]]]:
    """
    Returns a list of direct parent classification names.
    """

    stmt = select(
        models.DirectParentClassification.id, models.DirectParentClassification.name
    )
    if id:
        stmt = stmt.where(models.DirectParentClassification.id == id)
    if not id and name:
        stmt = stmt.where(models.DirectParentClassification.name.ilike(name))
    result: Sequence[Row[Tuple[int, str]]] = session.execute(stmt).all()
    return result


@app.get(
    "/chemical_super_class/",
    response_model=schemas.ChemicalSuperClassSearchResult,
    tags=[Tag.COMPOUND],
)
async def search_chemical_super_class(
    search: schemas.ChemicalSuperClassSearch = Depends(),
    session: Session = Depends(get_session),
) -> SASearchResults | dict[str, str]:
    """
    Search chemical super classes. Returns a list of chemical super classes
    with their compounds.
    """
    return build_dynamic_query(
        search_obj=search,
        model_cls=models.ChemicalSuperClass,
        db=session,
    )


@app.get(
    "/chemical_super_class/names",
    response_model=list[schemas.Name],
    tags=[Tag.COMPOUND],
)
async def get_chemical_super_class_names(
    session: Session = Depends(get_session),
    id: int | None = Query(
        None, description="Optional chemical super class ID to filter results"
    ),
    name: str | None = Query(
        None, description="Optional chemical super class name to filter results"
    ),
) -> Sequence[Row[Tuple[int, str]]]:
    """
    Returns a list of chemical super class names.
    """

    stmt = select(models.ChemicalSuperClass.id, models.ChemicalSuperClass.name)
    if id:
        stmt = stmt.where(models.ChemicalSuperClass.id == id)
    if not id and name:
        stmt = stmt.where(models.ChemicalSuperClass.name.ilike(name))
    result: Sequence[Row[Tuple[int, str]]] = session.execute(stmt).all()
    return result


@app.get(
    "/np_classifier_pathway/",
    response_model=schemas.NpClassifierPathwaySearchResult,
    tags=[Tag.COMPOUND],
)
async def search_np_classifier_pathway(
    search: schemas.NpClassifierPathwaySearch = Depends(),
    session: Session = Depends(get_session),
) -> SASearchResults | dict[str, str]:
    """
    Search NP classifier pathways. Returns a list of NP classifier
    pathways with their compounds.
    """
    return build_dynamic_query(
        search_obj=search,
        model_cls=models.NpClassifierPathway,
        db=session,
    )


@app.get(
    "/np_classifier_pathway/names",
    response_model=list[schemas.Name],
    tags=[Tag.COMPOUND],
)
async def get_np_classifier_pathway_names(
    session: Session = Depends(get_session),
    id: int | None = Query(
        None, description="Optional NP classifier pathway ID to filter results"
    ),
    name: str | None = Query(
        None, description="Optional NP classifier pathway name to filter results"
    ),
) -> Sequence[Row[Tuple[int, str]]]:
    """
    Returns a list of NP classifier pathway names.
    """

    stmt = select(models.NpClassifierPathway.id, models.NpClassifierPathway.name)
    if id:
        stmt = stmt.where(models.NpClassifierPathway.id == id)
    if not id and name:
        stmt = stmt.where(models.NpClassifierPathway.name.ilike(name))
    result: Sequence[Row[Tuple[int, str]]] = session.execute(stmt).all()
    return result


@app.get(
    "/np_classifier_superclass/",
    response_model=schemas.NpClassifierSuperclassSearchResult,
    tags=[Tag.COMPOUND],
)
async def search_np_classifier_superclass(
    search: schemas.NpClassifierSuperclassSearch = Depends(),
    session: Session = Depends(get_session),
) -> SASearchResults | dict[str, str]:
    """
    Search NP classifier superclasses. Returns a list of NP classifier superclasses with their compounds.
    """
    return build_dynamic_query(
        search_obj=search,
        model_cls=models.NpClassifierSuperclass,
        db=session,
    )


@app.get(
    "/np_classifier_superclass/names",
    response_model=list[schemas.Name],
    tags=[Tag.COMPOUND],
)
async def get_np_classifier_superclass_names(
    session: Session = Depends(get_session),
    id: int | None = Query(
        None, description="Optional NP classifier superclass ID to filter results"
    ),
    name: str | None = Query(
        None, description="Optional NP classifier superclass name to filter results"
    ),
) -> Sequence[Row[Tuple[int, str]]]:
    """
    Returns a list of NP classifier superclass names.
    """

    stmt = select(models.NpClassifierSuperclass.id, models.NpClassifierSuperclass.name)
    if id:
        stmt = stmt.where(models.NpClassifierSuperclass.id == id)
    if not id and name:
        stmt = stmt.where(models.NpClassifierSuperclass.name.ilike(name))
    result: Sequence[Row[Tuple[int, str]]] = session.execute(stmt).all()
    return result


@app.get(
    "/np_classifier_class/",
    response_model=schemas.NpClassifierClassSearchResult,
    tags=[Tag.COMPOUND],
)
async def search_np_classifier_class(
    search: schemas.NpClassifierClassSearch = Depends(),
    session: Session = Depends(get_session),
) -> SASearchResults | dict[str, str]:
    """
    Search NP classifier classes. Returns a list of NP classifier classes with their compounds.
    """
    return build_dynamic_query(
        search_obj=search,
        model_cls=models.NpClassifierClass,
        db=session,
    )


@app.get(
    "/np_classifier_class/names",
    response_model=list[schemas.Name],
    tags=[Tag.COMPOUND],
)
async def get_np_classifier_class_names(
    session: Session = Depends(get_session),
    id: int | None = Query(
        None, description="Optional NP classifier class ID to filter results"
    ),
    name: str | None = Query(
        None, description="Optional NP classifier class name to filter results"
    ),
) -> Sequence[Row[Tuple[int, str]]]:
    """
    Returns a list of NP classifier class names.
    """

    stmt = select(models.NpClassifierClass.id, models.NpClassifierClass.name)
    if id:
        stmt = stmt.where(models.NpClassifierClass.id == id)
    if not id and name:
        stmt = stmt.where(models.NpClassifierClass.name.ilike(name))
    result: Sequence[Row[Tuple[int, str]]] = session.execute(stmt).all()
    return result
