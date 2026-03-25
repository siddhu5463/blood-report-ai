# generate_sample_report.py
# WHAT THIS DOES:
# Creates a realistic fake blood report PDF for testing.
# All values are made up - safe to use for learning.

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import random

def generate_blood_report(filename="sample_blood_report.pdf"):
    """Creates a realistic-looking blood report PDF"""

    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []  # list of elements to add to the PDF

    # ---- HEADER ----
    title = Paragraph("<b>COMPREHENSIVE BLOOD PANEL REPORT</b>", styles["Title"])
    story.append(title)
    story.append(Spacer(1, 0.2 * inch))

    # ---- PATIENT INFO ----
    patient_info = [
        ["Patient Name:", "John Doe",         "Report Date:", "03/15/2024"],
        ["Date of Birth:", "05/22/1978",       "Age:",         "45 years"],
        ["Patient ID:",    "PT-00123",          "Gender:",      "Male"],
        ["Ordering Physician:", "Dr. Smith",   "Lab ID:",      "LAB-2024-0315"],
    ]

    patient_table = Table(patient_info, colWidths=[1.5*inch, 2*inch, 1.5*inch, 2*inch])
    patient_table.setStyle(TableStyle([
        ("FONTSIZE",    (0,0), (-1,-1), 10),
        ("FONTNAME",    (0,0), (0,-1), "Helvetica-Bold"),  # bold label column
        ("FONTNAME",    (2,0), (2,-1), "Helvetica-Bold"),  # bold label column
        ("BOTTOMPADDING",(0,0),(-1,-1), 4),
    ]))
    story.append(patient_table)
    story.append(Spacer(1, 0.3 * inch))

    # ---- SECTION TITLE ----
    story.append(Paragraph("<b>LABORATORY RESULTS</b>", styles["Heading2"]))
    story.append(Spacer(1, 0.1 * inch))

    # ---- BLOOD VALUES TABLE ----
    # Format: [Test Name, Result, Unit, Reference Range, Status]
    blood_data = [
        # Header row
        ["TEST NAME", "RESULT", "UNIT", "REFERENCE RANGE", "STATUS"],

        # Hormones (HRT clinic focus)
        ["Testosterone (Total)",  "312",   "ng/dL",   "300 - 1000",   "Normal"],
        ["Testosterone (Free)",   "6.2",   "ng/dL",   "5.0 - 21.0",   "Normal"],
        ["Estradiol (E2)",        "42",    "pg/mL",   "10 - 40",      "High"],
        ["FSH",                   "3.1",   "mIU/mL",  "1.5 - 12.4",   "Normal"],
        ["LH",                    "4.8",   "mIU/mL",  "1.7 - 8.6",    "Normal"],
        ["DHEA-S",                "82",    "ug/dL",   "110 - 510",    "Low"],
        ["Progesterone",          "0.4",   "ng/mL",   "0.3 - 1.2",    "Normal"],
        ["Cortisol (AM)",         "22",    "ug/dL",   "6 - 23",       "Normal"],

        # Thyroid
        ["TSH",                   "3.8",   "mIU/L",   "0.4 - 4.0",    "Normal"],
        ["Free T3",               "2.6",   "pg/mL",   "2.3 - 4.2",    "Normal"],
        ["Free T4",               "0.9",   "ng/dL",   "0.8 - 1.8",    "Normal"],

        # Metabolic Panel
        ["Glucose (Fasting)",     "112",   "mg/dL",   "70 - 100",     "High"],
        ["HbA1c",                 "5.9",   "%",        "< 5.7",        "High"],
        ["Creatinine",            "1.1",   "mg/dL",   "0.7 - 1.3",    "Normal"],
        ["Sodium",                "139",   "mEq/L",   "136 - 145",    "Normal"],
        ["Potassium",             "4.1",   "mEq/L",   "3.5 - 5.1",    "Normal"],
        ["ALT",                   "38",    "U/L",      "7 - 40",       "Normal"],
        ["AST",                   "42",    "U/L",      "10 - 40",      "High"],

        # Lipids
        ["Total Cholesterol",     "215",   "mg/dL",   "< 200",        "High"],
        ["HDL Cholesterol",       "48",    "mg/dL",   "> 40",         "Normal"],
        ["LDL Cholesterol",       "138",   "mg/dL",   "< 100",        "High"],
        ["Triglycerides",         "178",   "mg/dL",   "< 150",        "High"],

        # CBC
        ["Hemoglobin",            "14.8",  "g/dL",    "13.5 - 17.5",  "Normal"],
        ["Hematocrit",            "44",    "%",        "41 - 53",      "Normal"],
        ["WBC",                   "7.2",   "K/uL",    "4.5 - 11.0",   "Normal"],
        ["RBC",                   "4.9",   "M/uL",    "4.5 - 5.9",    "Normal"],
        ["Platelets",             "220",   "K/uL",    "150 - 400",    "Normal"],
    ]

    # Create the table
    col_widths = [2.2*inch, 0.9*inch, 0.8*inch, 1.6*inch, 0.9*inch]
    blood_table = Table(blood_data, colWidths=col_widths)

    blood_table.setStyle(TableStyle([
        # Header row styling
        ("BACKGROUND",   (0,0), (-1,0),  colors.HexColor("#2C3E50")),
        ("TEXTCOLOR",    (0,0), (-1,0),  colors.white),
        ("FONTNAME",     (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,0),  9),
        ("ALIGN",        (0,0), (-1,0),  "CENTER"),

        # Data rows
        ("FONTSIZE",     (0,1), (-1,-1), 9),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [colors.white, colors.HexColor("#F8F9FA")]),
        ("BOTTOMPADDING",(0,0), (-1,-1), 5),
        ("TOPPADDING",   (0,0), (-1,-1), 5),
        ("GRID",         (0,0), (-1,-1), 0.5, colors.HexColor("#DEE2E6")),

        # Highlight HIGH values in red
        ("TEXTCOLOR",    (4,2),  (4,2),  colors.red),   # Estradiol High
        ("TEXTCOLOR",    (4,4),  (4,4),  colors.red),   # DHEA Low  
        ("TEXTCOLOR",    (4,12), (4,12), colors.red),   # Glucose High
        ("TEXTCOLOR",    (4,13), (4,13), colors.red),   # HbA1c High
        ("TEXTCOLOR",    (4,18), (4,18), colors.red),   # Cholesterol High
        ("TEXTCOLOR",    (4,20), (4,20), colors.red),   # LDL High
        ("TEXTCOLOR",    (4,21), (4,21), colors.red),   # Triglycerides High
        ("FONTNAME",     (4,2),  (4,2),  "Helvetica-Bold"),
        ("FONTNAME",     (4,12), (4,12), "Helvetica-Bold"),
    ]))

    story.append(blood_table)
    story.append(Spacer(1, 0.3 * inch))

    # ---- FOOTER NOTE ----
    note = Paragraph(
        "<i>* This report is generated for educational/testing purposes only. "
        "All values are fictional. Not for medical use.</i>",
        styles["Normal"]
    )
    story.append(note)

    # ---- BUILD THE PDF ----
    doc.build(story)
    print(f"✅ Sample blood report created: {filename}")
    print(f"   Open it to see what it looks like!")


# Run it
if __name__ == "__main__":
    generate_blood_report()