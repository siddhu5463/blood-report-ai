# main.py — all phases connected, in the terminal

import argparse
import logging

from pdf_extractor        import process_blood_report
from ai_analyzer          import analyze_blood_report, print_analysis
from medicine_db          import load_medicines, get_medicine_suggestions, print_suggestions
from prescription_checker import check_prescription, print_prescription_check


def run_pipeline(file_path, prescription=None, sex=None):
    """
    Runs the full pipeline: PDF → Extract → AI Analyze → Medicine Match → Prescription Check
    prescription = list of medicine names the doctor prescribed (Phase 4 is skipped if None)
    sex          = "Male" / "Female" to override what's printed on the report
    Returns True if every phase ran, False if it had to stop early.
    """

    # ── Phase 1: Extract blood values from PDF
    print("\n📌 PHASE 1: Extracting blood values...")
    extracted = process_blood_report(file_path, sex=sex)
    blood_values = extracted["blood_values"]
    if not blood_values:
        print("❌ Could not extract blood values. Please check your PDF format.")
        return False

    for marker, data in blood_values.items():
        print(f"  {marker:<18} {data['value']:>8g} {data['unit']:<8} [{data['status']}]  ref: {data['ref_range']}")

    # ── Phase 2: AI analysis with Gemini
    print("\n📌 PHASE 2: AI Analysis...")
    analysis = analyze_blood_report(blood_values, extracted["patient_info"])
    print_analysis(analysis)
    if "error" in analysis:
        return False  # Phases 3 and 4 need the AI's flagged values

    # ── Phase 3: Medicine suggestions from internal database
    print("\n📌 PHASE 3: Medicine Matching...")
    medicines    = load_medicines()
    flagged      = analysis.get("flagged_values", [])
    suggestions  = get_medicine_suggestions(flagged, medicines)
    print_suggestions(suggestions)

    # ── Phase 4: Compare against the doctor's prescription (optional)
    if prescription:
        print("\n📌 PHASE 4: Prescription Check...")
        print_prescription_check(check_prescription(prescription, suggestions))

    return True


if __name__ == "__main__":
    import sys

    parser = argparse.ArgumentParser(description="Analyse a blood report PDF in the terminal.")
    parser.add_argument("report", help="path to the blood report PDF")
    parser.add_argument("--rx", help='doctor\'s prescription, comma-separated, e.g. "Anastrozole, Metformin 500mg"')
    parser.add_argument("--sex", choices=["Male", "Female"], help="override the sex printed on the report")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    prescription = [name.strip() for name in args.rx.split(",")] if args.rx else None
    ok = run_pipeline(args.report, prescription, args.sex)
    sys.exit(0 if ok else 1)
