import pytest

from medicine_db import find_medicines_for_flag, get_medicine_suggestions, normalize_direction
from pdf_extractor import REFERENCE_RANGES


def names(meds):
    return [m["name"] for m in meds]


def test_database_targets_are_known_markers(medicines):
    for med in medicines:
        assert med["targets"], med["id"]
        for marker, direction in med["targets"].items():
            assert marker in REFERENCE_RANGES, f"{med['id']}: unknown marker {marker}"
            assert direction in ("High", "Low"), f"{med['id']}: bad direction {direction}"


def test_database_ids_are_unique(medicines):
    ids = [m["id"] for m in medicines]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("test, issue, expected", [
    ("TSH",          "High", ["Levothyroxine"]),
    ("Free T4",      "Low",  ["Levothyroxine"]),
    ("Free T4",      "High", []),               # hyperthyroid: levothyroxine would be wrong
    ("Glucose",      "High", ["Metformin"]),    # Vitamin D3 is not a glucose treatment
    ("Vitamin D",    "Low",  ["Vitamin D3"]),
    ("Estradiol",    "High", ["Anastrozole"]),
    ("Estradiol",    "Low",  ["Estradiol Patch"]),
    ("DHEA",         "Low",  ["DHEA Supplement"]),
])
def test_find_medicines_for_flag(medicines, test, issue, expected):
    assert names(find_medicines_for_flag(test, issue, medicines)) == expected


@pytest.mark.parametrize("ai_name", ["LDL", "LDL Cholesterol", "ldl-c"])
def test_ai_test_names_are_normalised(medicines, ai_name):
    assert names(find_medicines_for_flag(ai_name, "High", medicines)) == ["Omega-3 Fish Oil"]


@pytest.mark.parametrize("issue, expected", [
    ("High", "High"), ("high", "High"), ("Elevated", "High"),
    ("Low", "Low"), ("Low (borderline)", "Low"), ("decreased", "Low"),
])
def test_normalize_direction(issue, expected):
    assert normalize_direction(issue) == expected


def test_outside_scope_is_referred(medicines):
    [item] = get_medicine_suggestions([{"test": "LDL", "issue": "High", "within_hrt_scope": False}], medicines)
    assert item["action"] == "REFER TO SPECIALIST"
    assert item["medicines"] == []


def test_no_match_in_database(medicines):
    [item] = get_medicine_suggestions([{"test": "Sodium", "issue": "Low", "within_hrt_scope": True}], medicines)
    assert item["action"] == "No match in database"
    assert item["medicines"] == []
