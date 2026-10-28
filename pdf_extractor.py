# pdf_extractor.py
# WHAT THIS FILE DOES:
# Reads a blood report PDF and pulls out all the lab values
# Example output: {"Glucose": {"value": 95, "unit": "mg/dL", "status": "Normal"}}

import logging
import re          # helps us find patterns in text (like "Glucose: 95")

import pdfplumber  # reads PDF files

logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_path):
    """
    Opens a PDF file and reads all the text from every page.
    pdf_path = the location of the PDF on your computer, or an open file / BytesIO
    """
    full_text = ""  # we'll collect all text here

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:          # loop through every page
            text = page.extract_text()  # pull text from this page
            if text:                    # only add if page has text
                full_text += text + "\n"

    return full_text


# Default reference ranges for adults, used only when the report doesn't print its own.
# Format: "Marker": (min_normal, max_normal) — None means "no limit on that side".
# A marker with no default range (None) gets status "Unknown" unless the PDF gives a range.
# Values are in DEFAULT_UNITS below.
REFERENCE_RANGES = {
    "Glucose":           (70,   100),
    "HbA1c":             (None, 5.7),
    "Hemoglobin":        (13.5, 17.5),
    "Hematocrit":        (41,   53),
    "WBC":               (4.5,  11.0),
    "RBC":               (4.5,  5.9),
    "Platelets":         (150,  400),
    "Testosterone":      (300,  1000),
    "Free Testosterone": None,
    "Estradiol":         (10,   40),
    "FSH":               (1.5,  12.4),
    "LH":                (1.7,  8.6),
    "TSH":               (0.4,  4.0),
    "Free T3":           (2.3,  4.2),
    "Free T4":           (0.8,  1.8),
    "Cortisol":          (6,    23),
    "DHEA":              (110,  510),
    "Progesterone":      (0.3,  1.2),
    "Sodium":            (136,  145),
    "Potassium":         (3.5,  5.1),
    "Creatinine":        (0.7,  1.3),
    "ALT":               (7,    40),
    "AST":               (10,   40),
    "Cholesterol":       (None, 200),
    "HDL":               (40,   None),
    "LDL":               (None, 100),
    "Triglycerides":     (None, 150),
    "Vitamin D":         (30,   100),
}

# Female ranges that differ from the defaults above.
# Estradiol, Progesterone, FSH and LH depend on the menstrual cycle / menopause,
# so there is no safe single default — the report's own range is needed.
FEMALE_REFERENCE_RANGES = {
    "Testosterone":  (15,   70),
    "Hemoglobin":    (12.0, 15.5),
    "Hematocrit":    (36,   46),
    "RBC":           (4.0,  5.2),
    "Creatinine":    (0.5,  1.1),
    "HDL":           (50,   None),
    "DHEA":          (35,   430),
    "Estradiol":     None,
    "Progesterone":  None,
    "FSH":           None,
    "LH":            None,
}

# The unit the default ranges are written in
DEFAULT_UNITS = {
    "Glucose": "mg/dL", "HbA1c": "%", "Hemoglobin": "g/dL", "Hematocrit": "%",
    "WBC": "K/uL", "RBC": "M/uL", "Platelets": "K/uL",
    "Testosterone": "ng/dL", "Free Testosterone": "pg/mL", "Estradiol": "pg/mL",
    "FSH": "mIU/mL", "LH": "mIU/mL", "TSH": "mIU/L", "Free T3": "pg/mL", "Free T4": "ng/dL",
    "Cortisol": "ug/dL", "DHEA": "ug/dL", "Progesterone": "ng/mL",
    "Sodium": "mEq/L", "Potassium": "mEq/L", "Creatinine": "mg/dL", "ALT": "U/L", "AST": "U/L",
    "Cholesterol": "mg/dL", "HDL": "mg/dL", "LDL": "mg/dL", "Triglycerides": "mg/dL",
    "Vitamin D": "ng/mL",
}

# Other units labs use, and the factor that converts them to the default unit:
# value_in_default_unit = value * factor   (e.g. testosterone 10.4 nmol/L * 28.84 = 300 ng/dL)
_COUNT_UNITS = {"k/ul": 1, "10^3/ul": 1, "x10^3/ul": 1, "10^9/l": 1, "x10^9/l": 1, "thou/ul": 1}
UNIT_CONVERSIONS = {
    "Glucose":       {"mmol/l": 18.016},
    "Hemoglobin":    {"g/l": 0.1},
    "WBC":           _COUNT_UNITS,
    "Platelets":     _COUNT_UNITS,
    "RBC":           {"m/ul": 1, "10^6/ul": 1, "x10^6/ul": 1, "10^12/l": 1, "x10^12/l": 1},
    "Testosterone":  {"nmol/l": 28.84},
    "Estradiol":     {"pmol/l": 0.2724},
    "FSH":           {"iu/l": 1, "miu/ml": 1},
    "LH":            {"iu/l": 1, "miu/ml": 1},
    "TSH":           {"uiu/ml": 1, "miu/l": 1},
    "Free T3":       {"pmol/l": 0.651},
    "Free T4":       {"pmol/l": 0.0777},
    "Cortisol":      {"nmol/l": 0.03625},
    "DHEA":          {"umol/l": 36.85},
    "Progesterone":  {"nmol/l": 0.3145},
    "Sodium":        {"mmol/l": 1},
    "Potassium":     {"mmol/l": 1},
    "Creatinine":    {"umol/l": 0.01131},
    "ALT":           {"iu/l": 1},
    "AST":           {"iu/l": 1},
    "Cholesterol":   {"mmol/l": 38.67},
    "HDL":           {"mmol/l": 38.67},
    "LDL":           {"mmol/l": 38.67},
    "Triglycerides": {"mmol/l": 88.57},
    "Vitamin D":     {"nmol/l": 0.4006},
}

# Names labs use for each marker (regex, case-insensitive).
# ORDER MATTERS: more specific names come first, e.g. "Hemoglobin A1c" must be
# checked before "Hemoglobin", and "Testosterone (Free)" before "Testosterone".
MARKER_ALIASES = [
    ("HbA1c",             r"hba1c|hemoglobin\s+a1c|haemoglobin\s+a1c|a1c|glycated\s+ha?emoglobin"),
    ("Hemoglobin",        r"ha?emoglobin|hgb|hb"),
    ("Hematocrit",        r"ha?ematocrit|hct"),
    ("Glucose",           r"(?:fasting\s+|blood\s+)?glucose"),
    ("WBC",               r"wbc|white\s+blood\s+cells?(?:\s+count)?|leukocytes"),
    ("RBC",               r"rbc|red\s+blood\s+cells?(?:\s+count)?|erythrocytes"),
    ("Platelets",         r"platelets?(?:\s+count)?|plt"),
    ("Free Testosterone", r"free\s+testosterone|testosterone\s*,?\s*\(?\s*free\s*\)?"),
    ("Testosterone",      r"(?:total\s+)?testosterone"),
    ("Estradiol",         r"o?estradiol|e2"),
    ("FSH",               r"fsh|follicle[\s-]+stimulating\s+hormone"),
    ("LH",                r"lh|luteini[sz]ing\s+hormone"),
    ("TSH",               r"tsh|thyroid[\s-]+stimulating\s+hormone"),
    ("Free T3",           r"free\s+t3|ft3|t3\s*,?\s*\(?\s*free\s*\)?"),
    ("Free T4",           r"free\s+t4|ft4|t4\s*,?\s*\(?\s*free\s*\)?"),
    ("Cortisol",          r"cortisol"),
    ("DHEA",              r"dhea(?:[\s-]*s(?:o4)?)?|dehydroepiandrosterone(?:\s+sulfate)?"),
    ("Progesterone",      r"progesterone"),
    ("Sodium",            r"sodium|na"),
    ("Potassium",         r"potassium"),
    ("Creatinine",        r"creatinine"),
    ("ALT",               r"alt|sgpt|alanine\s+aminotransferase"),
    ("AST",               r"ast|sgot|aspartate\s+aminotransferase"),
    ("HDL",               r"hdl(?:[\s-]+(?:cholesterol|c))?"),
    ("LDL",               r"ldl(?:[\s-]+(?:cholesterol|c))?"),
    ("Cholesterol",       r"(?:total\s+)?cholesterol(?:\s*,\s*total)?"),
    ("Triglycerides",     r"triglycerides?|tg"),
    ("Vitamin D",         r"(?:25[\s-]*(?:oh|hydroxy)\s+)?vitamin\s+d3?(?:\s*,?\s*25[\s-]*(?:oh|hydroxy))?"),
]

# Extra words after the name like "(Fasting)", "(E2)" or "Total" — skipped over.
_QUALIFIER = r"(?:\s*\([^)]*\)|\s*,?\s+[A-Za-z][A-Za-z-]*)*?"
# A number such as 95, 5.9, 1,200 or <0.5
_NUMBER = r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?"
# A unit such as mg/dL, %, K/uL, 10^3/uL or µg/dL (must not start with a plain number)
_UNIT = r"10\^\d+/[A-Za-zµμ]+|[A-Za-zµμ%][\w/%^.µμ]*"
# A reference range such as "70 - 100", "< 5.7" or "> 40"
_RANGE = rf"(?P<lo>{_NUMBER})\s*[-–]\s*(?P<hi>{_NUMBER})|(?P<cmp>[<>≤≥]=?)\s*(?P<lim>{_NUMBER})"

_LINE_PATTERNS = [
    (marker, re.compile(
        rf"^\s*(?:{aliases})(?![\w-]){_QUALIFIER}\s*[:=]?\s+"
        rf"[<>]?\s*(?P<value>{_NUMBER})(?![\d/])"
        rf"(?:\s*(?P<unit>{_UNIT}))?"
        rf"(?:\s+(?:{_RANGE}))?",
        re.IGNORECASE,
    ))
    for marker, aliases in MARKER_ALIASES
]

_NAME_PATTERNS = [
    (marker, re.compile(rf"^\s*(?:{aliases})(?![\w-]){_QUALIFIER}\s*$", re.IGNORECASE))
    for marker, aliases in MARKER_ALIASES
]


def canonical_marker(name):
    """
    Turns any lab's name for a test into our standard marker name.
    e.g. "LDL Cholesterol" -> "LDL", "Estradiol (E2)" -> "Estradiol", "DHEA-S" -> "DHEA"
    Unknown names are returned unchanged.
    """
    for marker, pattern in _NAME_PATTERNS:
        if pattern.match(name or ""):
            return marker
    return name


def _to_float(number_text):
    return float(number_text.replace(",", ""))


def _parse_range(match):
    """Reads the reference range printed in the report, if any. Returns (low, high) or None."""
    if match.group("lo"):
        return _to_float(match.group("lo")), _to_float(match.group("hi"))
    if match.group("cmp"):
        limit = _to_float(match.group("lim"))
        return (None, limit) if match.group("cmp").startswith(("<", "≤")) else (limit, None)
    return None


def _format_range(low, high):
    if low is None:
        return f"< {high:g}"
    if high is None:
        return f"> {low:g}"
    return f"{low:g} - {high:g}"


def _normalize_unit(unit):
    """"µg/dL", "mcg/dL" and "ug/dl" all become "ug/dl"."""
    unit = unit.strip().lower().replace("µ", "u").replace("μ", "u")
    return unit.replace("mcg", "ug").replace("×", "x")


def _sig(number):
    """Rounds to 3 significant figures, e.g. 10.4021 -> 10.4"""
    return float(f"{number:.3g}")


def default_range(marker, unit="", sex=None):
    """
    Returns our built-in (low, high) range for a marker, in the report's own unit,
    or None if we don't have a safe default for it.
    sex = "Male", "Female" or None (unknown — uses the general defaults)
    """
    ranges = REFERENCE_RANGES
    if sex == "Female":
        ranges = {**REFERENCE_RANGES, **FEMALE_REFERENCE_RANGES}

    ref = ranges.get(marker)
    if ref is None:
        return None

    # No unit printed, or the same unit as our defaults: use the range as it is
    if not unit or _normalize_unit(unit) == _normalize_unit(DEFAULT_UNITS.get(marker, "")):
        return ref

    # A different unit we know how to convert, e.g. mmol/L glucose
    factor = UNIT_CONVERSIONS.get(marker, {}).get(_normalize_unit(unit))
    if factor is None:
        return None  # unknown unit — comparing would give a wrong answer

    return tuple(None if limit is None else _sig(limit / factor) for limit in ref)


def parse_blood_values(text, sex=None):
    """
    Finds blood values in PDF text, one test per line.
    Uses the report's own reference range when it prints one,
    otherwise falls back to our built-in ranges (adjusted for sex and units).
    sex = "Male", "Female" or None
    """
    results = {}

    for line in text.splitlines():
        for marker, pattern in _LINE_PATTERNS:
            match = pattern.match(line)
            if not match:
                continue

            # Only the first line for each marker counts (reports may repeat a test)
            if marker not in results:
                value        = _to_float(match.group("value"))
                unit         = match.group("unit") or ""
                report_range = _parse_range(match)
                ref          = report_range or default_range(marker, unit, sex)

                # Calculate status using reference ranges
                if ref is None:
                    status, ref_text, source = "Unknown", "N/A", "none"
                else:
                    low, high = ref
                    if low is not None and value < low:
                        status = "Low"
                    elif high is not None and value > high:
                        status = "High"
                    else:
                        status = "Normal"
                    ref_text = _format_range(low, high)
                    source   = "report" if report_range else "default"

                results[marker] = {
                    "value":      value,
                    "unit":       unit,
                    "status":     status,
                    "ref_range":  ref_text,
                    "ref_source": source,
                }
            break  # a line belongs to one marker only

    return results


def extract_patient_info(text):
    """
    Tries to find basic patient info like name, date, age.
    Blood reports usually have this at the top.
    """
    info = {}

    # Look for a date pattern like 01/15/2024 or 2024-01-15
    date_match = re.search(r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b', text)
    if date_match:
        info["report_date"] = date_match.group(1)

    # Look for age pattern like "Age: 45" or "45 years"
    age_match = re.search(r'Age[:\s]+(\d+)', text, re.IGNORECASE)
    if age_match:
        info["age"] = int(age_match.group(1))

    # Look for "Gender: Male", "Sex: F" etc.
    sex_match = re.search(r'\b(?:Gender|Sex)\s*[:\-]?\s*(Male|Female|M|F)\b', text, re.IGNORECASE)
    if sex_match:
        info["sex"] = "Female" if sex_match.group(1).lower().startswith("f") else "Male"

    return info


def process_blood_report(pdf_path, sex=None):
    """
    MAIN FUNCTION - call this to process a blood report PDF.
    It runs all the steps above and returns everything together.
    sex = "Male" / "Female" to override what's printed on the report (None = use the report)
    """
    logger.info("📄 Reading PDF: %s", getattr(pdf_path, "name", pdf_path))

    # Step 1: get raw text from PDF
    raw_text = extract_text_from_pdf(pdf_path)
    logger.info("✅ Extracted %d characters of text", len(raw_text))

    # Step 2: find patient info (sex changes some reference ranges)
    patient_info = extract_patient_info(raw_text)
    if sex:
        patient_info["sex"] = sex

    # Step 3: find blood values in the text
    blood_values = parse_blood_values(raw_text, sex=patient_info.get("sex"))
    logger.info("✅ Found %d blood markers", len(blood_values))

    return {
        "patient_info":  patient_info,
        "blood_values":  blood_values,
        "raw_text":      raw_text  # we'll send this to AI in Phase 2
    }


# ---- TEST IT ----
# Run this file directly to test it: python pdf_extractor.py
if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if len(sys.argv) < 2:
        print("Usage: python pdf_extractor.py path/to/report.pdf")
    else:
        result = process_blood_report(sys.argv[1])
        print("\n📊 EXTRACTED VALUES:")
        for marker, data in result["blood_values"].items():
            print(f"  {marker}: {data['value']} {data['unit']} [{data['status']}]")
