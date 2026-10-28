# medicine_db.py
# WHAT THIS FILE DOES:
# Loads our internal medicine list from medicines.json
# Matches flagged blood values to appropriate medicines
# ONLY suggests medicines from our internal list - nothing external

import json
import logging
import os

from pdf_extractor import canonical_marker

logger = logging.getLogger(__name__)

# Look for medicines.json next to this file, so it works from any folder
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "medicines.json")


def normalize_direction(issue):
    """Turns the AI's wording ("High", "elevated", "Low (borderline)") into "High" / "Low"."""
    issue = (issue or "").strip().lower()
    if issue.startswith(("high", "elevated", "raised")):
        return "High"
    if issue.startswith(("low", "decreased", "reduced")):
        return "Low"
    return issue.title()


def load_medicines(json_path=DEFAULT_DB_PATH):
    """
    Loads the medicine database from our JSON file.
    Returns a list of medicine dictionaries.
    """
    if not os.path.exists(json_path):
        logger.error("❌ medicines.json not found at %s", json_path)
        return []

    with open(json_path, "r") as f:
        medicines = json.load(f)

    logger.info("✅ Loaded %d medicines from database", len(medicines))
    return medicines


def find_medicines_for_flag(test_name, direction, medicines):
    """
    Finds medicines that treat a specific flagged blood value.

    test_name = the blood test name  e.g. "Estradiol" or "LDL Cholesterol"
    direction = "High" or "Low"
    medicines = the full list loaded from medicines.json

    Returns list of matching medicines
    """
    marker    = canonical_marker(test_name)
    direction = normalize_direction(direction)
    matches   = []

    for med in medicines:
        # Products marked outside HRT scope are kept in the database but never suggested
        if not med.get("within_hrt_scope", True):
            continue

        # "targets" maps each marker to the direction this medicine treats,
        # e.g. Levothyroxine: {"TSH": "High", "Free T4": "Low"}
        if med["targets"].get(marker) == direction:
            matches.append(med)

    return matches


def get_medicine_suggestions(flagged_values, medicines):
    """
    MAIN FUNCTION - goes through all flagged blood values
    and finds matching medicines for each one.

    flagged_values = list of flagged items from AI analysis
    medicines      = full medicine list from load_medicines()

    Returns a structured suggestion report
    """
    suggestions = []

    for flag in flagged_values:
        test_name = flag.get("test", "")
        direction = normalize_direction(flag.get("issue", ""))   # "High" or "Low"
        in_scope  = flag.get("within_hrt_scope", True)

        # If outside HRT scope, don't suggest medicine - refer to specialist
        if not in_scope:
            suggestions.append({
                "test":        test_name,
                "issue":       direction,
                "medicines":   [],
                "action":      "REFER TO SPECIALIST",
                "note":        "This issue is outside our clinic scope. Please refer to a specialist."
            })
            continue

        # Find matching medicines from our internal database only
        matched = find_medicines_for_flag(test_name, direction, medicines)

        if matched:
            suggestions.append({
                "test":      test_name,
                "issue":     direction,
                "medicines": matched,
                "action":    "Medicine found in database",
                "note":      f"Found {len(matched)} option(s) in our product list"
            })
        else:
            suggestions.append({
                "test":      test_name,
                "issue":     direction,
                "medicines": [],
                "action":    "No match in database",
                "note":      "No medicine in our current product list for this. Consider adding one."
            })

    return suggestions


def print_suggestions(suggestions):
    """
    Prints medicine suggestions in a readable terminal format.
    """
    print("\n" + "="*60)
    print("💊 MEDICINE SUGGESTIONS (Internal Database Only)")
    print("="*60)

    for item in suggestions:
        print(f"\n🔬 Test: {item['test']} — {item['issue']}")
        print(f"   Action: {item['action']}")

        if item["medicines"]:
            for med in item["medicines"]:
                print(f"""
   ✅ {med['name']} ({med['type']})
      Dosage : {med['dosage']}
      Notes  : {med['notes']}""")
        else:
            print(f"   ⚠️  {item['note']}")

        print("   " + "-"*40)

    print("="*60)
    print("⚕️  REMINDER: Doctor has final authority on all prescriptions.")
    print("="*60 + "\n")


# ---- TEST ----
if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    # Load medicines from JSON file
    medicines = load_medicines()

    # Sample flagged values (same format as AI analyzer output)
    sample_flagged = [
        {"test": "Estradiol",       "issue": "High", "within_hrt_scope": True},
        {"test": "DHEA",            "issue": "Low",  "within_hrt_scope": True},
        {"test": "Triglycerides",   "issue": "High", "within_hrt_scope": True},
        {"test": "HbA1c",           "issue": "High", "within_hrt_scope": True},
        {"test": "LDL Cholesterol", "issue": "High", "within_hrt_scope": False},  # outside scope test
    ]

    suggestions = get_medicine_suggestions(sample_flagged, medicines)
    print_suggestions(suggestions)