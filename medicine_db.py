# medicine_db.py
# WHAT THIS FILE DOES:
# Loads our internal medicine list from medicines.json
# Matches flagged blood values to appropriate medicines
# ONLY suggests medicines from our internal list - nothing external

import json
import os


def load_medicines(json_path="medicines.json"):
    """
    Loads the medicine database from our JSON file.
    Returns a list of medicine dictionaries.
    """
    if not os.path.exists(json_path):
        print(f"❌ medicines.json not found at {json_path}")
        return []

    with open(json_path, "r") as f:
        medicines = json.load(f)

    print(f"✅ Loaded {len(medicines)} medicines from database")
    return medicines


def find_medicines_for_flag(test_name, direction, medicines):
    """
    Finds medicines that treat a specific flagged blood value.

    test_name = the blood test name  e.g. "Estradiol"
    direction = "High" or "Low"
    medicines = the full list loaded from medicines.json

    Returns list of matching medicines
    """
    matches = []

    for med in medicines:
        # Check if this medicine targets this test
        targets_match    = test_name.lower() in [t.lower() for t in med["targets"]]
        # Check if direction matches (High Estradiol needs a medicine for "High")
        direction_match  = med["direction"].lower() == direction.lower()

        if targets_match and direction_match:
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
        direction = flag.get("issue", "")   # "High" or "Low"
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