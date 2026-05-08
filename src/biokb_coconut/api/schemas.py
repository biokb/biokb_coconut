import re
from enum import Enum
from logging import getLogger
from typing import Annotated, List, Optional

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

logger = getLogger(__name__)
# Pre-compile the regex for performance
RANGE_PATTERN = re.compile(
    r"^(?P<low>[+-]?\d*(?P<low_decimal>\.?\d+)?)(\s*-\s*(?P<high>[+-]?\d*(?P<high_decimal>\.?\d+)?))?$"
)


def get_and_validate_range_logic(
    v: Optional[str | int | float],
) -> Optional[int | float | str]:
    """Validate that the input string is in the format "min-max" and that min < max."""
    # logger.info(f"Validating range logic for value: {v}, type: {type(v)}")
    if v is None or isinstance(
        v,
        (
            int,
            float,
        ),
    ):
        return v
    match = RANGE_PATTERN.match(v.strip())
    if not match:
        raise ValueError(
            "Format must be numeric range 'min-max' or a single numeric value"
        )
    found = match.groupdict()
    low = high = None
    low = float(found["low"]) if found["low_decimal"] else int(found["low"])

    if found["high"]:
        high = float(found["high"]) if found["high_decimal"] else int(found["high"])
        if low >= high:
            raise ValueError(
                f"Invalid range: low value {low} must be less than high value {high}"
            )
        return f"{low}-{high}"
    else:
        return low  # If there's no high value, just return the low value as a single number


# Create a custom type alias
NumericOrRange = Annotated[
    str | int | float,
    AfterValidator(get_and_validate_range_logic),
]


class NumericOperator(str, Enum):
    """Comparison operators for numeric fields."""

    EQ = "="  # Equal
    GT = ">"  # Greater than
    GTE = ">="  # Greater than or equal
    LT = "<"  # Less than
    LTE = "<="  # Less than or equal
    BTW = "between"  # Between (for range queries)


class OffsetLimit(BaseModel):
    limit: Annotated[int, Field(le=100)] = 10
    offset: int = 0


class Name(BaseModel):
    id: int = Field(..., description="Primary key, unique identifier")
    name: str = Field(..., description="Name")

    model_config = ConfigDict(from_attributes=True)


class CompoundBase2(BaseModel):
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
    number_of_organisms: Optional[int] = Field(
        None, description="Number of organisms associated with the compound"
    )


class CompoundBase(CompoundBase2):
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


class Compound(CompoundBase2):
    chemical_class: Optional["ChemicalClassBase"] = Field(
        None, description="Chemical class object"
    )
    chemical_sub_class: Optional["ChemicalSubClassBase"] = Field(
        default=None, description="Chemical subclass object"
    )
    direct_parent_classification: Optional["DirectParentClassificationBase"] = Field(
        default=None, description="Direct parent classification object"
    )
    chemical_super_class: Optional["ChemicalSuperClassBase"] = Field(
        default=None, description="Chemical superclass object"
    )
    np_classifier_pathway: Optional["NpClassifierPathwayBase"] = Field(
        default=None, description="NP classifier pathway object"
    )
    np_classifier_superclass: Optional["NpClassifierSuperclassBase"] = Field(
        default=None, description="NP classifier superclass object"
    )
    np_classifier_class: Optional["NpClassifierClassBase"] = Field(
        default=None, description="NP classifier class object"
    )

    model_config = ConfigDict(from_attributes=True)


class CompoundDetail(Compound):
    organisms: List["OrganismBase"] = Field(
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


class CompoundSearchBase(BaseModel):
    identifier: Optional[str] = Field(None, description="Unique compound identifier")
    canonical_smiles: Optional[str] = Field(
        None, description="Canonical SMILES notation"
    )
    standard_inchi: Optional[str] = Field(None, description="Standard InChI string")
    standard_inchi_key: Optional[str] = Field(None, description="Standard InChIKey")
    name: Optional[str] = Field(None, description="Name of the compound")
    iupac_name: Optional[str] = Field(None, description="IUPAC name")
    # annotation_level: Optional[int | str] = Field(None, description="Annotation level")
    annotation_level: Optional[NumericOrRange] = Field(
        None, description="Annotation level"
    )
    annotation_level_op: NumericOperator = Field(
        NumericOperator.EQ, description="Operator for annotation_level comparison"
    )
    total_atom_count: Optional[NumericOrRange] = Field(
        None, description="Total atom count"
    )
    total_atom_count_op: Optional[NumericOperator] = Field(
        NumericOperator.EQ, description="Operator for total_atom_count comparison"
    )
    heavy_atom_count: Optional[NumericOrRange] = Field(
        None, description="Heavy atom count"
    )
    heavy_atom_count_op: Optional[NumericOperator] = Field(
        NumericOperator.EQ, description="Operator for heavy_atom_count comparison"
    )
    molecular_weight: Optional[NumericOrRange] = Field(
        None, description="Molecular weight"
    )
    molecular_weight_op: Optional[NumericOperator] = Field(
        NumericOperator.EQ, description="Operator for molecular_weight comparison"
    )
    exact_molecular_weight: Optional[NumericOrRange] = Field(
        None, description="Exact molecular weight"
    )
    exact_molecular_weight_op: Optional[NumericOperator] = Field(
        NumericOperator.EQ, description="Operator for exact_molecular_weight comparison"
    )
    molecular_formula: Optional[str] = Field(None, description="Molecular formula")
    alogp: Optional[NumericOrRange] = Field(None, description="ALogP value")
    alogp_op: Optional[NumericOperator] = Field(
        NumericOperator.EQ, description="Operator for alogp comparison"
    )
    topological_polar_surface_area: Optional[NumericOrRange] = Field(
        None, description="Topological polar surface area"
    )
    topological_polar_surface_area_op: Optional[NumericOperator] = Field(
        NumericOperator.EQ,
        description="Operator for topological_polar_surface_area comparison",
    )
    rotatable_bond_count: Optional[NumericOrRange] = Field(
        None, description="Rotatable bond count"
    )
    rotatable_bond_count_op: Optional[NumericOperator] = Field(
        NumericOperator.EQ, description="Operator for rotatable_bond_count comparison"
    )
    hydrogen_bond_acceptors: Optional[NumericOrRange] = Field(
        None, description="Hydrogen bond acceptors"
    )
    hydrogen_bond_acceptors_op: Optional[NumericOperator] = Field(
        NumericOperator.EQ,
        description="Operator for hydrogen_bond_acceptors comparison",
    )
    hydrogen_bond_donors: Optional[NumericOrRange] = Field(
        None, description="Hydrogen bond donors"
    )
    hydrogen_bond_donors_op: Optional[NumericOperator] = Field(
        NumericOperator.EQ, description="Operator for hydrogen_bond_donors comparison"
    )
    hydrogen_bond_acceptors_lipinski: Optional[NumericOrRange] = Field(
        None, description="Lipinski hydrogen bond acceptors"
    )
    hydrogen_bond_acceptors_lipinski_op: Optional[NumericOperator] = Field(
        NumericOperator.EQ,
        description="Operator for hydrogen_bond_acceptors_lipinski comparison",
    )
    hydrogen_bond_donors_lipinski: Optional[NumericOrRange] = Field(
        None, description="Lipinski hydrogen bond donors"
    )
    hydrogen_bond_donors_lipinski_op: Optional[NumericOperator] = Field(
        NumericOperator.EQ,
        description="Operator for hydrogen_bond_donors_lipinski comparison",
    )
    lipinski_rule_of_five_violations: Optional[NumericOrRange] = Field(
        None, description="Lipinski rule of five violations"
    )
    lipinski_rule_of_five_violations_op: Optional[NumericOperator] = Field(
        NumericOperator.EQ,
        description="Operator for lipinski_rule_of_five_violations comparison",
    )
    aromatic_rings_count: Optional[NumericOrRange] = Field(
        None, description="Aromatic rings count"
    )
    aromatic_rings_count_op: Optional[NumericOperator] = Field(
        NumericOperator.EQ, description="Operator for aromatic_rings_count comparison"
    )
    qed_drug_likeliness: Optional[NumericOrRange] = Field(
        None, description="QED drug-likeliness score"
    )
    qed_drug_likeliness_op: Optional[NumericOperator] = Field(
        NumericOperator.EQ, description="Operator for qed_drug_likeliness comparison"
    )
    formal_charge: Optional[NumericOrRange] = Field(None, description="Formal charge")
    formal_charge_op: Optional[NumericOperator] = Field(
        NumericOperator.EQ, description="Operator for formal_charge comparison"
    )
    fractioncsp3: Optional[NumericOrRange] = Field(
        None, description="Fraction of sp3 carbons"
    )
    fractioncsp3_op: Optional[NumericOperator] = Field(
        NumericOperator.EQ, description="Operator for fractioncsp3 comparison"
    )
    number_of_minimal_rings: Optional[NumericOrRange] = Field(
        None, description="Number of minimal rings"
    )
    number_of_minimal_rings_op: Optional[NumericOperator] = Field(
        NumericOperator.EQ,
        description="Operator for number_of_minimal_rings comparison",
    )
    van_der_walls_volume: Optional[NumericOrRange] = Field(
        None, description="Van der Waals volume"
    )
    van_der_walls_volume_op: Optional[NumericOperator] = Field(
        NumericOperator.EQ, description="Operator for van_der_walls_volume comparison"
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
    np_likeness: Optional[NumericOrRange] = Field(
        None, description="Natural product likeness score"
    )
    np_likeness_op: Optional[NumericOperator] = Field(
        NumericOperator.EQ, description="Operator for np_likeness comparison"
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
    number_of_organisms: Optional[NumericOrRange] = Field(
        None, description="Number of organisms associated with the compound"
    )
    number_of_organisms_op: Optional[NumericOperator] = Field(
        NumericOperator.EQ, description="Operator for number_of_organisms comparison"
    )

    model_config = ConfigDict(from_attributes=True)


class CompoundOrganismSearch(CompoundSearchBase, OffsetLimit):
    organism_name: Optional[str] = Field(None, description="Organism name")
    synonym: Optional[str] = Field(None, description="Synonym of compound")
    order_by: Optional[str] = Field(
        None,
        description="Field name to order the results by",
    )
    order_desc: Optional[bool] = Field(
        False,
        description="Whether to order the results in descending order",
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "identifier": "CNP0255066.1",
                    "canonical_smiles": "C[C@@H]1CC[C@@]23COC(=O)C2=C[C@@H](O[C@@H]2O[C@H](CO)[C@@H](O)[C@H](O)[C@H]2O)CC3[C@@]1(C)CCC1=COC=C1",
                    "standard_inchi": "InChI=1S/C26H36O9/c1-14-3-7-26-13-33-23(31)17(26)9-16(34-24-22(30)21(29)20(28)18(11-27)35-24)10-19(26)25(14,2)6-4-15-5-8-32-12-15/h5,8-9,12,14,16,18-22,24,27-30H,3-4,6-7,10-11,13H2,1-2H3/t14-,16-,18-,19?,20-,21+,22-,24-,25+,26-/m1/s1",
                    "standard_inchi_key": "ROSSVNHEVRUXGM-HEMPLKHUSA-N",
                    "name": None,
                    "iupac_name": "(5~{S},7~{S},8~{R},10~{a}~{S})-7-[2-(3-furyl)ethyl]-7,8-dimethyl-5-[(2~{R},3~{R},4~{S},5~{S},6~{R})-3,4,5-trihydroxy-6-(hydroxymethyl)tetrahydropyran-2-yl]oxy-5,6,6~{a},8,9,10-hexahydro-1~{H}-benzo[d]isobenzofuran-3-one",
                    "annotation_level": "5",
                    "total_atom_count": "71",
                    "heavy_atom_count": "35",
                    "molecular_weight": "492.57",
                    "exact_molecular_weight": "492.23593",
                    "molecular_formula": "C26H36O9",
                    "alogp": "1.32",
                    "topological_polar_surface_area": "138.82",
                    "rotatable_bond_count": "6",
                    "hydrogen_bond_acceptors": "9",
                    "hydrogen_bond_donors": "4",
                    "hydrogen_bond_acceptors_lipinski": "9",
                    "hydrogen_bond_donors_lipinski": "4",
                    "lipinski_rule_of_five_violations": "0",
                    "aromatic_rings_count": "1",
                    "qed_drug_likeliness": "0.43",
                    "formal_charge": "0",
                    "fractioncsp3": "0.73",
                    "number_of_minimal_rings": "5",
                    "van_der_walls_volume": "440.66",
                    "contains_sugar": True,
                    "contains_ring_sugars": True,
                    "contains_linear_sugars": False,
                    "murcko_framework": "o1ccc(c1)CCC2CCCC34C(=CC(OC5OCCCC5)CC23)COC4",
                    "np_likeness": "3.02",
                    "np_classifier_is_glycoside": True,
                    "number_of_organisms": "1",
                    "chemical_class_id": 274,
                    "chemical_sub_class_id": 266,
                    "direct_parent_classification_id": 1214,
                    "chemical_super_class_id": 16,
                    "np_classifier_pathway_id": 7,
                    "np_classifier_superclass_id": 16,
                    "np_classifier_class_id": 170,
                }
            ]
        },
    )


class CompoundSearchExportFile(CompoundSearchBase):
    order_by: Optional[str] = Field(
        None,
        description="Field name to order the results by",
    )
    order_desc: Optional[bool] = Field(
        False,
        description="Whether to order the results in descending order",
    )


class CompoundSearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    count: int
    offset: int
    limit: int
    results: List[CompoundBase]


class Quartile(BaseModel):
    min: float = Field(..., description="Minimum value")
    q25: float = Field(..., description="25th percentile")
    q50: float = Field(..., description="50th percentile (median)")
    q75: float = Field(..., description="75th percentile")
    max: float = Field(..., description="Maximum value")
    not_null_percentage: float = Field(
        ..., description="Percentage of non-null values for this property"
    )


class BooleanStatistics(BaseModel):
    true_percentage: float = Field(..., description="Percentage of true values")
    false_percentage: float = Field(..., description="Percentage of false values")
    null_percentage: float = Field(..., description="Percentage of null values")


class CompoundSearchResultStatistics(BaseModel):
    total_atom_count: Quartile
    heavy_atom_count: Quartile
    molecular_weight: Quartile
    alogp: Quartile
    topological_polar_surface_area: Quartile
    rotatable_bond_count: Quartile
    hydrogen_bond_acceptors: Quartile
    hydrogen_bond_donors: Quartile
    hydrogen_bond_acceptors_lipinski: Quartile
    hydrogen_bond_donors_lipinski: Quartile
    aromatic_rings_count: Quartile
    qed_drug_likeliness: Quartile
    formal_charge: Quartile
    fractioncsp3: Quartile
    number_of_minimal_rings: Quartile
    van_der_walls_volume: Quartile
    np_likeness: Quartile
    number_of_organisms: Quartile
    contains_sugar: BooleanStatistics
    contains_ring_sugars: BooleanStatistics
    contains_linear_sugars: BooleanStatistics
    np_classifier_is_glycoside: BooleanStatistics


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
