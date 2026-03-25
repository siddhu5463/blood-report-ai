# prescription_checker.py
# WHAT THIS FILE DOES:
# Doctor enters their prescription
# We compare it against what AI suggested
# Show a match score and highlight mismatches
# Doctor ALWAYS has final authority - this is just a review tool

def check_prescription(doctor_prescription, ai_suggestions):
    """
    Compares doctor's prescription against AI medicine suggestions.

    doctor_prescription = list of medicine names doctor prescribed
                          e.g. ["Anastrozole", "Metformin", "Omega-3 Fish Oil"]

    ai_suggestions      = output from medicine_db.get_medicine_suggestions()

    Returns a detailed match report
    """

    # Collect all AI suggested medicine names into a flat list
    ai_medicines = []
    for suggestion in ai_suggestions:
        for med in suggestion.get("medicines", []):
            ai_medicines.append({
                "name":  med["name"],
                "test":  suggestion["test"],
                "issue": suggestion["issue"]
            })

    ai_medicine_names = [m["name"].lower() for m in ai_medicines]
    doctor_lower      = [d.lower().strip() for d in doctor_prescription]

    matched    = []   # doctor prescribed AND AI suggested
    extra      = []   # doctor prescribed but AI did NOT suggest
    missed     = []   # AI suggested but doctor did NOT prescribe

    # Check each doctor prescription
    for med in doctor_prescription:
        if med.lower().strip() in ai_medicine_names:
            # Find which test this medicine was for
            for ai_med in ai_medicines:
                if ai_med["name"].lower() == med.lower().strip():
                    matched.append({
                        "medicine": med,
                        "test":     ai_med["test"],
                        "issue":    ai_med["issue"]
                    })
                    break
        else:
            extra.append(med)

    # Check what AI suggested that doctor didn't prescribe
    for ai_med in ai_medicines:
        if ai_med["name"].lower() not in doctor_lower:
            missed.append(ai_med)

    # Calculate match score (0-100)
    total_ai = len(ai_medicines)
    if total_ai == 0:
        match_score = 100  # no suggestions = nothing to match
    else:
        match_score = round((len(matched) / total_ai) * 100)

    return {
        "match_score":         match_score,
        "matched":             matched,
        "extra_prescriptions": extra,    # doctor added these (not in AI list)
        "missed_suggestions":  missed,   # AI suggested but doctor skipped
        "total_ai_suggested":  total_ai,
        "total_prescribed":    len(doctor_prescription),
    }


def print_prescription_check(report):
    """Prints the prescription check report in terminal"""

    print("\n" + "="*60)
    print("📋 PRESCRIPTION MATCH REPORT")
    print("="*60)

    # Match score with visual bar
    score = report["match_score"]
    filled = int(score / 10)
    bar    = "█" * filled + "░" * (10 - filled)
    emoji  = "✅" if score >= 80 else "⚠️" if score >= 50 else "🚨"
    print(f"\n{emoji} Match Score: {score}/100  [{bar}]")

    # Matched medicines
    if report["matched"]:
        print(f"\n✅ Matched ({len(report['matched'])}) — AI agrees with doctor:")
        for m in report["matched"]:
            print(f"   • {m['medicine']}  →  for {m['test']} ({m['issue']})")

    # Extra prescriptions (doctor added something AI didn't suggest)
    if report["extra_prescriptions"]:
        print(f"\n➕ Extra Prescriptions ({len(report['extra_prescriptions'])}) — not in AI suggestions:")
        for m in report["extra_prescriptions"]:
            print(f"   • {m}  ← Doctor added this (review recommended)")

    # Missed suggestions (AI suggested but doctor didn't prescribe)
    if report["missed_suggestions"]:
        print(f"\n⚠️  Missed Suggestions ({len(report['missed_suggestions'])}) — AI suggested but not prescribed:")
        for m in report["missed_suggestions"]:
            print(f"   • {m['name']}  →  for {m['test']} ({m['issue']})")

    print(f"\n📊 Summary:")
    print(f"   AI suggested    : {report['total_ai_suggested']} medicines")
    print(f"   Doctor prescribed: {report['total_prescribed']} medicines")
    print(f"\n⚕️  REMINDER: Doctor has final authority. AI is advisory only.")
    print("="*60 + "\n")


# ---- TEST ----
if __name__ == "__main__":
    from medicine_db import load_medicines, get_medicine_suggestions

    medicines = load_medicines()

    sample_flagged = [
        {"test": "Estradiol",     "issue": "High", "within_hrt_scope": True},
        {"test": "Glucose",       "issue": "High", "within_hrt_scope": True},
        {"test": "Triglycerides", "issue": "High", "within_hrt_scope": True},
        {"test": "HbA1c",         "issue": "High", "within_hrt_scope": True},
    ]

    suggestions = get_medicine_suggestions(sample_flagged, medicines)

    # Simulate a doctor's prescription (some match, some don't)
    doctor_prescription = [
        "Anastrozole",      # ✅ matches AI suggestion
        "Metformin",        # ✅ matches AI suggestion
        "Aspirin",          # ➕ doctor added this - not in AI list
    ]

    report = check_prescription(doctor_prescription, suggestions)
    print_prescription_check(report)