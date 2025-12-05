from typing import Optional

from sqlalchemy import (
    Column,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from biokb_coconut import constants


class Base(DeclarativeBase):
    table_prefix = constants.PROJECT_NAME + "_"


# abstract base class for tables with only unique name field
class OnlyName:
    __tablename__: str
    id: Mapped[int]
    name: Mapped[str]
    compounds: Mapped[list["Compound"]]


# many-to-many association tables
class CompoundOrganism(Base):
    __tablename__ = Base.table_prefix + "compound_organism"

    compound_id: Mapped[int] = mapped_column(
        ForeignKey(Base.table_prefix + "compound.id"), primary_key=True
    )
    organism_id: Mapped[int] = mapped_column(
        ForeignKey(Base.table_prefix + "organism.id"), primary_key=True
    )


class CompoundCollection(Base):
    __tablename__ = Base.table_prefix + "compound_collection"

    compound_id: Mapped[int] = mapped_column(
        ForeignKey(Base.table_prefix + "compound.id"), primary_key=True
    )
    collection_id: Mapped[int] = mapped_column(
        ForeignKey(Base.table_prefix + "collection.id"), primary_key=True
    )


class CompoundSynonym(Base):
    __tablename__ = Base.table_prefix + "compound_synonym"

    compound_id: Mapped[int] = mapped_column(
        ForeignKey(Base.table_prefix + "compound.id"), primary_key=True
    )
    synonym_id: Mapped[int] = mapped_column(
        ForeignKey(Base.table_prefix + "synonym.id"), primary_key=True
    )


class CompoundCAS(Base):
    __tablename__ = Base.table_prefix + "compound_cas"

    compound_id: Mapped[int] = mapped_column(
        ForeignKey(Base.table_prefix + "compound.id"), primary_key=True
    )
    cas_number_id: Mapped[int] = mapped_column(
        ForeignKey(Base.table_prefix + "cas.id"), primary_key=True
    )


class CompoundDOI(Base):
    __tablename__ = Base.table_prefix + "compound_doi"

    compound_id: Mapped[int] = mapped_column(
        ForeignKey(Base.table_prefix + "compound.id"), primary_key=True
    )
    doi_id: Mapped[int] = mapped_column(
        ForeignKey(Base.table_prefix + "doi.id"), primary_key=True
    )


# other tables
class Compound(Base):
    __tablename__ = Base.table_prefix + "compound"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    identifier: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    canonical_smiles: Mapped[str] = mapped_column(Text)
    standard_inchi: Mapped[str] = mapped_column(Text)
    standard_inchi_key: Mapped[str] = mapped_column(String(32))
    name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    iupac_name: Mapped[Optional[str]] = mapped_column(Text)
    annotation_level: Mapped[int]
    total_atom_count: Mapped[int]
    heavy_atom_count: Mapped[int]
    molecular_weight: Mapped[float]
    exact_molecular_weight: Mapped[float]
    molecular_formula: Mapped[str] = mapped_column(String(255))
    alogp: Mapped[float]
    topological_polar_surface_area: Mapped[float]
    rotatable_bond_count: Mapped[int]
    hydrogen_bond_acceptors: Mapped[int]
    hydrogen_bond_donors: Mapped[int]
    hydrogen_bond_acceptors_lipinski: Mapped[int]
    hydrogen_bond_donors_lipinski: Mapped[int]
    lipinski_rule_of_five_violations: Mapped[int]
    aromatic_rings_count: Mapped[int]
    qed_drug_likeliness: Mapped[float]
    formal_charge: Mapped[int]
    fractioncsp3: Mapped[float]
    number_of_minimal_rings: Mapped[int]
    van_der_walls_volume: Mapped[Optional[float]]
    contains_sugar: Mapped[Optional[bool]]
    contains_ring_sugars: Mapped[bool]
    contains_linear_sugars: Mapped[bool]
    murcko_framework: Mapped[Optional[str]] = mapped_column(Text)
    np_likeness: Mapped[float]
    np_classifier_pathway_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey(Base.table_prefix + "np_classifier_pathway.id")
    )
    np_classifier_superclass_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey(Base.table_prefix + "np_classifier_superclass.id")
    )
    np_classifier_class_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey(Base.table_prefix + "np_classifier_class.id")
    )
    np_classifier_is_glycoside: Mapped[Optional[bool]]

    # foreign keys to classification tables
    chemical_class_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey(Base.table_prefix + "chemical_class.id")
    )
    chemical_sub_class_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey(Base.table_prefix + "chemical_sub_class.id")
    )
    direct_parent_classification_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey(Base.table_prefix + "direct_parent_classification.id")
    )
    chemical_super_class_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey(Base.table_prefix + "chemical_super_class.id")
    )
    # relationships
    chemical_class: Mapped[Optional["ChemicalClass"]] = relationship(
        back_populates="compounds"
    )
    chemical_sub_class: Mapped[Optional["ChemicalSubClass"]] = relationship(
        back_populates="compounds"
    )
    direct_parent_classification: Mapped[Optional["DirectParentClassification"]] = (
        relationship(back_populates="compounds")
    )
    chemical_super_class: Mapped[Optional["ChemicalSuperClass"]] = relationship(
        back_populates="compounds"
    )
    np_classifier_pathway: Mapped[Optional["NpClassifierPathway"]] = relationship(
        back_populates="compounds"
    )
    np_classifier_superclass: Mapped[Optional["NpClassifierSuperclass"]] = relationship(
        back_populates="compounds"
    )
    np_classifier_class: Mapped[Optional["NpClassifierClass"]] = relationship(
        back_populates="compounds"
    )

    organisms: Mapped[list["Organism"]] = relationship(
        secondary=CompoundOrganism.__table__, back_populates="compounds"
    )
    collections: Mapped[list["Collection"]] = relationship(
        secondary=CompoundCollection.__table__, back_populates="compounds"
    )
    dois: Mapped[list["DOI"]] = relationship(
        secondary=CompoundDOI.__table__, back_populates="compounds"
    )
    synonyms: Mapped[list["Synonym"]] = relationship(
        secondary=CompoundSynonym.__table__, back_populates="compounds"
    )
    cas_numbers: Mapped[list["CAS"]] = relationship(
        secondary=CompoundCAS.__table__, back_populates="compounds"
    )


class NpClassifierPathway(Base, OnlyName):
    __tablename__ = Base.table_prefix + "np_classifier_pathway"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)

    compounds: Mapped[list["Compound"]] = relationship(
        back_populates="np_classifier_pathway"
    )


class NpClassifierSuperclass(Base, OnlyName):
    __tablename__ = Base.table_prefix + "np_classifier_superclass"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)

    compounds: Mapped[list["Compound"]] = relationship(
        back_populates="np_classifier_superclass"
    )


class NpClassifierClass(Base, OnlyName):
    __tablename__ = Base.table_prefix + "np_classifier_class"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)

    compounds: Mapped[list["Compound"]] = relationship(
        back_populates="np_classifier_class"
    )


class ChemicalClass(Base, OnlyName):
    __tablename__ = Base.table_prefix + "chemical_class"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)

    compounds: Mapped[list["Compound"]] = relationship(back_populates="chemical_class")


class ChemicalSubClass(Base, OnlyName):
    __tablename__ = Base.table_prefix + "chemical_sub_class"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)

    compounds: Mapped[list["Compound"]] = relationship(
        back_populates="chemical_sub_class"
    )


class DirectParentClassification(Base, OnlyName):
    __tablename__ = Base.table_prefix + "direct_parent_classification"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)

    compounds: Mapped[list["Compound"]] = relationship(
        back_populates="direct_parent_classification"
    )


class ChemicalSuperClass(Base, OnlyName):
    __tablename__ = Base.table_prefix + "chemical_super_class"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)

    compounds: Mapped[list["Compound"]] = relationship(
        back_populates="chemical_super_class"
    )


class DOI(Base):
    __tablename__ = Base.table_prefix + "doi"

    id: Mapped[int] = mapped_column(primary_key=True)
    identifier: Mapped[str] = mapped_column(
        String(255).with_variant(String(255, collation="utf8mb4_bin"), "mysql"),
        unique=True,
    )
    compounds: Mapped[list["Compound"]] = relationship(
        secondary=CompoundDOI.__table__, back_populates="dois"
    )


class Synonym(Base):
    __tablename__ = Base.table_prefix + "synonym"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(1000).with_variant(String(1000, collation="utf8mb4_bin"), "mysql")
    )
    compounds: Mapped[list["Compound"]] = relationship(
        secondary=CompoundSynonym.__table__, back_populates="synonyms"
    )
    __table_args__ = (Index("uq_my_model_name", "name", unique=True, mysql_length=768),)


class Organism(Base):
    __tablename__ = Base.table_prefix + "organism"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(1000).with_variant(
            String(length=1000, collation="utf8mb4_bin"), "mysql"
        ),
    )
    tax_id: Mapped[Optional[int]] = mapped_column(index=True)
    ipni_id: Mapped[Optional[str]] = mapped_column(String(255))
    wcvp_id: Mapped[Optional[int]]
    powo_id: Mapped[Optional[str]] = mapped_column(String(255))
    compounds: Mapped[list["Compound"]] = relationship(
        secondary=CompoundOrganism.__table__, back_populates="organisms"
    )

    __table_args__ = (
        Index(
            f"ux_{__tablename__}__name",
            name,
            mysql_length=255,
        ),
    )


class Collection(Base):
    __tablename__ = Base.table_prefix + "collection"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(255).with_variant(String(255, collation="utf8mb4_bin"), "mysql"),
        unique=True,
    )
    compounds: Mapped[list["Compound"]] = relationship(
        secondary=CompoundCollection.__table__, back_populates="collections"
    )

    @property
    def compound_identifiers(self):
        return [compound.identifier for compound in self.compounds]


class CAS(Base):
    __tablename__ = Base.table_prefix + "cas"

    id = Column(Integer, primary_key=True)
    number = Column(
        String(255).with_variant(String(255, collation="utf8mb4_bin"), "mysql"),
        unique=True,
    )
    compounds: Mapped[list["Compound"]] = relationship(
        secondary=CompoundCAS.__table__, back_populates="cas_numbers"
    )


class TaxonomyName(Base):
    """Class definition for table taxonomy_name. Name from
    NCBI taxonomy https://www.ncbi.nlm.nih.gov/taxonomys."""

    __tablename__ = Base.table_prefix + "taxonomy_name"
    __table_args__ = {"comment": "Taxonomy names by NCBI"}
    id: Mapped[int] = mapped_column(primary_key=True)
    tax_id: Mapped[int] = mapped_column(index=True, comment="NCBI taxonomy Identifier")
    name: Mapped[str] = mapped_column(Text)
    name_type: Mapped[str] = mapped_column(String(255), index=True)

    __table_args__ = (
        Index(
            f"ix_{__tablename__}__name",
            name,
            mysql_length=255,
        ),
    )


class WCVPPlant(Base):
    __tablename__ = Base.table_prefix + "wcvp_plant"
    plant_name_id: Mapped[int] = mapped_column(primary_key=True)
    taxon_name: Mapped[Optional[str]] = mapped_column(Text)
    accepted_plant_name_id: Mapped[Optional[int]] = mapped_column(index=True)
    powo_id: Mapped[Optional[str]] = mapped_column(String(255))
    ipni_id: Mapped[Optional[str]] = mapped_column(String(255))

    __table_args__ = (
        Index(
            f"ix_{__tablename__}__taxon_name",
            taxon_name,
            mysql_length=255,
        ),
    )
