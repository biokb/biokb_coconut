"""This module contains the SQLAlchemy ORM models for the biokb_coconut database.

Each class in this module represents a table in the database, with attributes corresponding
to the columns of the table. Relationships between tables are defined using SQLAlchemy's
relationship function."""

from typing import Optional

from sqlalchemy import Column, ForeignKey, Index, Integer, String, Text
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
    """Joining table for Compound and Organism many-to-many relationship.

    Attributes:
        compound_id (int): Foreign key to the compound table.
        organism_id (int): Foreign key to the organism table.
    """

    __tablename__ = Base.table_prefix + "compound__organism"

    compound_id: Mapped[int] = mapped_column(
        ForeignKey(Base.table_prefix + "compound.id"), primary_key=True
    )
    organism_id: Mapped[int] = mapped_column(
        ForeignKey(Base.table_prefix + "organism.id"), primary_key=True
    )


class CompoundCollection(Base):
    """Joining table for Compound and Collection many-to-many relationship.

    Attributes:
        compound_id (int): Foreign key to the compound table.
        collection_id (int): Foreign key to the collection table.
    """

    __tablename__ = Base.table_prefix + "compound__collection"

    compound_id: Mapped[int] = mapped_column(
        ForeignKey(Base.table_prefix + "compound.id"), primary_key=True
    )
    collection_id: Mapped[int] = mapped_column(
        ForeignKey(Base.table_prefix + "collection.id"), primary_key=True
    )


class CompoundSynonym(Base):
    """Joining table for Compound and Synonym many-to-many relationship.

    Attributes:
        compound_id (int): Foreign key to the compound table.
        synonym_id (int): Foreign key to the synonym table.
    """

    __tablename__ = Base.table_prefix + "compound__synonym"

    compound_id: Mapped[int] = mapped_column(
        ForeignKey(Base.table_prefix + "compound.id"), primary_key=True
    )
    synonym_id: Mapped[int] = mapped_column(
        ForeignKey(Base.table_prefix + "synonym.id"), primary_key=True
    )


class CompoundCAS(Base):
    """Joining table for Compound and CAS many-to-many relationship.

    Attributes:
        compound_id (int): Foreign key to the compound table.
        cas_number_id (int): Foreign key to the cas table.
    """

    __tablename__ = Base.table_prefix + "compound_cas"

    compound_id: Mapped[int] = mapped_column(
        ForeignKey(Base.table_prefix + "compound.id"), primary_key=True
    )
    cas_number_id: Mapped[int] = mapped_column(
        ForeignKey(Base.table_prefix + "cas.id"), primary_key=True
    )


class CompoundDOI(Base):
    """Joining table for Compound and DOI many-to-many relationship.

    Attributes:
        compound_id (int): Foreign key to the compound table.
        doi_id (int): Foreign key to the doi table.
    """

    __tablename__ = Base.table_prefix + "compound_doi"

    compound_id: Mapped[int] = mapped_column(
        ForeignKey(Base.table_prefix + "compound.id"), primary_key=True
    )
    doi_id: Mapped[int] = mapped_column(
        ForeignKey(Base.table_prefix + "doi.id"), primary_key=True
    )


# other tables
class Compound(Base):
    """Class definition for table compound.

    Attributes:
        id (int): Primary key.
        identifier (str): Unique identifier for the compound.
        canonical_smiles (str): Canonical SMILES representation of the compound.
        standard_inchi (str): Standard InChI representation of the compound.
        standard_inchi_key (str): Standard InChI Key of the compound.
        name (Optional[str]): Name of the compound.
        iupac_name (Optional[str]): IUPAC name of the compound.
        annotation_level (int): Annotation level of the compound.
        total_atom_count (int): Total atom count of the compound.
        heavy_atom_count (int): Heavy atom count of the compound.
        molecular_weight (float): Molecular weight of the compound.
        exact_molecular_weight (float): Exact molecular weight of the compound.
        molecular_formula (str): Molecular formula of the compound.
        alogp (float): ALogP value of the compound.
        topological_polar_surface_area (float): Topological polar surface area of the compound.
        rotatable_bond_count (int): Rotatable bond count of the compound.
        hydrogen_bond_acceptors (int): Number of hydrogen bond acceptors.
        hydrogen_bond_donors (int): Number of hydrogen bond donors.
        hydrogen_bond_acceptors_lipinski (int): Number of hydrogen bond acceptors according to Lipinski's rule.
        hydrogen_bond_donors_lipinski (int): Number of hydrogen bond donors according to Lipinski's rule.
        lipinski_rule_of_five_violations (int): Number of Lipinski's rule of five violations.
        aromatic_rings_count (int): Aromatic rings count of the compound.
        qed_drug_likeliness (float): QED drug-likeliness score of the compound.
        formal_charge (int): Formal charge of the compound.
        fractioncsp3 (float): Fraction of sp3 hybridized carbons in the compound.
        number_of_minimal_rings (int): Number of minimal rings in the compound.
        van_der_walls_volume (Optional[float]): Van der Waals volume of the compound.
        contains_sugar (Optional[bool]): Indicates if the compound contains sugar.
        contains_ring_sugars (bool): Indicates if the compound contains ring sugars.
        contains_linear_sugars (bool): Indicates if the compound contains linear sugars.
        murcko_framework (Optional[str]): Murcko framework of the compound.
        np_likeness (float): Natural product-likeness score of the compound.
        np_classifier_is_glycoside (Optional[bool]): Indicates if the compound is classified as a glycoside by the NP classifier.
        chemical_class_id (Optional[int]): Foreign key to the chemical class table.
        chemical_sub_class_id (Optional[int]): Foreign key to the chemical sub-class table.
        direct_parent_classification_id (Optional[int]): Foreign key to the direct parent classification table.
        chemical_super_class_id (Optional[int]): Foreign key to the chemical super-class table.
        np_classifier_pathway_id (Optional[int]): Foreign key to the NP classifier pathway table.
        np_classifier_superclass_id (Optional[int]): Foreign key to the NP classifier superclass table.
        np_classifier_class_id (Optional[int]): Foreign key to the NP classifier class table.
        chemical_class (Optional[ChemicalClass]): Relationship to the chemical class.
        chemical_sub_class (Optional[ChemicalSubClass]): Relationship to the chemical sub-class.
        direct_parent_classification (Optional[DirectParentClassification]): Relationship to the direct parent classification.
        chemical_super_class (Optional[ChemicalSuperClass]): Relationship to the chemical super-class.
        np_classifier_pathway (Optional[NpClassifierPathway]): Relationship to the NP classifier pathway.
        np_classifier_superclass (Optional[NpClassifierSuperclass]): Relationship to the NP classifier superclass.
        np_classifier_class (Optional[NpClassifierClass]): Relationship to the NP classifier class.
        organisms (list[Organism]): List of organisms associated with the compound.
        collections (list[Collection]): List of collections associated with the compound.
        dois (list[DOI]): List of DOIs associated with the compound.
        synonyms (list[Synonym]): List of synonyms associated with the compound.
        cas_numbers (list[CAS]): List of CAS numbers associated with the compound.
    """

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
    np_classifier_pathway_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey(Base.table_prefix + "np_classifier_pathway.id")
    )
    np_classifier_superclass_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey(Base.table_prefix + "np_classifier_superclass.id")
    )
    np_classifier_class_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey(Base.table_prefix + "np_classifier_class.id")
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
    # many-to-many relationships
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

    def __repr__(self) -> str:
        return (
            f"<Compound(id={self.id}, name={self.name}, identifier={self.identifier})>"
        )


class NpClassifierPathway(Base, OnlyName):
    """Natural Product Classifier Pathway model.

    Attributes:
        id (int): Primary key.
        name (str): Unique name of the NP classifier pathway.
        compounds (list[Compound]): List of compounds associated with this pathway.
    """

    __tablename__ = Base.table_prefix + "np_classifier_pathway"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)

    compounds: Mapped[list["Compound"]] = relationship(
        back_populates="np_classifier_pathway"
    )

    @property
    def compound_identifiers(self) -> list[str]:
        return [compound.identifier for compound in self.compounds]

    def __repr__(self) -> str:
        return f"<NpClassifierPathway(id={self.id}, name={self.name})>"


class NpClassifierSuperclass(Base, OnlyName):
    """Natural Product Classifier Superclass model.

    Attributes:
        id (int): Primary key.
        name (str): Unique name of the NP classifier superclass.
        compounds (list[Compound]): List of compounds associated with this superclass.
    """

    __tablename__ = Base.table_prefix + "np_classifier_superclass"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)

    compounds: Mapped[list["Compound"]] = relationship(
        back_populates="np_classifier_superclass"
    )

    @property
    def compound_identifiers(self) -> list[str]:
        return [compound.identifier for compound in self.compounds]

    def __repr__(self) -> str:
        return f"<NpClassifierSuperclass(id={self.id}, name={self.name})>"


class NpClassifierClass(Base, OnlyName):
    """Natural Product Classifier Class model.

    Attributes:
        id (int): Primary key.
        name (str): Unique name of the NP classifier class.
        compounds (list[Compound]): List of compounds associated with this class.
    """

    __tablename__ = Base.table_prefix + "np_classifier_class"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)

    compounds: Mapped[list["Compound"]] = relationship(
        back_populates="np_classifier_class"
    )

    @property
    def compound_identifiers(self) -> list[str]:
        return [compound.identifier for compound in self.compounds]

    def __repr__(self) -> str:
        return f"<NpClassifierClass(id={self.id}, name={self.name})>"


class ChemicalClass(Base, OnlyName):
    """Chemical Class model.

    Attributes:
        id (int): Primary key.
        name (str): Unique name of the chemical class.
        compounds (list[Compound]): List of compounds associated with this class.
    """

    __tablename__ = Base.table_prefix + "chemical_class"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)

    compounds: Mapped[list["Compound"]] = relationship(back_populates="chemical_class")

    @property
    def compound_identifiers(self) -> list[str]:
        return [compound.identifier for compound in self.compounds]

    def __repr__(self) -> str:
        return f"<ChemicalClass(id={self.id}, name={self.name})>"


class ChemicalSubClass(Base, OnlyName):
    """Chemical Sub-Class model.

    Attributes:
        id (int): Primary key.
        name (str): Unique name of the chemical sub-class.
        compounds (list[Compound]): List of compounds associated with this sub-class.
    """

    __tablename__ = Base.table_prefix + "chemical_sub_class"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)

    compounds: Mapped[list["Compound"]] = relationship(
        back_populates="chemical_sub_class"
    )

    @property
    def compound_identifiers(self) -> list[str]:
        return [compound.identifier for compound in self.compounds]

    def __repr__(self) -> str:
        return f"<ChemicalSubClass(id={self.id}, name={self.name})>"


class DirectParentClassification(Base, OnlyName):
    """Direct Parent Classification model.

    Attributes:
        id (int): Primary key.
        name (str): Unique name of the direct parent classification.
        compounds (list[Compound]): List of compounds associated with this classification.
    """

    __tablename__ = Base.table_prefix + "direct_parent_classification"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)

    compounds: Mapped[list["Compound"]] = relationship(
        back_populates="direct_parent_classification"
    )

    @property
    def compound_identifiers(self) -> list[str]:
        return [compound.identifier for compound in self.compounds]

    def __repr__(self) -> str:
        return f"<DirectParentClassification(id={self.id}, name={self.name})>"


class ChemicalSuperClass(Base, OnlyName):
    """Chemical Super-Class model.

    Attributes:
        id (int): Primary key.
        name (str): Unique name of the chemical super-class.
        compounds (list[Compound]): List of compounds associated with this super-class.
    """

    __tablename__ = Base.table_prefix + "chemical_super_class"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)

    compounds: Mapped[list["Compound"]] = relationship(
        back_populates="chemical_super_class"
    )

    @property
    def compound_identifiers(self) -> list[str]:
        return [compound.identifier for compound in self.compounds]

    def __repr__(self) -> str:
        return f"<ChemicalSuperClass(id={self.id}, name={self.name})>"


class DOI(Base):
    """Class definition for table doi.

    Attributes:
        id (int): Primary key.
        identifier (str): Unique identifier for the DOI.
        compounds (list[Compound]): List of compounds associated with this DOI.
    """

    __tablename__ = Base.table_prefix + "doi"

    id: Mapped[int] = mapped_column(primary_key=True)
    identifier: Mapped[str] = mapped_column(
        String(255).with_variant(String(255, collation="utf8mb4_bin"), "mysql"),
        unique=True,
    )
    compounds: Mapped[list["Compound"]] = relationship(
        secondary=CompoundDOI.__table__, back_populates="dois"
    )

    def __repr__(self) -> str:
        return f"<DOI(id={self.id}, identifier={self.identifier})>"


class Synonym(Base):
    """Class definition for table synonym.

    Attributes:
        id (int): Primary key.
        name (str): Unique name of the synonym.
        compounds (list[Compound]): List of compounds associated with this synonym.
    """

    __tablename__ = Base.table_prefix + "synonym"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(1000).with_variant(String(1000, collation="utf8mb4_bin"), "mysql")
    )

    @property
    def compound_identifiers(self) -> list[str]:
        return [compound.identifier for compound in self.compounds]

    # m2m relationship
    compounds: Mapped[list["Compound"]] = relationship(
        secondary=CompoundSynonym.__table__, back_populates="synonyms"
    )
    __table_args__ = (Index("uq_my_model_name", "name", unique=True, mysql_length=768),)

    def __repr__(self) -> str:
        return f"<Synonym(id={self.id}, name={self.name})>"


class Organism(Base):
    """Class definition for table organism.

    Attributes:
        id (int): Primary key.
        name (str): Name of the organism.
        tax_id (Optional[int]): NCBI taxonomy identifier.
        ipni_id (Optional[str]): IPNI identifier.
        wcvp_id (Optional[int]): WCVP identifier.
        powo_id (Optional[str]): POWO identifier.
        compounds (list[Compound]): List of compounds associated with this organism.
    """

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

    @property
    def compound_identifiers(self) -> list[str]:
        return [compound.identifier for compound in self.compounds]

    __table_args__ = (
        Index(
            f"ux_{__tablename__}__name",
            name,
            mysql_length=255,
        ),
    )

    def __repr__(self) -> str:
        return f"<Organism(id={self.id}, name={self.name}, tax_id={self.tax_id})>"


class Collection(Base):
    """Class definition for table collection.

    Attributes:
        id (int): Primary key.
        name (str): Unique name of the collection.
        compounds (list[Compound]): List of compounds associated with this collection.
    """

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
    def compound_identifiers(self) -> list[str]:
        return [compound.identifier for compound in self.compounds]

    def __repr__(self) -> str:
        return f"<Collection(id={self.id}, name={self.name})>"


class CAS(Base):
    """Class definition for table cas.

    Attributes:
        id (int): Primary key.
        number (str): Unique CAS number.
        compounds (list[Compound]): List of compounds associated with this CAS number.
    """

    __tablename__ = Base.table_prefix + "cas"

    id = Column(Integer, primary_key=True)
    number = Column(
        String(255).with_variant(String(255, collation="utf8mb4_bin"), "mysql"),
        unique=True,
    )
    compounds: Mapped[list["Compound"]] = relationship(
        secondary=CompoundCAS.__table__, back_populates="cas_numbers"
    )

    def __repr__(self) -> str:
        return f"<CAS(id={self.id}, number={self.number})>"


class TaxonomyName(Base):
    """Class definition for table taxonomy_name. Name from
    NCBI taxonomy https://www.ncbi.nlm.nih.gov/taxonomys.

    Attributes:
        id (int): Primary key.
        tax_id (int): NCBI taxonomy Identifier.
        name (str): Name associated with the tax_id.
        name_type (str): Type of the name (e.g., scientific name, common name, synonym).
    """

    __tablename__ = Base.table_prefix + "taxonomy_name"
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

    def __repr__(self) -> str:
        return f"<TaxonomyName(id={self.id}, tax_id={self.tax_id}, name={self.name}, name_type={self.name_type})>"


class WCVPPlant(Base):
    """Class definition for table wcvp_plant. Plant names from
    World Checklist of Vascular Plants (WCVP).

    Attributes:
        plant_name_id (int): Primary key.
        taxon_name (Optional[str]): Taxon name of the plant.
        accepted_plant_name_id (Optional[int]): Accepted plant name identifier.
        powo_id (Optional[str]): POWO identifier.
        ipni_id (Optional[str]): IPNI identifier.
    """

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

    def __repr__(self) -> str:
        return f"<WCVPPlant(plant_name_id={self.plant_name_id}, taxon_name={self.taxon_name})>"
