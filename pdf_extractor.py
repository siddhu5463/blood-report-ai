# pdf_extractor.py
# WHAT THIS FILE DOES:
# Reads a blood report PDF and pulls out all the lab values
# Example output: {"Glucose": {"value": 95, "unit": "mg/dL", "status": "normal"}}

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


def parse_blood_values(text):
    """
    Finds blood values in PDF text using regex.
    Then calculates High/Low/Normal using built-in reference ranges.
    This way we don't depend on the PDF having a status column.
    """

    # Reference ranges for each marker
    # Format: "Marker": (min_normal, max_normal)
    reference_ranges = {
        "Glucose":       (70,   100),
        "Hemoglobin":    (13.5, 17.5),
        "Hematocrit":    (41,   53),
        "WBC":           (4.5,  11.0),
        "RBC":           (4.5,  5.9),
        "Platelets":     (150,  400),
        "Testosterone":  (300,  1000),
        "Estradiol":     (10,   40),
        "FSH":           (1.5,  12.4),
        "LH":            (1.7,  8.6),
        "TSH":           (0.4,  4.0),
        "T3":            (2.3,  4.2),
        "T4":            (0.8,  1.8),
        "Cortisol":      (6,    23),
        "DHEA":          (110,  510),
        "Progesterone":  (0.3,  1.2),
        "Sodium":        (136,  145),
        "Potassium":     (3.5,  5.1),
        "Creatinine":    (0.7,  1.3),
        "ALT":           (7,    40),
        "AST":           (10,   40),
        "Cholesterol":   (0,    200),
        "HDL":           (40,   999),
        "LDL":           (0,    100),
        "Triglycerides": (0,    150),
        "HbA1c":         (0,    5.7),
    }

    results = {}

    markers = list(reference_ranges.keys())  # use keys as our marker list

    for marker in markers:
        # Regex finds: MarkerName followed by a number
        pattern = rf"{marker}[\w\s\(\)]*?\s+(\d+\.?\d*)\s*([a-zA-Z/%]+)"
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            value = float(match.group(1))
            unit  = match.group(2) or ""

            # Calculate status using reference ranges
            low, high = reference_ranges[marker]
            if value < low:
                status = "Low"
            elif value > high:
                status = "High"
            else:
                status = "Normal"

            results[marker] = {
                "value":  value,
                "unit":   unit,
                "status": status,
                "ref_range": f"{low} - {high}"  # store range too
            }

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