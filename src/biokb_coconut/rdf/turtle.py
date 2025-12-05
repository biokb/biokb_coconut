"""Module to create RDF turtle files from the WCVP (World Checklist of Vascular Plants) data.

This module provides functionality to export taxonomic and geographic data from a SQL database
into RDF Turtle format, suitable for semantic web applications and knowledge graphs.
"""

import logging
import os.path
import re
import shutil
from os import name
from typing import List, Type, TypeVar
from urllib.parse import urlparse

from rdflib import RDF, XSD, Graph, Literal, Namespace, URIRef
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm

logger = logging.getLogger(__name__)


from biokb_coconut.constants import (
    BASIC_NODE_LABEL,
    DATA_FOLDER,
    EXPORT_FOLDER,
    TAXONOMY_URL,
)
from biokb_coconut.db import models
from biokb_coconut.rdf import namespaces

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

    return graph


def get_rel_name(model: Type[models.OnlyName]) -> str:
    """
    Convert a SQLAlchemy model class name to a relationship name in uppercase snake case with underscores.

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
    from a relational database into RDF Turtle format for use in semantic web applications.
    """

    def __init__(
        self,
        engine: Engine | None = None,
    ):
        self.__ttls_folder = EXPORT_FOLDER
        # Set up database engine and session factory
        self.__engine = engine
        self.Session = sessionmaker(bind=self.__engine)

    def create_ttls(self) -> str:
        logging.info("Starting turtle file generation process.")

        self.create_compounds()
        self.create_only_name_classes()

        # Package everything into a zip file
        path_to_zip_file: str = self.create_zip_from_all_ttls()
        logging.info(f"Turtle files successfully packaged in {path_to_zip_file}")
        return path_to_zip_file

    def create_organisms_with_links(self):
        logging.info("Creating RDF organisms turtle file.")
        org_ns = get_namespace(models.Organism.__name__)
        graph = get_empty_graph()
        graph.bind(prefix="o", namespace=org_ns)

        with self.Session() as session:
            # Query only accepted plant names (not synonyms)
            organisms: List[models.Organism] = session.query(models.Organism).all()

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
                            Literal(organism.tax_id, datatype=XSD.integer),
                        )
                    )
                # link compounds
                for compound in organism.compounds:
                    graph.add(
                        triple=(
                            org,
                            namespaces.REL_NS["HAS_COMPOUND"],
                            namespaces.COMP_NS[str(compound.identifier)],
                        )
                    )

        ttl_path = os.path.join(
            self.__ttls_folder, f"{models.Organism.__tablename__}.ttl"
        )
        graph.serialize(ttl_path, format="turtle")
        del graph

    def __create_only_name_class(
        self, model: Type[models.OnlyName], add_node_label: str | None = None
    ):

        logging.info(f"Creating RDF {model.__name__} classifiers turtle file.")
        model_namespace = get_namespace(model.__name__)
        graph = Graph()
        graph.bind(prefix="r", namespace=namespaces.REL_NS)
        graph.bind(prefix="x", namespace=XSD)
        graph.bind(prefix="e", namespace=model_namespace)
        graph.bind(prefix="n", namespace=namespaces.NODE_NS)
        graph.bind(prefix="c", namespace=namespaces.COMP_NS)

        with self.Session() as session:
            # Query all entities of model
            entities: List[models.OnlyName] = session.query(model).all()
            for entity in tqdm(entities, desc=f"Creating {model.__name__} triples"):
                # uri
                ent: URIRef = model_namespace[str(entity.id)]
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
                        Literal(entity.name, datatype=XSD.string),
                    )
                )
                # link compounds
                for compound in entity.compounds:
                    graph.add(
                        triple=(
                            namespaces.COMP_NS[str(compound.identifier)],
                            namespaces.REL_NS[get_rel_name(model)],
                            ent,
                        )
                    )

        ttl_path = os.path.join(self.__ttls_folder, f"{model.__tablename__}.ttl")
        graph.serialize(ttl_path, format="turtle")
        del graph

    def create_only_name_classes(self):
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

    def create_compounds(self):
        logging.info("Creating RDF compounds turtle file.")
        graph = get_empty_graph()

        with self.Session() as session:
            # Query only accepted plant names (not synonyms)
            compounds: List[models.Compound] = session.query(models.Compound).all()

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
                        namespaces.REL_NS["name"],
                        Literal(compound.name, datatype=XSD.string),
                    )
                )
                graph.add(
                    triple=(
                        comp,
                        namespaces.REL_NS["SAME_AS"],
                        namespaces.INCHI_NS[compound.standard_inchi_key],
                    )
                )
                if compound.chemical_class_id:
                    graph.add(
                        triple=(
                            comp,
                            namespaces.REL_NS["HAS_CHEMICAL_CLASSIFIER"],
                            namespaces.CHEMICAL_CLASS_NS[
                                str(compound.chemical_class_id)
                            ],
                        )
                    )
                if compound.chemical_sub_class_id:
                    graph.add(
                        triple=(
                            comp,
                            namespaces.REL_NS["HAS_CHEMICAL_CLASSIFIER"],
                            namespaces.CHEMICAL_SUB_CLASS_NS[
                                str(compound.chemical_sub_class_id)
                            ],
                        )
                    )
                if compound.chemical_super_class_id:
                    graph.add(
                        triple=(
                            comp,
                            namespaces.REL_NS["HAS_CHEMICAL_CLASSIFIER"],
                            namespaces.CHEMICAL_SUPER_CLASS_NS[
                                str(compound.chemical_super_class_id)
                            ],
                        )
                    )
                if compound.direct_parent_classification_id:
                    graph.add(
                        triple=(
                            comp,
                            namespaces.REL_NS["HAS_CHEMICAL_CLASSIFIER"],
                            namespaces.DIRECT_PARENT_CLASSIFICATION_NS[
                                str(compound.direct_parent_classification_id)
                            ],
                        )
                    )
                if compound.np_classifier_pathway_id:
                    graph.add(
                        triple=(
                            comp,
                            namespaces.REL_NS["HAS_NP_CLASSIFIER"],
                            namespaces.NP_CLASSIFIER_PATHWAY_NS[
                                str(compound.np_classifier_pathway_id)
                            ],
                        )
                    )
                if compound.np_classifier_superclass_id:
                    graph.add(
                        triple=(
                            comp,
                            namespaces.REL_NS["HAS_NP_CLASSIFIER"],
                            namespaces.NP_CLASSIFIER_SUPERCLASS_NS[
                                str(compound.np_classifier_superclass_id)
                            ],
                        )
                    )
                if compound.np_classifier_class_id:
                    graph.add(
                        triple=(
                            comp,
                            namespaces.REL_NS["HAS_NP_CLASSIFIER"],
                            namespaces.NP_CLASSIFIER_CLASS_NS[
                                str(compound.np_classifier_class_id)
                            ],
                        )
                    )

        ttl_path = os.path.join(self.__ttls_folder, "coconut_compounds.ttl")
        graph.serialize(ttl_path, format="turtle")
        del graph

    def create_zip_from_all_ttls(self) -> str:
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
