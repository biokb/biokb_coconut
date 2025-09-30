from typing import Optional

from sqlalchemy import Column, ForeignKey, Index, Integer, String, Table, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from biokb_coconut import constants


class Base(DeclarativeBase):
    table_prefix = constants.PROJECT_NAME + "_"


# Association tables for many-to-many relationships
compound_organism = Table(
    Base.table_prefix + "compound_organism",
    Base.metadata,
    Column(
        "compound_id", ForeignKey(Base.table_prefix + "compound.id"), primary_key=True
    ),
    Column(
        "organism_id", ForeignKey(Base.table_prefix + "organism.id"), primary_key=True
    ),
)

compound_collection = Table(
    Base.table_prefix + "compound_collection",
    Base.metadata,
    Column(
        "compound_id", ForeignKey(Base.table_prefix + "compound.id"), primary_key=True
    ),
    Column(
        "collection_id",
        ForeignKey(Base.table_prefix + "collection.id"),
        primary_key=True,
    ),
)

compound_synonym = Table(
    Base.table_prefix + "compound_synonym",
    Base.metadata,
    Column(
        "compound_id", ForeignKey(Base.table_prefix + "compound.id"), primary_key=True
    ),
    Column(
        "synonym_id", ForeignKey(Base.table_prefix + "synonym.id"), primary_key=True
    ),
)

compound_cas = Table(
    Base.table_prefix + "compound_cas",
    Base.metadata,
    Column(
        "compound_id", ForeignKey(Base.table_prefix + "compound.id"), primary_key=True
    ),
    Column("cas_number_id", ForeignKey(Base.table_prefix + "cas.id"), primary_key=True),
)

compound_doi = Table(
    Base.table_prefix + "compound_doi",
    Base.metadata,
    Column(
        "compound_id", ForeignKey(Base.table_prefix + "compound.id"), primary_key=True
    ),
    Column("doi_id", ForeignKey(Base.table_prefix + "doi.id"), primary_key=True),
)


class Compound(Base):
    __tablename__ = Base.table_prefix + "compound"
    __table_args__ = {
        "mysql_charset": "utf8",
        "mysql_collate": "utf8_unicode_ci",
    }

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
    contains_sugar: Mapped[bool]
    contains_ring_sugars: Mapped[bool]
    contains_linear_sugars: Mapped[bool]
    murcko_framework: Mapped[Optional[str]] = mapped_column(Text)
    np_likeness: Mapped[float]
    chemical_class: Mapped[Optional[str]] = mapped_column(String(255))
    chemical_sub_class: Mapped[Optional[str]] = mapped_column(String(255))
    chemical_super_class: Mapped[Optional[str]] = mapped_column(String(255))
    direct_parent_classification: Mapped[Optional[str]] = mapped_column(String(255))
    np_classifier_pathway: Mapped[Optional[str]] = mapped_column(String(255))
    np_classifier_superclass: Mapped[Optional[str]] = mapped_column(String(255))
    np_classifier_class: Mapped[Optional[str]] = mapped_column(String(255))
    np_classifier_is_glycoside: Mapped[Optional[bool]]

    organisms: Mapped[list["Organism"]] = relationship(
        secondary=compound_organism, back_populates="compounds"
    )
    collections: Mapped[list["Collection"]] = relationship(
        secondary=compound_collection, back_populates="compounds"
    )
    dois: Mapped[list["DOI"]] = relationship(
        secondary=compound_doi, back_populates="compounds"
    )
    synonyms: Mapped[list["Synonym"]] = relationship(
        secondary=compound_synonym, back_populates="compounds"
    )
    cas_numbers: Mapped[list["CAS"]] = relationship(
        secondary=compound_cas, back_populates="compounds"
    )


class DOI(Base):
    __tablename__ = Base.table_prefix + "doi"
    __table_args__ = {
        "mysql_charset": "utf8",
        "mysql_collate": "utf8_unicode_ci",
    }

    id: Mapped[int] = mapped_column(primary_key=True)
    identifier: Mapped[str] = mapped_column(
        # The collation in this String column only works for MySQL, not SQLite or other dialects. I will replace it with a dialect-specific variant for now everywhere
        # String(255, collation="utf8mb4_bin"),
        String(255).with_variant(String(255, collation="utf8mb4_bin"), "mysql"),
        unique=True,
    )
    compounds: Mapped[list["Compound"]] = relationship(
        secondary=compound_doi, back_populates="dois"
    )


class Synonym(Base):
    __tablename__ = Base.table_prefix + "synonym"
    __table_args__ = {
        "mysql_charset": "utf8",
        "mysql_collate": "utf8_unicode_ci",
    }

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        # String(768, collation="utf8mb4_bin"),
        String(768).with_variant(String(768, collation="utf8mb4_bin"), "mysql")
    )
    compounds: Mapped[list["Compound"]] = relationship(
        secondary=compound_synonym, back_populates="synonyms"
    )
    __table_args__ = (Index("uq_my_model_name", "name", unique=True, mysql_length=768),)


class Organism(Base):
    __tablename__ = Base.table_prefix + "organism"
    __table_args__ = {
        "mysql_charset": "utf8",
        "mysql_collate": "utf8_unicode_ci",
    }

    id: Mapped[int] = mapped_column(primary_key=True)
    # name: Mapped[str] = mapped_column(String(255, collation="utf8mb4_bin"), unique=True)
    name: Mapped[str] = mapped_column(String(255).with_variant(String(255, collation="utf8mb4_bin"), "mysql"), unique=True)
    compounds: Mapped[list["Compound"]] = relationship(
        secondary=compound_organism, back_populates="organisms"
    )


class Collection(Base):
    __tablename__ = Base.table_prefix + "collection"
    __table_args__ = {
        "mysql_charset": "utf8",
        "mysql_collate": "utf8_unicode_ci",
    }

    id: Mapped[int] = mapped_column(primary_key=True)
    #name: Mapped[str] = mapped_column(String(255, collation="utf8mb4_bin"), unique=True)
    name: Mapped[str] = mapped_column(String(255).with_variant(String(255, collation="utf8mb4_bin"), "mysql"), unique=True)
    compounds: Mapped[list["Compound"]] = relationship(
        secondary=compound_collection, back_populates="collections"
    )

    @property
    def compound_identifiers(self):
        return [compound.identifier for compound in self.compounds]


class CAS(Base):
    __tablename__ = Base.table_prefix + "cas"
    __table_args__ = {
        "mysql_charset": "utf8",
        "mysql_collate": "utf8_unicode_ci",
    }
    id = Column(Integer, primary_key=True)
    number = Column(
        # String(255, collation="utf8mb4_bin"),
        String(255).with_variant(String(255, collation="utf8mb4_bin"), "mysql"),
        unique=True,
    )
    compounds: Mapped[list["Compound"]] = relationship(
        secondary=compound_cas, back_populates="cas_numbers"
    )
