# pdf_extractor.py
# WHAT THIS FILE DOES:
# Reads a blood report PDF and pulls out all the lab values
# Example output: {"Glucose": {"value": 95, "unit": "mg/dL", "status": "Normal"}}

import pdfplumber  # reads PDF files
import re          # helps us find patterns in text (like "Glucose: 95")


def extract_text_from_pdf(pdf_path):
    """
    Opens a PDF file and reads all the text from every page.
    pdf_path = the location of the PDF on your computer
    """
    full_text = ""  # we'll collect all text here

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:          # loop through every page
            text = page.extract_text()  # pull text from this page
            if text:                    # only add if page has text
                full_text += text + "\n"

    return full_text


# Default reference ranges, used only when the report doesn't print its own.
# Format: "Marker": (min_normal, max_normal) — None means "no limit on that side".
# A marker with no default range is only reported when the PDF gives a range.
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


def parse_blood_values(text):
    """
    Finds blood values in PDF text, one test per line.
    Uses the report's own reference range when it prints one,
    otherwise falls back to our built-in REFERENCE_RANGES.
    """
    results = {}

    for line in text.splitlines():
        for marker, pattern in _LINE_PATTERNS:
            match = pattern.match(line)
            if not match:
                continue

            # Only the first line for each marker counts (reports may repeat a test)
            if marker not in results:
                report_range = _parse_range(match)
                ref = report_range or REFERENCE_RANGES.get(marker)
                if ref is not None:
                    value     = _to_float(match.group("value"))
                    low, high = ref

                    # Calculate status using reference ranges
                    if low is not None and value < low:
                        status = "Low"
                    elif high is not None and value > high:
                        status = "High"
                    else:
                        status = "Normal"

                    results[marker] = {
                        "value":      value,
                        "unit":       match.group("unit") or "",
                        "status":     status,
                        "ref_range":  _format_range(low, high),
                        "ref_source": "report" if report_range else "default",
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

    return info


def process_blood_report(pdf_path):
    """
    MAIN FUNCTION - call this to process a blood report PDF.
    It runs all the steps above and returns everything together.
    """
    print(f"📄 Reading PDF: {pdf_path}")

    # Step 1: get raw text from PDF
    raw_text = extract_text_from_pdf(pdf_path)
    print(f"✅ Extracted {len(raw_text)} characters of text")

    # Step 2: find blood values in the text
    blood_values = parse_blood_values(raw_text)
    print(f"✅ Found {len(blood_values)} blood markers")

    # Step 3: find patient info
    patient_info = extract_patient_info(raw_text)

    return {
        "patient_info":  patient_info,
        "blood_values":  blood_values,
        "raw_text":      raw_text  # we'll send this to AI in Phase 2
    }


# ---- TEST IT ----
# Run this file directly to test it: python pdf_extractor.py
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python pdf_extractor.py path/to/report.pdf")
    else:
        result = process_blood_report(sys.argv[1])
        print("\n📊 EXTRACTED VALUES:")
        for marker, data in result["blood_values"].items():
            print(f"  {marker}: {data['value']} {data['unit']} [{data['status']}]")
