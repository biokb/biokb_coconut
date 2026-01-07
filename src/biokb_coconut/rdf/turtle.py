"""Module to create RDF turtle files from the WCVP
(World Checklist of Vascular Plants) data.

This module provides functionality to export taxonomic and geographic data from a
SQL database into RDF Turtle format, suitable for semantic web applications and
knowledge graphs.

Compound Filtering Rationale:

The compound filtering is based on drug-likeness criteria derived from Lipinski's
Rule of Five and additional pharmaceutical parameters. Compounds are excluded when
they violate multiple drug-likeness criteria.

Exclusion Criteria:

• lipinski_rule_of_five_violations > 1: Multiple violations indicate poor
    drug-like behavior and unfavorable absorption/distribution properties

• molecular_weight > 500 Da: Follows Lipinski's rule. Larger compounds exhibit
    poor absorption and cannot cross biological membranes effectively

• hydrogen_bond_donors_lipinski > 5: Excessive hydrogen bonding prevents
    effective lipid bilayer crossing and reduces membrane permeability

• hydrogen_bond_acceptors_lipinski > 10: Too many acceptor sites increase
    polarity and impair passive diffusion through cellular membranes

• alogp > 5: Excessive lipophilicity causes poor aqueous solubility and
    potential toxicity issues while affecting formulation stability

• topological_polar_surface_area > 140 Ų: Values above this threshold
    typically indicate poor passive absorption and membrane permeability

• qed_drug_likeliness < 0.67: Low drug quality estimation combining multiple
    molecular descriptors to predict drug-like characteristics

Pharmaceutical Impact:

• Poor absorption: Multiple violations predict inadequate passive diffusion
    across intestinal epithelium

• Low skin penetration: Compounds exceeding 500 Da cannot effectively traverse
    the stratum corneum barrier

• High polarity issues: Excessive hydrogen bonding prevents lipid bilayer
    crossing

• Excessive lipophilicity: Poor solubility and potential toxicity concerns

• Low permeability: TPSA above 140 Ų strongly correlates with poor membrane
    passage

• Overall low drug quality: QED below 0.67 indicates unfavorable drug-like
    characteristics
"""

import logging
import os.path
import re
import shutil
from typing import List, Optional, Sequence, Type, TypeVar

from rdflib import RDF, XSD, Graph, Literal, Namespace, URIRef
from sqlalchemy import Engine, create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.elements import ColumnElement
from tqdm import tqdm

from biokb_coconut import constants
from biokb_coconut.constants import BASIC_NODE_LABEL, EXPORT_FOLDER
from biokb_coconut.db import models
from biokb_coconut.rdf import namespaces

logger = logging.getLogger(__name__)


# Type variable for SQLAlchemy model classes
BaseModels = TypeVar("BaseModels", bound=models.Base)


def get_namespace(model_name: str) -> Namespace:
    """Generate an RDF namespace for a given SQLAlchemy model class.

    Args:
        model: SQLAlchemy model class to generate namespace for.

    Returns:
        RDF Namespace object with URI based on the model's class name.
    """
    return Namespace(f"{namespaces.BASE_URI}/{model_name}#")


def get_empty_graph() -> Graph:
    graph = Graph()
    # Bind generic ontology namespaces
    graph.bind(prefix="comp", namespace=namespaces.COMP_NS)
    graph.bind(prefix="rel", namespace=namespaces.REL_NS)
    graph.bind(prefix="xs", namespace=XSD)
    graph.bind(prefix="n", namespace=namespaces.NODE_NS)
    graph.bind(prefix="inchi", namespace=namespaces.INCHI_NS)
    graph.bind(prefix="cc", namespace=namespaces.CHEMICAL_CLASS_NS)
    graph.bind(prefix="cs", namespace=namespaces.CHEMICAL_SUB_CLASS_NS)
    graph.bind(prefix="cu", namespace=namespaces.CHEMICAL_SUPER_CLASS_NS)
    graph.bind(
        prefix="dpc",
        namespace=namespaces.DIRECT_PARENT_CLASSIFICATION_NS,
    )
    graph.bind(prefix="ncp", namespace=namespaces.NP_CLASSIFIER_PATHWAY_NS)
    graph.bind(
        prefix="ncs",
        namespace=namespaces.NP_CLASSIFIER_SUPERCLASS_NS,
    )
    graph.bind(prefix="npc", namespace=namespaces.NP_CLASSIFIER_CLASS_NS)
    graph.bind(prefix="wcvp", namespace=namespaces.WCVP_PLANT_NS)
    graph.bind(prefix="ncbi", namespace=namespaces.NCBI_TAXON_NS)
    graph.bind(prefix="ipni", namespace=namespaces.IPNI_NS)

    return graph


def get_rel_name(model: Type[models.OnlyName]) -> str:
    """
    Convert a SQLAlchemy model class name to a relationship name in uppercase snake
    case with underscores.

    Prefixing with "HAS_"

    Args:
        model (Type[models.Base]): A SQLAlchemy model class
    Returns:
        str: The relationship name in the format "HAS_<UPPERCASE_WITH_UNDERSCORES>"
    Examples:
        >>> get_rel_name(UserProfile)
        'HAS_USER_PROFILE'
    """

    name = model.__name__
    for match in re.findall(r"([A-Z]{2}[a-z])", name):
        name = f"{match[0]}_{match[1:]}".join(name.split(match))
    for match in re.findall(r"([a-z][A-Z])", name):
        name = f"{match[0]}_{match[1]}".join(name.split(match))
    return "HAS_" + name.upper()


class TurtleCreator:
    """Factory class for generating RDF Turtle files from WCVP database.

    This class handles the export of plant taxonomic data and geographic distributions
    from a relational database into RDF Turtle format for use in semantic
    web applications.
    """

    compound_filter: Sequence[ColumnElement[bool]] = (
        models.Compound.lipinski_rule_of_five_violations <= 1,
        models.Compound.hydrogen_bond_donors_lipinski <= 5,
        models.Compound.hydrogen_bond_acceptors_lipinski <= 10,
        models.Compound.molecular_weight <= 500,
        models.Compound.alogp <= 5,
        models.Compound.qed_drug_likeliness >= 0.67,
        models.Compound.topological_polar_surface_area <= 140,
    )

    def __init__(
        self,
        engine: Engine | None = None,
    ):
        self.__ttls_folder = EXPORT_FOLDER
        connection_str = os.getenv(
            "CONNECTION_STR", constants.DB_DEFAULT_CONNECTION_STR
        )
        self.__engine = engine if engine else create_engine(str(connection_str))
        self.Session = sessionmaker(bind=self.__engine)

    def _set_ttls_folder(self, export_to_folder: str) -> None:
        """Sets the export folder path.

        This is mainly for testing purposes.
        """
        self.__ttls_folder = export_to_folder

    def create_ttls(self) -> str:
        """Generate RDF Turtle files from the database.
        Returns:
            Path to the zip file containing all generated Turtle files.
        """
        logging.info("Starting turtle file generation process.")
        os.makedirs(self.__ttls_folder, exist_ok=True)
        self._create_compounds()
        self._create_only_name_classes()
        self._create_organisms_with_links()

        # Package everything into a zip file
        path_to_zip_file: str = self._create_zip_from_all_ttls()
        logging.info(f"Turtle files successfully packaged in {path_to_zip_file}")
        return path_to_zip_file

    def _create_organisms_with_links(self) -> None:
        logging.info("Creating RDF organisms turtle file.")
        org_ns = get_namespace(models.Organism.__name__)
        graph = get_empty_graph()
        graph.bind(prefix="o", namespace=org_ns)

        with self.Session() as session:
            # Query only accepted plant names (not synonyms)
            organisms: List[models.Organism] = (
                session.query(models.Organism)
                .join(models.Organism.compounds)
                .where(*self.compound_filter)
                .all()
            )

            for organism in tqdm(organisms, desc="Creating organisms triples"):

                org: URIRef = org_ns[str(organism.id)]
                # Add type declarations
                graph.add(
                    triple=(
                        org,
                        RDF.type,
                        namespaces.NODE_NS[models.Organism.__name__],
                    )
                )
                graph.add(triple=(org, RDF.type, namespaces.NODE_NS[BASIC_NODE_LABEL]))
                graph.add(
                    triple=(
                        org,
                        namespaces.REL_NS["name"],
                        Literal(organism.name, datatype=XSD.string),
                    )
                )
                if organism.wcvp_id:
                    graph.add(
                        triple=(
                            org,
                            namespaces.REL_NS["SAME_AS"],
                            namespaces.WCVP_PLANT_NS[str(organism.wcvp_id)],
                        )
                    )
                if organism.tax_id:
                    graph.add(
                        triple=(
                            org,
                            namespaces.REL_NS["SAME_AS"],
                            namespaces.NCBI_TAXON_NS[str(organism.tax_id)],
                        )
                    )
                if organism.ipni_id:
                    graph.add(
                        triple=(
                            org,
                            namespaces.REL_NS["SAME_AS"],
                            namespaces.IPNI_NS[str(organism.ipni_id)],
                        )
                    )

            stmt = (
                select(models.Organism.id, models.Compound.identifier)
                .select_from(models.Compound)
                .join(models.Compound.organisms)
                .where(*self.compound_filter)
            )

            rows = session.execute(stmt).all()
            # link compounds
            for row in tqdm(rows, desc="Creating compound/organism link triples"):
                graph.add(
                    triple=(
                        org_ns[str(row.id)],
                        namespaces.REL_NS["HAS_COMPOUND"],
                        namespaces.COMP_NS[str(row.identifier)],
                    )
                )

        ttl_path = os.path.join(
            self.__ttls_folder, f"{models.Organism.__tablename__}.ttl"
        )
        graph.serialize(ttl_path, format="turtle")
        del graph

    def __create_only_name_class(
        self, model: Type[models.OnlyName], add_node_label: str | None = None
    ) -> None:

        logging.info(f"Creating RDF {model.__name__} classifiers turtle file.")
        model_namespace = get_namespace(model.__name__)
        graph = Graph()
        graph.bind(prefix="r", namespace=namespaces.REL_NS)
        graph.bind(prefix="x", namespace=XSD)
        graph.bind(prefix="e", namespace=model_namespace)
        graph.bind(prefix="n", namespace=namespaces.NODE_NS)
        graph.bind(prefix="c", namespace=namespaces.COMP_NS)

        with self.Session() as session:

            rows_model = session.query(model.id, model.name).all()

            for row in tqdm(rows_model, desc=f"Creating {model.__name__} triples"):
                # uri
                ent: URIRef = model_namespace[str(row.id)]
                # type declarations
                graph.add(triple=(ent, RDF.type, namespaces.NODE_NS[BASIC_NODE_LABEL]))
                graph.add(
                    triple=(
                        ent,
                        RDF.type,
                        namespaces.NODE_NS[model.__name__],
                    )
                )
                graph.add(triple=(ent, RDF.type, namespaces.NODE_NS[BASIC_NODE_LABEL]))
                # properties
                graph.add(
                    triple=(
                        ent,
                        namespaces.REL_NS["name"],
                        Literal(row.name, datatype=XSD.string),
                    )
                )

            # link compounds

            stmt = (
                select(
                    models.ChemicalClass.id.label("model_id"),
                    models.Compound.identifier.label("compound_identifier"),
                )
                .select_from(models.Compound)
                .join(models.ChemicalClass)
                .where(*self.compound_filter)
            )
            rows_compound_link = session.execute(stmt).all()

            for model_id, compound_identifier in tqdm(
                rows_compound_link,
                desc=f"Creating compound/{model.__name__} link triples",
            ):
                # compounds
                graph.add(
                    triple=(
                        namespaces.COMP_NS[str(compound_identifier)],
                        namespaces.REL_NS[get_rel_name(model)],
                        model_namespace[str(model_id)],
                    )
                )

        ttl_path = os.path.join(self.__ttls_folder, f"{model.__tablename__}.ttl")
        graph.serialize(ttl_path, format="turtle")
        del graph

    def _create_only_name_classes(self) -> None:
        list_of_models: List[Type[models.OnlyName]] = [
            models.ChemicalClass,
            models.ChemicalSubClass,
            models.ChemicalSuperClass,
            models.DirectParentClassification,
            models.NpClassifierPathway,
            models.NpClassifierSuperclass,
            models.NpClassifierClass,
        ]
        for model in list_of_models:
            self.__create_only_name_class(model)

    def _create_compounds(self) -> None:
        logging.info("Creating RDF compounds turtle file.")
        graph = get_empty_graph()

        with self.Session() as session:
            # Query only accepted plant names (not synonyms)
            compounds: List[models.Compound] = (
                session.query(models.Compound).where(*self.compound_filter).all()
            )

            for compound in tqdm(compounds, desc="Creating compounds triples"):
                comp: URIRef = namespaces.COMP_NS[str(compound.identifier)]
                # Add type declarations
                graph.add(
                    triple=(
                        comp,
                        RDF.type,
                        namespaces.NODE_NS[models.Compound.__name__],
                    )
                )
                graph.add(triple=(comp, RDF.type, namespaces.NODE_NS[BASIC_NODE_LABEL]))
                graph.add(
                    triple=(
                        comp,
                        namespaces.REL_NS["iupac_name"],
                        Literal(compound.iupac_name, datatype=XSD.string),
                    )
                )
                graph.add(
                    triple=(
                        comp,
                        namespaces.REL_NS["SAME_AS"],
                        namespaces.INCHI_NS[compound.standard_inchi_key],
                    )
                )
                for property in [
                    "hydrogen_bond_acceptors_lipinski",
                    "hydrogen_bond_donors_lipinski",
                    "lipinski_rule_of_five_violations",
                    "np_likeness",
                    "qed_drug_likeliness",
                    "topological_polar_surface_area",
                    "molecular_weight",
                    "alogp",
                ]:
                    value = getattr(compound, property)
                    if value is not None:
                        graph.add(
                            triple=(
                                comp,
                                namespaces.REL_NS[property],
                                Literal(value, datatype=XSD.float),
                            )
                        )

        ttl_path = os.path.join(self.__ttls_folder, "coconut_compounds.ttl")
        graph.serialize(ttl_path, format="turtle")
        del graph

    def _create_zip_from_all_ttls(self) -> str:
        """Package all generated turtle files into a single zip archive.

        Creates a zip file containing all .ttl files in the export folder,
        then removes the temporary turtle files directory to clean up.

        Returns:
            Path to the created zip file.
        """
        logger.info("Packaging turtle files into zip archive.")

        # Create zip archive from all turtle files
        path_to_zip_file = shutil.make_archive(
            base_name=self.__ttls_folder, format="zip", root_dir=self.__ttls_folder
        )

        # Clean up temporary turtle files directory
        shutil.rmtree(self.__ttls_folder)

        return path_to_zip_file


def create_ttls(
    engine: Optional[Engine] = None,
    export_to_folder: Optional[str] = None,
) -> str:
    """Create all turtle files.

    If engine=None tries to get the settings from config ini file

    If export_to_folder=None takes the default path.

    Args:
        engine (Engine | None, optional): SQLAlchemy class. Defaults to None.
        export_to_folder (str | None, optional): Folder to export ttl files.
            Defaults to None.

    Returns:
        str: path zipped file with ttls.
    """
    ttl_creator = TurtleCreator(engine=engine)
    if export_to_folder:
        ttl_creator._set_ttls_folder(export_to_folder)
    return ttl_creator.create_ttls()
