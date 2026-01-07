import os
from typing import Generator

from sqlalchemy.orm.session import Session

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from biokb_coconut.api.main import app, get_session
from biokb_coconut.db.manager import DbManager

# Create a new test database engine (SQLite in-memory for testing)
os.makedirs("tests/dbs", exist_ok=True)
# Delete Database before running to ensure it is created anew
if os.path.exists("tests/dbs/test.db"):
    os.remove("tests/dbs/test.db")
test_engine = create_engine("sqlite:///tests/dbs/test.db")
# test_engine = create_engine(
#     "mysql+pymysql://biokb_user:biokb_passwd@127.0.0.1:3307/biokb"
# )
TestSessionLocal = sessionmaker(bind=test_engine)

### NOTE: If you want to test the API yourself in your browser, remember to export the connection string first (`export CONNECTION_STR="sqlite:///tests/dbs/test.db"` in a Python terminal)


# Dependency override to use test database
def override_get_db() -> Generator[Session, None, None]:
    db: Session = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Apply the override to the FastAPI dependency
app.dependency_overrides[get_session] = override_get_db


@pytest.fixture()
def client_with_data():
    # Create tables in the test database
    test_data_folder = os.path.join("tests", "data")
    dm = DbManager(test_engine)
    dm.set_path_to_file(os.path.join(test_data_folder, "dummy_data.zip"))
    dm.import_data()
    return TestClient(app)


def test_server(client_with_data: TestClient) -> None:
    response = client_with_data.get("/")
    assert response.status_code == 200
    assert response.json() == {"msg": "Running!"}


class TestCompound:
    def test_get_compound(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("compounds/?identifier=1")
        assert response.status_code == 200
        data = response.json()
        # Note: In the original result, there are many boolean columns that are replaced here with capital letters (False instead of false and True instead of true)
        expected = {
        "count": 1,
        "offset": 0,
        "limit": 10,
        "results": [
            {
            "id": 1,
            "identifier": "1",
            "canonical_smiles": "Smile_1",
            "standard_inchi": "Inchi_1",
            "standard_inchi_key": "inchi_key_1",
            "name": "Esorubicin",
            "iupac_name": "(7~{S},9~{S})-7-[(2~{S},4~{R},6~{S})-4-amino-6-methyl-tetrahydropyran-2-yl]oxy-6,9,11-trihydroxy-9-(2-hydroxyacetyl)-4-methoxy-8,10-dihydro-7~{H}-tetracene-5,12-dione",
            "annotation_level": 3,
            "total_atom_count": 67,
            "heavy_atom_count": 38,
            "molecular_weight": 527.53,
            "exact_molecular_weight": 527.17915,
            "molecular_formula": "C27H29NO10",
            "alogp": 1.03,
            "topological_polar_surface_area": 185.84,
            "rotatable_bond_count": 5,
            "hydrogen_bond_acceptors": 11,
            "hydrogen_bond_donors": 5,
            "hydrogen_bond_acceptors_lipinski": 11,
            "hydrogen_bond_donors_lipinski": 5,
            "lipinski_rule_of_five_violations": 2,
            "aromatic_rings_count": 2,
            "qed_drug_likeliness": 0.3,
            "formal_charge": 0,
            "fractioncsp3": 0.44,
            "number_of_minimal_rings": 5,
            "van_der_walls_volume": 445.49,
            "contains_sugar": False,
            "contains_ring_sugars": False,
            "contains_linear_sugars": False,
            "murcko_framework": "O1CCCCC1OC2c3cc4c(cc3CCC2)Cc5ccccc5C4",
            "np_likeness": 1.56,
            "chemical_class": "Naphthacenes",
            "chemical_sub_class": "Tetracenequinones",
            "chemical_super_class": "Benzenoids",
            "direct_parent_classification": "Tetracenequinones",
            "np_classifier_pathway": "Polyketides",
            "np_classifier_superclass": "Polycyclic aromatic polyketides",
            "np_classifier_class": "Anthracyclines",
            "np_classifier_is_glycoside": True
            }
        ]
        }
        assert data == expected

    def test_list_compounds(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/compounds/")
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 3

    def test_list_compounds_offset(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/compounds/?offset=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1

    def test_list_compounds_limit(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/compounds/?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 2

    def test_list_compounds_offset_limit(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("compounds/?offset=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        expected = {
        "count": 3,
        "offset": 2,
        "limit": 2,
        "results": [
            {
            "id": 3,
            "identifier": "3",
            "canonical_smiles": "Smile_3",
            "standard_inchi": "Inchi_3",
            "standard_inchi_key": "inchi_key_3",
            "name": "Talotrexin",
            "iupac_name": "2-[[(4~{S})-4-carboxy-4-[[4-[(2,4-diaminopteridin-6-yl)methylamino]benzoyl]amino]butyl]carbamoyl]benzoic acid",
            "annotation_level": 3,
            "total_atom_count": 69,
            "heavy_atom_count": 42,
            "molecular_weight": 573.57,
            "exact_molecular_weight": 573.20843,
            "molecular_formula": "C27H27N9O6",
            "alogp": 1.29,
            "topological_polar_surface_area": 248.43,
            "rotatable_bond_count": 12,
            "hydrogen_bond_acceptors": 11,
            "hydrogen_bond_donors": 7,
            "hydrogen_bond_acceptors_lipinski": 11,
            "hydrogen_bond_donors_lipinski": 7,
            "lipinski_rule_of_five_violations": 3,
            "aromatic_rings_count": 4,
            "qed_drug_likeliness": 0.12,
            "formal_charge": 0,
            "fractioncsp3": 0.19,
            "number_of_minimal_rings": 4,
            "van_der_walls_volume": 494.02,
            "contains_sugar": False,
            "contains_ring_sugars": False,
            "contains_linear_sugars": False,
            "murcko_framework": "n1cnc2ncc(nc2c1)CNc3ccc(cc3)CNCCCCNCc4ccccc4",
            "np_likeness": -0.62,
            "chemical_class": "Benzene and substituted derivatives",
            "chemical_sub_class": "Benzoic acids and derivatives",
            "chemical_super_class": "Benzenoids",
            "direct_parent_classification": "Hippuric acids and derivatives",
            "np_classifier_pathway": "Alkaloids",
            "np_classifier_superclass": "NoSuperclass",
            "np_classifier_class": "NoSuperclass",
            "np_classifier_is_glycoside": False
            }
        ]
        }
        assert data == expected

class TestDois:
    def test_get_doi(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("dois/?identifier=DOI_1")
        assert response.status_code == 200
        data = response.json()
        # Note: In the original result, there are many boolean columns that are replaced here with 0 for false and 1 for true
        expected = {
        "count": 1,
        "offset": 0,
        "limit": 10,
        "results": [
            {
            "id": 1,
            "identifier": "DOI_1",
            "compounds": [
                {
                "id": 1,
                "identifier": "1",
                "canonical_smiles": "Smile_1",
                "standard_inchi": "Inchi_1",
                "standard_inchi_key": "inchi_key_1",
                "name": "Esorubicin",
                "iupac_name": "(7~{S},9~{S})-7-[(2~{S},4~{R},6~{S})-4-amino-6-methyl-tetrahydropyran-2-yl]oxy-6,9,11-trihydroxy-9-(2-hydroxyacetyl)-4-methoxy-8,10-dihydro-7~{H}-tetracene-5,12-dione",
                "annotation_level": 3,
                "total_atom_count": 67,
                "heavy_atom_count": 38,
                "molecular_weight": 527.53,
                "exact_molecular_weight": 527.17915,
                "molecular_formula": "C27H29NO10",
                "alogp": 1.03,
                "topological_polar_surface_area": 185.84,
                "rotatable_bond_count": 5,
                "hydrogen_bond_acceptors": 11,
                "hydrogen_bond_donors": 5,
                "hydrogen_bond_acceptors_lipinski": 11,
                "hydrogen_bond_donors_lipinski": 5,
                "lipinski_rule_of_five_violations": 2,
                "aromatic_rings_count": 2,
                "qed_drug_likeliness": 0.3,
                "formal_charge": 0,
                "fractioncsp3": 0.44,
                "number_of_minimal_rings": 5,
                "van_der_walls_volume": 445.49,
                "contains_sugar": False,
                "contains_ring_sugars": False,
                "contains_linear_sugars": False,
                "murcko_framework": "O1CCCCC1OC2c3cc4c(cc3CCC2)Cc5ccccc5C4",
                "np_likeness": 1.56,
                "chemical_class": "Naphthacenes",
                "chemical_sub_class": "Tetracenequinones",
                "chemical_super_class": "Benzenoids",
                "direct_parent_classification": "Tetracenequinones",
                "np_classifier_pathway": "Polyketides",
                "np_classifier_superclass": "Polycyclic aromatic polyketides",
                "np_classifier_class": "Anthracyclines",
                "np_classifier_is_glycoside": True
                }
            ]
            }
        ]
        }
        assert data == expected

    def test_list_dois(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/dois/")
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 3

    def test_list_dois_offset(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/dois/?offset=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1

    def test_list_dois_limit(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/dois/?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 2

    def test_list_dois_offset_limit(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("dois/?offset=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        expected = {
        "count": 3,
        "offset": 2,
        "limit": 2,
        "results": [
            {
            "id": 3,
            "identifier": "DOI_3",
            "compounds": [
                {
                "id": 3,
                "identifier": "3",
                "canonical_smiles": "Smile_3",
                "standard_inchi": "Inchi_3",
                "standard_inchi_key": "inchi_key_3",
                "name": "Talotrexin",
                "iupac_name": "2-[[(4~{S})-4-carboxy-4-[[4-[(2,4-diaminopteridin-6-yl)methylamino]benzoyl]amino]butyl]carbamoyl]benzoic acid",
                "annotation_level": 3,
                "total_atom_count": 69,
                "heavy_atom_count": 42,
                "molecular_weight": 573.57,
                "exact_molecular_weight": 573.20843,
                "molecular_formula": "C27H27N9O6",
                "alogp": 1.29,
                "topological_polar_surface_area": 248.43,
                "rotatable_bond_count": 12,
                "hydrogen_bond_acceptors": 11,
                "hydrogen_bond_donors": 7,
                "hydrogen_bond_acceptors_lipinski": 11,
                "hydrogen_bond_donors_lipinski": 7,
                "lipinski_rule_of_five_violations": 3,
                "aromatic_rings_count": 4,
                "qed_drug_likeliness": 0.12,
                "formal_charge": 0,
                "fractioncsp3": 0.19,
                "number_of_minimal_rings": 4,
                "van_der_walls_volume": 494.02,
                "contains_sugar": False,
                "contains_ring_sugars": False,
                "contains_linear_sugars": False,
                "murcko_framework": "n1cnc2ncc(nc2c1)CNc3ccc(cc3)CNCCCCNCc4ccccc4",
                "np_likeness": -0.62,
                "chemical_class": "Benzene and substituted derivatives",
                "chemical_sub_class": "Benzoic acids and derivatives",
                "chemical_super_class": "Benzenoids",
                "direct_parent_classification": "Hippuric acids and derivatives",
                "np_classifier_pathway": "Alkaloids",
                "np_classifier_superclass": "NoSuperclass",
                "np_classifier_class": "NoSuperclass",
                "np_classifier_is_glycoside": False
                }
            ]
            }
        ]
        }
        assert data == expected 

class TestOrganisms:
    def test_get_organism(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("organisms/?name=Organism_1")
        assert response.status_code == 200
        data = response.json()
        # Note: In the original result, there are many boolean columns that are replaced here with 0 for false and 1 for true
        expected = {
        "count": 1,
        "offset": 0,
        "limit": 10,
        "results": [
            {
            "id": 1,
            "name": "Organism_1",
            "compounds": [
                {
                "id": 1,
                "identifier": "1",
                "canonical_smiles": "Smile_1",
                "standard_inchi": "Inchi_1",
                "standard_inchi_key": "inchi_key_1",
                "name": "Esorubicin",
                "iupac_name": "(7~{S},9~{S})-7-[(2~{S},4~{R},6~{S})-4-amino-6-methyl-tetrahydropyran-2-yl]oxy-6,9,11-trihydroxy-9-(2-hydroxyacetyl)-4-methoxy-8,10-dihydro-7~{H}-tetracene-5,12-dione",
                "annotation_level": 3,
                "total_atom_count": 67,
                "heavy_atom_count": 38,
                "molecular_weight": 527.53,
                "exact_molecular_weight": 527.17915,
                "molecular_formula": "C27H29NO10",
                "alogp": 1.03,
                "topological_polar_surface_area": 185.84,
                "rotatable_bond_count": 5,
                "hydrogen_bond_acceptors": 11,
                "hydrogen_bond_donors": 5,
                "hydrogen_bond_acceptors_lipinski": 11,
                "hydrogen_bond_donors_lipinski": 5,
                "lipinski_rule_of_five_violations": 2,
                "aromatic_rings_count": 2,
                "qed_drug_likeliness": 0.3,
                "formal_charge": 0,
                "fractioncsp3": 0.44,
                "number_of_minimal_rings": 5,
                "van_der_walls_volume": 445.49,
                "contains_sugar": False,
                "contains_ring_sugars": False,
                "contains_linear_sugars": False,
                "murcko_framework": "O1CCCCC1OC2c3cc4c(cc3CCC2)Cc5ccccc5C4",
                "np_likeness": 1.56,
                "chemical_class": "Naphthacenes",
                "chemical_sub_class": "Tetracenequinones",
                "chemical_super_class": "Benzenoids",
                "direct_parent_classification": "Tetracenequinones",
                "np_classifier_pathway": "Polyketides",
                "np_classifier_superclass": "Polycyclic aromatic polyketides",
                "np_classifier_class": "Anthracyclines",
                "np_classifier_is_glycoside": True
                }
            ]
            }
        ]
        }
        assert data == expected

    def test_list_organisms(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/organisms/")
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 3

    def test_list_organisms_offset(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/organisms/?offset=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1

    def test_list_organisms_limit(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/organisms/?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 2

    def test_list_organisms_offset_limit(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("organisms/?offset=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        expected = {
        "count": 3,
        "offset": 2,
        "limit": 2,
        "results": [
            {
            "id": 3,
            "name": "Organism_3",
            "compounds": [
                {
                "id": 3,
                "identifier": "3",
                "canonical_smiles": "Smile_3",
                "standard_inchi": "Inchi_3",
                "standard_inchi_key": "inchi_key_3",
                "name": "Talotrexin",
                "iupac_name": "2-[[(4~{S})-4-carboxy-4-[[4-[(2,4-diaminopteridin-6-yl)methylamino]benzoyl]amino]butyl]carbamoyl]benzoic acid",
                "annotation_level": 3,
                "total_atom_count": 69,
                "heavy_atom_count": 42,
                "molecular_weight": 573.57,
                "exact_molecular_weight": 573.20843,
                "molecular_formula": "C27H27N9O6",
                "alogp": 1.29,
                "topological_polar_surface_area": 248.43,
                "rotatable_bond_count": 12,
                "hydrogen_bond_acceptors": 11,
                "hydrogen_bond_donors": 7,
                "hydrogen_bond_acceptors_lipinski": 11,
                "hydrogen_bond_donors_lipinski": 7,
                "lipinski_rule_of_five_violations": 3,
                "aromatic_rings_count": 4,
                "qed_drug_likeliness": 0.12,
                "formal_charge": 0,
                "fractioncsp3": 0.19,
                "number_of_minimal_rings": 4,
                "van_der_walls_volume": 494.02,
                "contains_sugar": False,
                "contains_ring_sugars": False,
                "contains_linear_sugars": False,
                "murcko_framework": "n1cnc2ncc(nc2c1)CNc3ccc(cc3)CNCCCCNCc4ccccc4",
                "np_likeness": -0.62,
                "chemical_class": "Benzene and substituted derivatives",
                "chemical_sub_class": "Benzoic acids and derivatives",
                "chemical_super_class": "Benzenoids",
                "direct_parent_classification": "Hippuric acids and derivatives",
                "np_classifier_pathway": "Alkaloids",
                "np_classifier_superclass": "NoSuperclass",
                "np_classifier_class": "NoSuperclass",
                "np_classifier_is_glycoside": False
                }
            ]
            }
        ]
        }
        assert data == expected


class TestSynonyms:
    def test_get_synonym(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("synonyms/?name=Synonym_1")
        assert response.status_code == 200
        data = response.json()
        # Note: In the original result, there are many boolean columns that are replaced here with 0 for false and 1 for true
        expected = {
        "count": 1,
        "offset": 0,
        "limit": 10,
        "results": [
            {
            "id": 1,
            "name": "Synonym_1",
            "compounds": [
                {
                "id": 1,
                "identifier": "1",
                "canonical_smiles": "Smile_1",
                "standard_inchi": "Inchi_1",
                "standard_inchi_key": "inchi_key_1",
                "name": "Esorubicin",
                "iupac_name": "(7~{S},9~{S})-7-[(2~{S},4~{R},6~{S})-4-amino-6-methyl-tetrahydropyran-2-yl]oxy-6,9,11-trihydroxy-9-(2-hydroxyacetyl)-4-methoxy-8,10-dihydro-7~{H}-tetracene-5,12-dione",
                "annotation_level": 3,
                "total_atom_count": 67,
                "heavy_atom_count": 38,
                "molecular_weight": 527.53,
                "exact_molecular_weight": 527.17915,
                "molecular_formula": "C27H29NO10",
                "alogp": 1.03,
                "topological_polar_surface_area": 185.84,
                "rotatable_bond_count": 5,
                "hydrogen_bond_acceptors": 11,
                "hydrogen_bond_donors": 5,
                "hydrogen_bond_acceptors_lipinski": 11,
                "hydrogen_bond_donors_lipinski": 5,
                "lipinski_rule_of_five_violations": 2,
                "aromatic_rings_count": 2,
                "qed_drug_likeliness": 0.3,
                "formal_charge": 0,
                "fractioncsp3": 0.44,
                "number_of_minimal_rings": 5,
                "van_der_walls_volume": 445.49,
                "contains_sugar": False,
                "contains_ring_sugars": False,
                "contains_linear_sugars": False,
                "murcko_framework": "O1CCCCC1OC2c3cc4c(cc3CCC2)Cc5ccccc5C4",
                "np_likeness": 1.56,
                "chemical_class": "Naphthacenes",
                "chemical_sub_class": "Tetracenequinones",
                "chemical_super_class": "Benzenoids",
                "direct_parent_classification": "Tetracenequinones",
                "np_classifier_pathway": "Polyketides",
                "np_classifier_superclass": "Polycyclic aromatic polyketides",
                "np_classifier_class": "Anthracyclines",
                "np_classifier_is_glycoside": True
                }
            ]
            }
        ]
        }
        assert data == expected

    def test_list_synonyms(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/synonyms/")
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 3

    def test_list_synonyms_offset(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/synonyms/?offset=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1

    def test_list_synonyms_limit(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/synonyms/?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 2

    def test_list_synonyms_offset_limit(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("synonyms/?offset=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        expected = {
        "count": 3,
        "offset": 2,
        "limit": 2,
        "results": [
            {
            "id": 3,
            "name": "Synonym_3",
            "compounds": [
                {
                "id": 3,
                "identifier": "3",
                "canonical_smiles": "Smile_3",
                "standard_inchi": "Inchi_3",
                "standard_inchi_key": "inchi_key_3",
                "name": "Talotrexin",
                "iupac_name": "2-[[(4~{S})-4-carboxy-4-[[4-[(2,4-diaminopteridin-6-yl)methylamino]benzoyl]amino]butyl]carbamoyl]benzoic acid",
                "annotation_level": 3,
                "total_atom_count": 69,
                "heavy_atom_count": 42,
                "molecular_weight": 573.57,
                "exact_molecular_weight": 573.20843,
                "molecular_formula": "C27H27N9O6",
                "alogp": 1.29,
                "topological_polar_surface_area": 248.43,
                "rotatable_bond_count": 12,
                "hydrogen_bond_acceptors": 11,
                "hydrogen_bond_donors": 7,
                "hydrogen_bond_acceptors_lipinski": 11,
                "hydrogen_bond_donors_lipinski": 7,
                "lipinski_rule_of_five_violations": 3,
                "aromatic_rings_count": 4,
                "qed_drug_likeliness": 0.12,
                "formal_charge": 0,
                "fractioncsp3": 0.19,
                "number_of_minimal_rings": 4,
                "van_der_walls_volume": 494.02,
                "contains_sugar": False,
                "contains_ring_sugars": False,
                "contains_linear_sugars": False,
                "murcko_framework": "n1cnc2ncc(nc2c1)CNc3ccc(cc3)CNCCCCNCc4ccccc4",
                "np_likeness": -0.62,
                "chemical_class": "Benzene and substituted derivatives",
                "chemical_sub_class": "Benzoic acids and derivatives",
                "chemical_super_class": "Benzenoids",
                "direct_parent_classification": "Hippuric acids and derivatives",
                "np_classifier_pathway": "Alkaloids",
                "np_classifier_superclass": "NoSuperclass",
                "np_classifier_class": "NoSuperclass",
                "np_classifier_is_glycoside": False
                }
            ]
            }
        ]
        }
        assert data == expected 

class TestCollections:
    def test_get_collection(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("collections/?name=Collection_1")
        assert response.status_code == 200
        data = response.json()
        # Note: In the original result, there are many boolean columns that are replaced here with 0 for false and 1 for true
        expected = {
        "count": 1,
        "offset": 0,
        "limit": 10,
        "results": [
            {
            "id": 1,
            "name": "Collection_1",
            "compound_identifiers": [
                "1"
            ]
            }
        ]
        }
        assert data == expected

    def test_list_collections(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/collections/")
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 3

    def test_list_collections_offset(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/collections/?offset=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1

    def test_list_collections_limit(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/collections/?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 2

    def test_list_collections_offset_limit(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("collections/?offset=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        expected = {
        "count": 3,
        "offset": 2,
        "limit": 2,
        "results": [
            {
            "id": 3,
            "name": "Collection_3",
            "compound_identifiers": [
                "3"
            ]
            }
        ]
        }
        assert data == expected 

class TestCas:
    def test_get_cas(self, client_with_data: TestClient):
        response = client_with_data.get("cas/?number=Cas_1")
        assert response.status_code == 200
        data = response.json()
        # Note: In the original result, there are many boolean columns that are replaced here with 0 for false and 1 for true
        expected = {
        "count": 1,
        "offset": 0,
        "limit": 10,
        "results": [
            {
            "id": 1,
            "number": "Cas_1",
            "compounds": [
                {
                "id": 1,
                "identifier": "1",
                "canonical_smiles": "Smile_1",
                "standard_inchi": "Inchi_1",
                "standard_inchi_key": "inchi_key_1",
                "name": "Esorubicin",
                "iupac_name": "(7~{S},9~{S})-7-[(2~{S},4~{R},6~{S})-4-amino-6-methyl-tetrahydropyran-2-yl]oxy-6,9,11-trihydroxy-9-(2-hydroxyacetyl)-4-methoxy-8,10-dihydro-7~{H}-tetracene-5,12-dione",
                "annotation_level": 3,
                "total_atom_count": 67,
                "heavy_atom_count": 38,
                "molecular_weight": 527.53,
                "exact_molecular_weight": 527.17915,
                "molecular_formula": "C27H29NO10",
                "alogp": 1.03,
                "topological_polar_surface_area": 185.84,
                "rotatable_bond_count": 5,
                "hydrogen_bond_acceptors": 11,
                "hydrogen_bond_donors": 5,
                "hydrogen_bond_acceptors_lipinski": 11,
                "hydrogen_bond_donors_lipinski": 5,
                "lipinski_rule_of_five_violations": 2,
                "aromatic_rings_count": 2,
                "qed_drug_likeliness": 0.3,
                "formal_charge": 0,
                "fractioncsp3": 0.44,
                "number_of_minimal_rings": 5,
                "van_der_walls_volume": 445.49,
                "contains_sugar": False,
                "contains_ring_sugars": False,
                "contains_linear_sugars": False,
                "murcko_framework": "O1CCCCC1OC2c3cc4c(cc3CCC2)Cc5ccccc5C4",
                "np_likeness": 1.56,
                "chemical_class": "Naphthacenes",
                "chemical_sub_class": "Tetracenequinones",
                "chemical_super_class": "Benzenoids",
                "direct_parent_classification": "Tetracenequinones",
                "np_classifier_pathway": "Polyketides",
                "np_classifier_superclass": "Polycyclic aromatic polyketides",
                "np_classifier_class": "Anthracyclines",
                "np_classifier_is_glycoside": True
                }
            ]
            }
        ]
        }
        assert data == expected

    def test_list_cas(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/cas/")
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 3

    def test_list_cas_offset(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/cas/?offset=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1

    def test_list_cas_limit(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("/cas/?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 2

    def test_list_cas_offset_limit(self, client_with_data: TestClient) -> None:
        response = client_with_data.get("cas/?offset=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        expected = {
        "count": 3,
        "offset": 2,
        "limit": 2,
        "results": [
            {
            "id": 3,
            "number": "Cas_3",
            "compounds": [
                {
                "id": 3,
                "identifier": "3",
                "canonical_smiles": "Smile_3",
                "standard_inchi": "Inchi_3",
                "standard_inchi_key": "inchi_key_3",
                "name": "Talotrexin",
                "iupac_name": "2-[[(4~{S})-4-carboxy-4-[[4-[(2,4-diaminopteridin-6-yl)methylamino]benzoyl]amino]butyl]carbamoyl]benzoic acid",
                "annotation_level": 3,
                "total_atom_count": 69,
                "heavy_atom_count": 42,
                "molecular_weight": 573.57,
                "exact_molecular_weight": 573.20843,
                "molecular_formula": "C27H27N9O6",
                "alogp": 1.29,
                "topological_polar_surface_area": 248.43,
                "rotatable_bond_count": 12,
                "hydrogen_bond_acceptors": 11,
                "hydrogen_bond_donors": 7,
                "hydrogen_bond_acceptors_lipinski": 11,
                "hydrogen_bond_donors_lipinski": 7,
                "lipinski_rule_of_five_violations": 3,
                "aromatic_rings_count": 4,
                "qed_drug_likeliness": 0.12,
                "formal_charge": 0,
                "fractioncsp3": 0.19,
                "number_of_minimal_rings": 4,
                "van_der_walls_volume": 494.02,
                "contains_sugar": False,
                "contains_ring_sugars": False,
                "contains_linear_sugars": False,
                "murcko_framework": "n1cnc2ncc(nc2c1)CNc3ccc(cc3)CNCCCCNCc4ccccc4",
                "np_likeness": -0.62,
                "chemical_class": "Benzene and substituted derivatives",
                "chemical_sub_class": "Benzoic acids and derivatives",
                "chemical_super_class": "Benzenoids",
                "direct_parent_classification": "Hippuric acids and derivatives",
                "np_classifier_pathway": "Alkaloids",
                "np_classifier_superclass": "NoSuperclass",
                "np_classifier_class": "NoSuperclass",
                "np_classifier_is_glycoside": False
                }
            ]
            }
        ]
        }
        assert data == expected

