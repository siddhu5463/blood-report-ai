import pytest

from medicine_db import get_medicine_suggestions
from prescription_checker import check_prescription


def suggestions_for(medicines, *flags):
    return get_medicine_suggestions(
        [{"test": test, "issue": issue, "within_hrt_scope": True} for test, issue in flags],
        medicines,
    )


@pytest.fixture
def glucose_and_hba1c(medicines):
    return suggestions_for(medicines, ("Glucose", "High"), ("HbA1c", "High"))


def test_one_medicine_can_cover_several_issues(glucose_and_hba1c):
    report = check_prescription(["Metformin"], glucose_and_hba1c)
    assert report["match_score"] == 100
    assert report["covered_issues"] == 2
    assert report["missed_suggestions"] == []
    assert report["extra_prescriptions"] == []
    assert report["total_ai_suggested"] == 1


def test_dose_and_case_do_not_block_a_match(glucose_and_hba1c):
    report = check_prescription(["  metformin 500mg twice daily "], glucose_and_hba1c)
    assert report["match_score"] == 100


def test_similar_name_is_not_a_match(glucose_and_hba1c):
    report = check_prescription(["Metformin-like herbal"], glucose_and_hba1c)
    assert report["match_score"] == 0


def test_partial_coverage_and_extras(medicines):
    suggestions = suggestions_for(medicines, ("Estradiol", "High"), ("Glucose", "High"), ("DHEA", "Low"))
    report = check_prescription(["Anastrozole", "Aspirin"], suggestions)

    assert report["match_score"] == 33
    assert report["covered_issues"] == 1
    assert report["total_issues"] == 3
    assert report["extra_prescriptions"] == ["Aspirin"]
    assert [m["test"] for m in report["missed_suggestions"]] == ["Glucose", "DHEA"]
    assert report["missed_suggestions"][0]["options"] == ["Metformin"]


def test_issues_without_options_are_not_scored(medicines):
    suggestions = get_medicine_suggestions([
        {"test": "Estradiol", "issue": "High", "within_hrt_scope": True},
        {"test": "Sodium",    "issue": "Low",  "within_hrt_scope": True},   # nothing in database
        {"test": "AST",       "issue": "High", "within_hrt_scope": False},  # referred out
    ], medicines)
    report = check_prescription(["Anastrozole"], suggestions)
    assert report["total_issues"] == 1
    assert report["match_score"] == 100


def test_nothing_to_match_scores_100():
    report = check_prescription(["Aspirin"], [])
    assert report["match_score"] == 100
    assert report["extra_prescriptions"] == ["Aspirin"]


def test_duplicate_and_blank_lines_are_ignored(glucose_and_hba1c):
    report = check_prescription(["Metformin", "", "metformin"], glucose_and_hba1c)
    assert report["total_prescribed"] == 1
    assert report["extra_prescriptions"] == []
