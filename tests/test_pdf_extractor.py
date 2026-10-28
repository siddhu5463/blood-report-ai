import pytest

from pdf_extractor import REFERENCE_RANGES, canonical_marker, parse_blood_values, process_blood_report


# ── The sample report, end to end

@pytest.fixture(scope="module")
def sample_values(sample_pdf):
    return process_blood_report(sample_pdf)["blood_values"]


@pytest.mark.parametrize("marker, value, status", [
    ("Testosterone",      312,   "Normal"),
    ("Free Testosterone", 6.2,   "Normal"),
    ("Estradiol",         42,    "High"),
    ("DHEA",              82,    "Low"),     # printed as "DHEA-S"
    ("Free T3",           2.6,   "Normal"),
    ("Free T4",           0.9,   "Normal"),
    ("Glucose",           112,   "High"),
    ("HbA1c",             5.9,   "High"),
    ("AST",               42,    "High"),    # used to be read from "Glucose (Fasting) 112"
    ("Cholesterol",       215,   "High"),
    ("HDL",               48,    "Normal"),
    ("LDL",               138,   "High"),
    ("Triglycerides",     178,   "High"),
    ("Hemoglobin",        14.8,  "Normal"),
    ("Platelets",         220,   "Normal"),
])
def test_sample_report_values(sample_values, marker, value, status):
    assert sample_values[marker]["value"] == value
    assert sample_values[marker]["status"] == status


def test_sample_report_finds_every_row(sample_values):
    # 27 test rows in generate_sample_report.py
    assert len(sample_values) == 27


def test_sample_report_uses_printed_ranges(sample_values):
    assert sample_values["HbA1c"]["ref_range"] == "< 5.7"
    assert sample_values["HDL"]["ref_range"] == "> 40"
    assert sample_values["Estradiol"]["ref_range"] == "10 - 40"
    assert all(v["ref_source"] == "report" for v in sample_values.values())


def test_sample_report_patient_info(sample_pdf):
    info = process_blood_report(sample_pdf)["patient_info"]
    assert info == {"report_date": "03/15/2024", "age": 45}


# ── Parsing edge cases

def test_marker_name_inside_another_word_is_ignored():
    values = parse_blood_values("Glucose (Fasting) 112 mg/dL\n")
    assert "AST" not in values
    assert values["Glucose"]["value"] == 112


def test_default_range_used_when_report_has_none():
    values = parse_blood_values("Glucose: 95 mg/dL\n")
    assert values["Glucose"]["status"] == "Normal"
    assert values["Glucose"]["ref_range"] == "70 - 100"
    assert values["Glucose"]["ref_source"] == "default"


def test_report_range_overrides_default():
    # Female-range estradiol: 150 would be High against the built-in 10-40
    values = parse_blood_values("Estradiol 150 pg/mL 30 - 400\n")
    assert values["Estradiol"]["status"] == "Normal"
    assert values["Estradiol"]["ref_range"] == "30 - 400"


def test_thousands_separator():
    values = parse_blood_values("Platelets 1,200 K/uL 150 - 400\n")
    assert values["Platelets"]["value"] == 1200
    assert values["Platelets"]["status"] == "High"


def test_less_than_value():
    values = parse_blood_values("Progesterone <0.2 ng/mL 0.3 - 1.2\n")
    assert values["Progesterone"]["value"] == 0.2
    assert values["Progesterone"]["status"] == "Low"


def test_one_sided_ranges():
    values = parse_blood_values("HDL Cholesterol 35 mg/dL > 40\nTriglycerides 120 mg/dL < 150\n")
    assert values["HDL"]["status"] == "Low"
    assert values["Triglycerides"]["status"] == "Normal"


def test_hemoglobin_a1c_is_not_hemoglobin():
    values = parse_blood_values("Hemoglobin A1c 6.1 %\n")
    assert values["HbA1c"]["value"] == 6.1
    assert "Hemoglobin" not in values


def test_free_testosterone_is_not_total():
    values = parse_blood_values("Testosterone (Free) 6.2 ng/dL 5.0 - 21.0\nTestosterone (Total) 450 ng/dL\n")
    assert values["Testosterone"]["value"] == 450
    assert values["Free Testosterone"]["value"] == 6.2


def test_free_testosterone_without_range_is_skipped():
    # No built-in range for free testosterone (it depends on the units), so nothing to compare against
    assert parse_blood_values("Free Testosterone 6.2 ng/dL\n") == {}


def test_related_lines_are_not_mistaken_for_markers():
    text = "Non-HDL Cholesterol 160 mg/dL\nCholesterol/HDL Ratio 4.5\n"
    assert parse_blood_values(text) == {}


def test_first_occurrence_wins():
    values = parse_blood_values("Glucose 90 mg/dL\nGlucose 150 mg/dL\n")
    assert values["Glucose"]["value"] == 90


def test_vitamin_d_with_25_oh_name():
    values = parse_blood_values("Vitamin D, 25-Hydroxy 22 ng/mL 30 - 100\n")
    assert values["Vitamin D"]["value"] == 22
    assert values["Vitamin D"]["status"] == "Low"


def test_unit_with_power_of_ten():
    values = parse_blood_values("WBC 7.2 10^3/uL 4.5 - 11.0\n")
    assert values["WBC"]["unit"] == "10^3/uL"
    assert values["WBC"]["status"] == "Normal"


# ── Name normalisation

@pytest.mark.parametrize("name, expected", [
    ("LDL Cholesterol",       "LDL"),
    ("HDL-C",                 "HDL"),
    ("Total Cholesterol",     "Cholesterol"),
    ("Estradiol (E2)",        "Estradiol"),
    ("DHEA-S",                "DHEA"),
    ("Glucose (Fasting)",     "Glucose"),
    ("Hemoglobin A1c",        "HbA1c"),
    ("Free T4",               "Free T4"),
    ("Testosterone (Total)",  "Testosterone"),
    ("Testosterone (Free)",   "Free Testosterone"),
    ("Something Unknown",     "Something Unknown"),
])
def test_canonical_marker(name, expected):
    assert canonical_marker(name) == expected


def test_every_marker_name_is_its_own_canonical_name():
    for marker in REFERENCE_RANGES:
        assert canonical_marker(marker) == marker
