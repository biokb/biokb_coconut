import logging
import os
import re
import secrets
from contextlib import asynccontextmanager
from typing import Annotated, Optional, get_args, get_origin

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from biokb_coconut.api import schemas
from biokb_coconut.api.query_tools import build_dynamic_query
from biokb_coconut.api.tags import Tag
from biokb_coconut.db import manager, models

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

USERNAME = os.environ.get("API_USERNAME", "admin")
PASSWORD = os.environ.get("API_PASSWORD", "admin")


def get_session():
    dbm = manager.DbManager()
    session: Session = dbm.Session()
    try:
        yield session
    finally:
        session.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # dbm.drop_db()
    dbm = manager.DbManager()
    dbm.create_db()
    yield
    # Clean up
    pass


description = (
    """A RESTful API for Coconut. Reference: https://coconut.naturalproducts.net/"""
)

app = FastAPI(
    title="RESTful API for Coconut",
    description=description,
    version="0.0.1",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


def verify_credentials(credentials: HTTPBasicCredentials = Depends(HTTPBasic())):
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


@app.get("/", tags=["Manage"])
def check_status() -> dict:
    return {"msg": "Running!"}


@app.post(path="/import_data/", tags=[Tag.DBMANAGE])
def import_data(
    credentials: HTTPBasicCredentials = Depends(verify_credentials),
):
    """Load a tsv file in database."""
    dbm = manager.DbManager()
    return dbm.import_data()


# tag: Compound
# ========================


@app.get(
    "/compounds/", response_model=schemas.CompoundSearchResult, tags=[Tag.COMPOUND]
)
async def search_compounds(
    search: schemas.CompoundSearch = Depends(),
    session: Session = Depends(get_session),
):
    """
    Search compounds. Returns a list of compounds with their DOIs,
    synonyms, organisms, collections, and CAS numbers.
    """
    return build_dynamic_query(
        search_obj=search,
        model_cls=models.Compound,
        db=session,
    )


@app.get("/dois/", response_model=schemas.DOISearchResult, tags=[Tag.COMPOUND])
async def search_dois(
    search: schemas.DOISearch = Depends(),
    session: Session = Depends(get_session),
):
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
):
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
):
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
):
    """
    Search collections. Returns a list of collections with their compound identifiers.
    """
    return build_dynamic_query(
        search_obj=search,
        model_cls=models.Collection,
        db=session,
    )


@app.get("/cas/", response_model=schemas.CASSearchResult, tags=[Tag.COMPOUND])
async def search_cas(
    search: schemas.CASSearch = Depends(),
    session: Session = Depends(get_session),
):
    """
    Search CAS numbers. Returns a list of CAS numbers with their compounds.
    """
    return build_dynamic_query(
        search_obj=search,
        model_cls=models.CAS,
        db=session,
    )
