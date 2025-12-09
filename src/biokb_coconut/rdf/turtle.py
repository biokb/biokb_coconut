"""Module to create RDF turtle files from the WCVP (World Checklist of Vascular Plants) data.

This module provides functionality to export taxonomic and geographic data from a SQL database
into RDF Turtle format, suitable for semantic web applications and knowledge graphs.

Reasons for excluding compounds:

| COCONUT Parameter | Threshold for Very Low Potential | Related Lipinski Rule (Ro5) | Why it Hinders Wound Healing Drug Action |
| :--- | :--- | :--- | :--- |
| **`lipinski_rule_of_five_violations`** | $>= 2$ Violations | The overall rule compliance. | **Poor Absorption:** Two or more violations strongly predict that the molecule will be too large or too polar to achieve passive diffusion, resulting in very low concentrations reaching the deep dermis from topical application. |
| **`molecular_weight`** | $> 500$ Daltons (Da) | Molecular weight $<= 500$ Da. | **Low Skin Penetration:** Compounds over 500 Da generally cannot cross the **stratum corneum** (the outermost skin barrier) by passive diffusion, severely limiting their ability to reach the wound site. |
| **`hydrogen_bond_donors_lipinski` (HBD)** | $> 5$ | HBD $<= 5$. | **High Polarity/Desolvation:** Too many HBDs increase the energy needed for the molecule to shed its surrounding water molecules (desolvation), making it energetically unfavorable to partition into the lipid bilayer of cell membranes. |
| **`hydrogen_bond_acceptors_lipinski` (HBA)** | $> 10$ | HBA $<= 10$. | **High Polarity/Solubility:** Similar to HBD, too many acceptors anchor the molecule strongly to the aqueous environment, preventing it from crossing the lipid-rich barriers in the skin. |
| **`alogp`** | $> 5$ | $\text{cLogP} <= 5$. | **Excessive Lipophilicity:** While some lipophilicity is needed, an $\text{alogP}$ over 5 means the compound is too fat-soluble. This can lead to poor solubility in formulation vehicles and potential non-specific binding/accumulation in fatty tissues, leading to poor systemic availability or toxicity. |
| **`topological_polar_surface_area` (TPSA)** | $> 140 A°2 | Not directly in Ro5, but strongly related to HBD/HBA. | **Low Permeability:** TPSA quantifies the polar surface. Values over $140 A°^2 are strongly correlated with very poor passive permeability across biological membranes, including the skin. |
| **`qed_drug_likeliness`** | $< 0.67$ | Overall measure of drug quality. | **Low Overall Quality:** This score integrates the crucial physicochemical factors. A low score suggests the molecule possesses characteristics that make it significantly less "drug-like" compared to established medicines. |

Would you like me to use the search tool to find the actual Lipinski rule values for a specific natural product used in wound healing, like Curcumin?
"""

import logging
import os.path
import re
import shutil
from os import name
from typing import List, Type, TypeVar
from urllib.parse import urlparse

from rdflib import RDF, XSD, Graph, Literal, Namespace, URIRef
from sqlalchemy import Engine, create_engine, select
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm

logger = logging.getLogger(__name__)


from biokb_coconut import constants
from biokb_coconut.constants import BASIC_NODE_LABEL, TTL_EXPORT_FOLDER
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
    graph.bind(prefix="wcvp", namespace=namespaces.WCVP_PLANT_NS)
    graph.bind(prefix="ncbi", namespace=namespaces.NCBI_TAXON_NS)
    graph.bind(prefix="ipni", namespace=namespaces.IPNI_NS)

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

    compound_filter = (
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
        self.__ttls_folder = TTL_EXPORT_FOLDER
        connection_str = os.getenv(
            "CONNECTION_STR", constants.DB_DEFAULT_CONNECTION_STR
        )
        self.__engine = engine if engine else create_engine(str(connection_str))
        self.Session = sessionmaker(bind=self.__engine)

    def create_ttls(self) -> str:
        """Generate RDF Turtle files from the database.
        Returns:
            Path to the zip file containing all generated Turtle files.
        """
        logging.info("Starting turtle file generation process.")

        self._create_compounds()
        self._create_only_name_classes()
        self._create_organisms_with_links()

        # Package everything into a zip file
        path_to_zip_file: str = self._create_zip_from_all_ttls()
        logging.info(f"Turtle files successfully packaged in {path_to_zip_file}")
        return path_to_zip_file

    def _create_organisms_with_links(self):
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

    def _create_only_name_classes(self):
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

    def _create_compounds(self):
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
