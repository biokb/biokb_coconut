from typing import Annotated, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class OffsetLimit(BaseModel):
    limit: Annotated[int, Field(le=100)] = 10
    offset: int = 0


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
    contains_sugar: bool = Field(..., description="Whether the compound contains sugar")
    contains_ring_sugars: bool = Field(
        ..., description="Whether the compound contains ring sugars"
    )
    contains_linear_sugars: bool = Field(
        ..., description="Whether the compound contains linear sugars"
    )
    murcko_framework: Optional[str] = Field(None, description="Murcko framework")
    np_likeness: float = Field(..., description="Natural product likeness score")
    chemical_class: Optional[str] = Field(None, description="Chemical class")
    chemical_sub_class: Optional[str] = Field(None, description="Chemical subclass")
    chemical_super_class: Optional[str] = Field(None, description="Chemical superclass")
    direct_parent_classification: Optional[str] = Field(
        None, description="Direct parent classification"
    )
    np_classifier_pathway: Optional[str] = Field(
        None, description="NPClassifier pathway"
    )
    np_classifier_superclass: Optional[str] = Field(
        None, description="NPClassifier superclass"
    )
    np_classifier_class: Optional[str] = Field(None, description="NPClassifier class")
    np_classifier_is_glycoside: Optional[bool] = Field(
        None, description="NPClassifier is glycoside"
    )


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
    chemical_class: Optional[str] = Field(None, description="Chemical class")
    chemical_sub_class: Optional[str] = Field(None, description="Chemical subclass")
    chemical_super_class: Optional[str] = Field(None, description="Chemical superclass")
    direct_parent_classification: Optional[str] = Field(
        None, description="Direct parent classification"
    )
    np_classifier_pathway: Optional[str] = Field(
        None, description="NPClassifier pathway"
    )
    np_classifier_superclass: Optional[str] = Field(
        None, description="NPClassifier superclass"
    )
    np_classifier_class: Optional[str] = Field(None, description="NPClassifier class")
    np_classifier_is_glycoside: Optional[bool] = Field(
        None, description="NPClassifier is glycoside"
    )


class CompoundSearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    count: int
    offset: int
    limit: int
    results: List[CompoundBase]


class DOIBase(BaseModel):
    id: int = Field(..., description="Primary key, unique identifier for the DOI")
    identifier: str = Field(..., description="Unique DOI identifier")


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


class Organism_with_compounds(OrganismBase):
    compounds: List[CompoundBase] = Field(
        [], description="List of compounds associated with this organism"
    )


class OrganismSearch(OffsetLimit):
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


class SynonymSearch(OffsetLimit):
    name: Optional[str] = Field(None, description="Name of the synonym")


class Synonym_with_compounds(SynonymBase):
    compounds: List[CompoundBase] = Field(
        [], description="List of compounds associated with this synonym"
    )


class SynonymSearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    count: int
    offset: int
    limit: int
    results: List[Synonym_with_compounds]


class CASBase(BaseModel):
    id: int = Field(..., description="Primary key, unique identifier for the CAS")
    number: str = Field(..., description="Unique CAS identifier")


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


class Collection_with_compound_identifiers(CollectionBase):
    compound_identifiers: List[str] = Field(
        [], description="List of compound identifiers associated with this collection"
    )


class CollectionSearch(OffsetLimit):
    name: Optional[str] = Field(None, description="Name of the collection")


class CollectionSearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    count: int
    offset: int
    limit: int
    results: List[Collection_with_compound_identifiers]
