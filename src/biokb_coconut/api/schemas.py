from typing import Annotated, List, Optional

from click import File
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import desc


class OffsetLimit(BaseModel):
    limit: Annotated[int, Field(le=100)] = 10
    offset: int = 0


class Name(BaseModel):
    id: int = Field(..., description="Primary key, unique identifier")
    name: str = Field(..., description="Name")

    model_config = ConfigDict(from_attributes=True)


class CompoundBase(BaseModel):
    id: int = Field(..., description="Primary key, unique identifier for the compound")
    identifier: str = Field(..., description="Unique compound identifier")
    canonical_smiles: Optional[str] = Field(
        None, description="Canonical SMILES notation"
    )
    standard_inchi: Optional[str] = Field(None, description="Standard InChI string")
    standard_inchi_key: Optional[str] = Field(None, description="Standard InChIKey")
    name: Optional[str] = Field(None, description="Name of the compound")
    iupac_name: Optional[str] = Field(None, description="IUPAC name")
    annotation_level: int = Field(..., description="Annotation level")
    total_atom_count: int = Field(..., description="Total atom count")
    heavy_atom_count: int = Field(..., description="Heavy atom count")
    molecular_weight: float = Field(..., description="Molecular weight")
    exact_molecular_weight: float = Field(..., description="Exact molecular weight")
    molecular_formula: str = Field(..., description="Molecular formula")
    alogp: float = Field(..., description="ALogP value")
    topological_polar_surface_area: float = Field(
        ..., description="Topological polar surface area"
    )
    rotatable_bond_count: int = Field(..., description="Rotatable bond count")
    hydrogen_bond_acceptors: int = Field(..., description="Hydrogen bond acceptors")
    hydrogen_bond_donors: int = Field(..., description="Hydrogen bond donors")
    hydrogen_bond_acceptors_lipinski: int = Field(
        ..., description="Lipinski hydrogen bond acceptors"
    )
    hydrogen_bond_donors_lipinski: int = Field(
        ..., description="Lipinski hydrogen bond donors"
    )
    lipinski_rule_of_five_violations: int = Field(
        ..., description="Lipinski rule of five violations"
    )
    aromatic_rings_count: int = Field(..., description="Aromatic rings count")
    qed_drug_likeliness: float = Field(..., description="QED drug-likeliness score")
    formal_charge: int = Field(..., description="Formal charge")
    fractioncsp3: float = Field(..., description="Fraction of sp3 carbons")
    number_of_minimal_rings: int = Field(..., description="Number of minimal rings")
    van_der_walls_volume: Optional[float] = Field(
        None, description="Van der Waals volume"
    )
    contains_sugar: Optional[bool] = Field(
        ..., description="Whether the compound contains sugar"
    )
    contains_ring_sugars: bool = Field(
        ..., description="Whether the compound contains ring sugars"
    )
    contains_linear_sugars: bool = Field(
        ..., description="Whether the compound contains linear sugars"
    )
    murcko_framework: Optional[str] = Field(None, description="Murcko framework")
    np_likeness: float = Field(..., description="Natural product likeness score")
    np_classifier_is_glycoside: Optional[bool] = Field(
        None, description="NPClassifier is glycoside"
    )
    # foreign keys to classification tables
    chemical_class_id: Optional[int] = Field(None, description="Chemical class ID")
    chemical_sub_class_id: Optional[int] = Field(
        None, description="Chemical subclass ID"
    )
    direct_parent_classification_id: Optional[int] = Field(
        None, description="Direct parent classification ID"
    )
    chemical_super_class_id: Optional[int] = Field(
        None, description="Chemical superclass ID"
    )
    np_classifier_pathway_id: Optional[int] = Field(
        None, description="NP classifier pathway ID"
    )
    np_classifier_superclass_id: Optional[int] = Field(
        None, description="NP classifier superclass ID"
    )
    np_classifier_class_id: Optional[int] = Field(
        None, description="NP classifier class ID"
    )

    model_config = ConfigDict(from_attributes=True)


class Compound(CompoundBase):
    chemical_class: Optional["ChemicalClass"] = Field(
        None, description="Chemical class object"
    )
    chemical_sub_class: Optional["ChemicalSubClass"] = Field(
        default=None, description="Chemical subclass object"
    )
    direct_parent_classification: Optional["DirectParentClassification"] = Field(
        default=None, description="Direct parent classification object"
    )
    chemical_super_class: Optional["ChemicalSuperClass"] = Field(
        default=None, description="Chemical superclass object"
    )
    np_classifier_pathway: Optional["NpClassifierPathway"] = Field(
        default=None, description="NP classifier pathway object"
    )
    np_classifier_superclass: Optional["NpClassifierSuperclass"] = Field(
        default=None, description="NP classifier superclass object"
    )
    np_classifier_class: Optional["NpClassifierClass"] = Field(
        default=None, description="NP classifier class object"
    )

    model_config = ConfigDict(from_attributes=True)


class CompoundDetail(Compound):
    organisms: List["Organism"] = Field(
        [], description="List of organisms associated with this compound"
    )
    dois: List["DOIBase"] = Field(
        [], description="List of DOIs associated with this compound"
    )
    synonyms: List["SynonymBase"] = Field(
        [], description="List of synonyms associated with this compound"
    )
    cas_numbers: List["CASBase"] = Field(
        [], description="List of CAS numbers associated with this compound"
    )

    model_config = ConfigDict(from_attributes=True)


class CompoundSearch(OffsetLimit):
    identifier: Optional[str] = Field(None, description="Unique compound identifier")
    canonical_smiles: Optional[str] = Field(
        None, description="Canonical SMILES notation"
    )
    standard_inchi: Optional[str] = Field(None, description="Standard InChI string")
    standard_inchi_key: Optional[str] = Field(None, description="Standard InChIKey")
    name: Optional[str] = Field(None, description="Name of the compound")
    iupac_name: Optional[str] = Field(None, description="IUPAC name")
    annotation_level: Optional[int] = Field(None, description="Annotation level")
    total_atom_count: Optional[int] = Field(None, description="Total atom count")
    heavy_atom_count: Optional[int] = Field(None, description="Heavy atom count")
    molecular_weight: Optional[float] = Field(None, description="Molecular weight")
    exact_molecular_weight: Optional[float] = Field(
        None, description="Exact molecular weight"
    )
    molecular_formula: Optional[str] = Field(None, description="Molecular formula")
    alogp: Optional[float] = Field(None, description="ALogP value")
    topological_polar_surface_area: Optional[float] = Field(
        None, description="Topological polar surface area"
    )
    rotatable_bond_count: Optional[int] = Field(
        None, description="Rotatable bond count"
    )
    hydrogen_bond_acceptors: Optional[int] = Field(
        None, description="Hydrogen bond acceptors"
    )
    hydrogen_bond_donors: Optional[int] = Field(
        None, description="Hydrogen bond donors"
    )
    hydrogen_bond_acceptors_lipinski: Optional[int] = Field(
        None, description="Lipinski hydrogen bond acceptors"
    )
    hydrogen_bond_donors_lipinski: Optional[int] = Field(
        None, description="Lipinski hydrogen bond donors"
    )
    lipinski_rule_of_five_violations: Optional[int] = Field(
        None, description="Lipinski rule of five violations"
    )
    aromatic_rings_count: Optional[int] = Field(
        None, description="Aromatic rings count"
    )
    qed_drug_likeliness: Optional[float] = Field(
        None, description="QED drug-likeliness score"
    )
    formal_charge: Optional[int] = Field(None, description="Formal charge")
    fractioncsp3: Optional[float] = Field(None, description="Fraction of sp3 carbons")
    number_of_minimal_rings: Optional[int] = Field(
        None, description="Number of minimal rings"
    )
    van_der_walls_volume: Optional[float] = Field(
        None, description="Van der Waals volume"
    )
    contains_sugar: Optional[bool] = Field(
        None, description="Whether the compound contains sugar"
    )
    contains_ring_sugars: Optional[bool] = Field(
        None, description="Whether the compound contains ring sugars"
    )
    contains_linear_sugars: Optional[bool] = Field(
        None, description="Whether the compound contains linear sugars"
    )
    murcko_framework: Optional[str] = Field(None, description="Murcko framework")
    np_likeness: Optional[float] = Field(
        None, description="Natural product likeness score"
    )
    chemical_sub_class: Optional[str] = Field(None, description="Chemical subclass")
    chemical_super_class: Optional[str] = Field(None, description="Chemical superclass")
    direct_parent_classification: Optional[str] = Field(
        None, description="Direct parent classification"
    )
    np_classifier_is_glycoside: Optional[bool] = Field(
        None, description="NPClassifier is glycoside"
    )
    chemical_class_id: Optional[int] = None
    chemical_sub_class_id: Optional[int] = None
    direct_parent_classification_id: Optional[int] = None
    chemical_super_class_id: Optional[int] = None
    np_classifier_pathway_id: Optional[int] = None
    np_classifier_superclass_id: Optional[int] = None
    np_classifier_class_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class CompoundSearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    count: int
    offset: int
    limit: int
    results: List[CompoundBase]


class DOIBase(BaseModel):
    id: int = Field(..., description="Primary key, unique identifier for the DOI")
    identifier: str = Field(..., description="Unique DOI identifier")

    model_config = ConfigDict(from_attributes=True)


class DOI_with_compounds(DOIBase):
    compounds: List[CompoundBase] = Field(
        [], description="List of compounds associated with this DOI"
    )


class DOISearch(OffsetLimit):
    identifier: Optional[str] = Field(None, description="Unique DOI identifier")


class DOISearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    count: int
    offset: int
    limit: int
    results: List[DOI_with_compounds]


class OrganismBase(BaseModel):
    id: int = Field(..., description="Primary key, unique identifier for the organism")
    name: str = Field(..., description="Name of the organism")
    tax_id: Optional[int]
    ipni_id: Optional[str]
    wcvp_id: Optional[int]
    powo_id: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class Organism_with_compounds(OrganismBase):
    compound_identifiers: List[str] = Field(
        [], description="List of compound identifiers associated with this organism"
    )


class OrganismSearch(OffsetLimit):
    id: Optional[int] = Field(
        None, description="Primary key, unique identifier for the organism"
    )
    tax_id: Optional[int] = Field(None, description="NCBI Taxonomy ID of the organism")
    ipni_id: Optional[str] = Field(None, description="IPNI ID of the organism")
    wcvp_id: Optional[int] = Field(None, description="WCVP ID of the organism")
    powo_id: Optional[str] = Field(None, description="POWO ID of the organism")
    name: Optional[str] = Field(None, description="Name of the organism")


class OrganismSearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    count: int
    offset: int
    limit: int
    results: List[Organism_with_compounds]


class SynonymBase(BaseModel):
    id: int = Field(..., description="Primary key, unique identifier for the synonym")
    name: str = Field(..., description="Name of the synonym")

    model_config = ConfigDict(from_attributes=True)


class SynonymSearch(OffsetLimit):
    id: Optional[int] = Field(
        None, description="Primary key, unique identifier for the synonym"
    )
    name: Optional[str] = Field(None, description="Name of the synonym")


class Synonym_with_compounds(SynonymBase):
    compound_identifiers: List[str] = Field(
        [], description="List of compound identifiers associated with this synonym"
    )

    model_config = ConfigDict(from_attributes=True)


class SynonymSearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    count: int
    offset: int
    limit: int
    results: List[Synonym_with_compounds]


class CASBase(BaseModel):
    id: int = Field(..., description="Primary key, unique identifier for the CAS")
    number: str = Field(..., description="Unique CAS identifier")

    model_config = ConfigDict(from_attributes=True)


class CAS_with_compounds(CASBase):
    compounds: List[CompoundBase] = Field(
        [], description="List of compounds associated with this CAS"
    )


class CASSearch(OffsetLimit):
    number: Optional[str] = Field(None, description="Unique CAS number")


class CASSearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    count: int
    offset: int
    limit: int
    results: List[CAS_with_compounds]


class CollectionBase(BaseModel):
    id: int = Field(
        ..., description="Primary key, unique identifier for the collection"
    )
    name: str = Field(..., description="Name of the collection")

    model_config = ConfigDict(from_attributes=True)


class Collection(CollectionBase):
    compound_identifiers: List[str] = Field(
        [], description="List of compound identifiers associated with this collection"
    )

    model_config = ConfigDict(from_attributes=True)


class Collection_with_compound_identifiers(CollectionBase):
    compound_identifiers: List[str] = Field(
        [], description="List of compound identifiers associated with this collection"
    )


class CollectionSearch(OffsetLimit):
    id: Optional[int] = Field(
        None, description="Primary key, unique identifier for the collection"
    )
    name: Optional[str] = Field(None, description="Name of the collection")


class CollectionSearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    count: int
    offset: int
    limit: int
    results: List[Collection_with_compound_identifiers]


class ChemicalClassBase(BaseModel):
    id: int = Field(
        ..., description="Primary key, unique identifier for the chemical class"
    )
    name: str = Field(..., description="Name of the chemical class")

    model_config = ConfigDict(from_attributes=True)


class ChemicalClass(ChemicalClassBase):
    compounds: List[CompoundBase] = Field(
        [], description="List of compounds associated with this chemical class"
    )

    model_config = ConfigDict(from_attributes=True)


class ChemicalClassWithCompoundIDs(ChemicalClassBase):
    compound_identifiers: List[str] = Field(
        [],
        description="List of compound identifiers associated with this chemical class",
    )

    model_config = ConfigDict(from_attributes=True)


class ChemicalClassSearch(OffsetLimit):
    id: Optional[int] = Field(
        None, description="Primary key, unique identifier for the chemical class"
    )
    name: Optional[str] = Field(None, description="Name of the chemical class")


class ChemicalClassSearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    count: int
    offset: int
    limit: int
    results: List[ChemicalClassWithCompoundIDs]


class ChemicalSubClassBase(BaseModel):
    id: int = Field(
        ..., description="Primary key, unique identifier for the chemical subclass"
    )
    name: str = Field(..., description="Name of the chemical subclass")

    model_config = ConfigDict(from_attributes=True)


class ChemicalSubClass(ChemicalSubClassBase):
    compounds: List[CompoundBase] = Field(
        [], description="List of compounds associated with this chemical subclass"
    )

    model_config = ConfigDict(from_attributes=True)


class ChemicalSubClassSearch(BaseModel):
    id: Optional[int] = Field(
        None, description="Primary key, unique identifier for the chemical subclass"
    )
    name: Optional[str] = Field(None, description="Name of the chemical subclass")


class ChemicalSubClassSearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    count: int
    offset: int
    limit: int
    results: List[ChemicalSubClass]


class DirectParentClassificationBase(BaseModel):
    id: int = Field(
        ...,
        description="Primary key, unique identifier for the direct parent classification",
    )
    name: str = Field(..., description="Name of the direct parent classification")

    model_config = ConfigDict(from_attributes=True)


class DirectParentClassification(DirectParentClassificationBase):
    compounds: List[CompoundBase] = Field(
        [],
        description="List of compounds associated with this direct parent classification",
    )

    model_config = ConfigDict(from_attributes=True)


class DirectParentClassificationWithCompoundIDs(DirectParentClassificationBase):
    compound_identifiers: List[str] = Field(
        [],
        description="List of compound identifiers associated with this direct parent classification",
    )

    model_config = ConfigDict(from_attributes=True)


class DirectParentClassificationSearch(OffsetLimit):
    id: Optional[int] = Field(
        None,
        description="Primary key, unique identifier for the direct parent classification",
    )
    name: Optional[str] = Field(
        None, description="Name of the direct parent classification"
    )


class DirectParentClassificationSearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    count: int
    offset: int
    limit: int
    results: List[DirectParentClassificationWithCompoundIDs]


class ChemicalSuperClassBase(BaseModel):
    id: int = Field(
        ..., description="Primary key, unique identifier for the chemical superclass"
    )
    name: str = Field(..., description="Name of the chemical superclass")

    model_config = ConfigDict(from_attributes=True)


class ChemicalSuperClass(ChemicalSuperClassBase):
    compounds: List[CompoundBase] = Field(
        [], description="List of compounds associated with this chemical superclass"
    )

    model_config = ConfigDict(from_attributes=True)


class ChemicalSuperClassWithCompoundIDs(ChemicalSuperClassBase):
    compound_identifiers: List[str] = Field(
        [],
        description="List of compound identifiers associated with this chemical superclass",
    )

    model_config = ConfigDict(from_attributes=True)


class ChemicalSuperClassSearch(OffsetLimit):
    id: Optional[int] = Field(
        None, description="Primary key, unique identifier for the chemical superclass"
    )
    name: Optional[str] = Field(None, description="Name of the chemical superclass")


class ChemicalSuperClassSearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    count: int
    offset: int
    limit: int
    results: List[ChemicalSuperClassWithCompoundIDs]


class NpClassifierPathwayBase(BaseModel):
    id: int = Field(
        ..., description="Primary key, unique identifier for the NP classifier pathway"
    )
    name: str = Field(..., description="Name of the NP classifier pathway")

    model_config = ConfigDict(from_attributes=True)


class NpClassifierPathway(NpClassifierPathwayBase):
    compounds: List[CompoundBase] = Field(
        [], description="List of compounds associated with this NP classifier pathway"
    )

    model_config = ConfigDict(from_attributes=True)


class NpClassifierPathwayWithCompoundIDs(NpClassifierPathwayBase):
    compound_identifiers: List[str] = Field(
        [],
        description="List of compound identifiers associated with this NP classifier pathway",
    )

    model_config = ConfigDict(from_attributes=True)


class NpClassifierPathwaySearch(OffsetLimit):
    id: Optional[int] = Field(
        None, description="Primary key, unique identifier for the NP classifier pathway"
    )
    name: Optional[str] = Field(None, description="Name of the NP classifier pathway")


class NpClassifierPathwaySearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    count: int
    offset: int
    limit: int
    results: List[NpClassifierPathwayWithCompoundIDs]


class NpClassifierSuperclassBase(BaseModel):
    id: int = Field(
        ...,
        description="Primary key, unique identifier for the NP classifier superclass",
    )
    name: str = Field(..., description="Name of the NP classifier superclass")

    model_config = ConfigDict(from_attributes=True)


class NpClassifierSuperclass(NpClassifierSuperclassBase):
    compounds: List[CompoundBase] = Field(
        [],
        description="List of compounds associated with this NP classifier superclass",
    )

    model_config = ConfigDict(from_attributes=True)


class NpClassifierSuperclassWithCompoundIDs(NpClassifierSuperclassBase):
    compound_identifiers: List[str] = Field(
        [],
        description="List of compound identifiers associated with this NP classifier superclass",
    )

    model_config = ConfigDict(from_attributes=True)


class NpClassifierSuperclassSearch(OffsetLimit):
    id: Optional[int] = Field(
        None,
        description="Primary key, unique identifier for the NP classifier superclass",
    )
    name: Optional[str] = Field(
        None, description="Name of the NP classifier superclass"
    )


class NpClassifierSuperclassSearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    count: int
    offset: int
    limit: int
    results: List[NpClassifierSuperclassWithCompoundIDs]


class NpClassifierClassBase(BaseModel):
    id: int = Field(
        ..., description="Primary key, unique identifier for the NP classifier class"
    )
    name: str = Field(..., description="Name of the NP classifier class")

    model_config = ConfigDict(from_attributes=True)


class NpClassifierClass(NpClassifierClassBase):
    compounds: List[CompoundBase] = Field(
        [], description="List of compounds associated with this NP classifier class"
    )

    model_config = ConfigDict(from_attributes=True)


class NpClassifierClassWithCompoundIDs(NpClassifierClassBase):
    compound_identifiers: List[str] = Field(
        [],
        description="List of compound identifiers associated with this NP classifier class",
    )

    model_config = ConfigDict(from_attributes=True)


class NpClassifierClassSearch(OffsetLimit):
    id: Optional[int] = Field(
        None, description="Primary key, unique identifier for the NP classifier class"
    )
    name: Optional[str] = Field(None, description="Name of the NP classifier class")


class NpClassifierClassSearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    count: int
    offset: int
    limit: int
    results: List[NpClassifierClassWithCompoundIDs]


class Organism(OrganismBase):
    compounds: List[CompoundBase] = Field(
        [], description="List of compounds associated with this organism"
    )

    model_config = ConfigDict(from_attributes=True)
