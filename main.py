# main.py — Phase 1 + Phase 2 + Phase 3 connected

from pdf_extractor  import process_blood_report
from ai_analyzer    import analyze_blood_report, print_analysis
from medicine_db    import load_medicines, get_medicine_suggestions, print_suggestions


def run_pipeline(file_path):
    """Runs the full pipeline: PDF → Extract → AI Analyze → Medicine Match"""

    # ── Phase 1: Extract blood values from PDF
    print("\n📌 PHASE 1: Extracting blood values...")
    extracted = process_blood_report(file_path)
    if not extracted:
        return

    # ── Phase 2: AI analysis with Gemini
    print("\n📌 PHASE 2: AI Analysis...")
    analysis = analyze_blood_report(extracted["blood_values"])
    print_analysis(analysis)

    # ── Phase 3: Medicine suggestions from internal database
    print("\n📌 PHASE 3: Medicine Matching...")
    medicines    = load_medicines()
    flagged      = analysis.get("flagged_values", [])
    suggestions  = get_medicine_suggestions(flagged, medicines)
    print_suggestions(suggestions)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python main.py your_report.pdf")
    else:
        run_pipeline(sys.argv[1])