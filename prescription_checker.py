# prescription_checker.py
# WHAT THIS FILE DOES:
# Doctor enters their prescription
# We compare it against what AI suggested
# Show a match score and highlight mismatches
# Doctor ALWAYS has final authority - this is just a review tool

def _normalize(name):
    """Lowercase and collapse spaces, so "  Metformin " == "metformin"."""
    return " ".join(name.lower().split())


def _is_prescribed(medicine_name, prescription_line):
    """
    True if a prescription line names this medicine.
    Allows a dose after the name, e.g. "Metformin 500mg" matches "Metformin".
    """
    med  = _normalize(medicine_name)
    line = _normalize(prescription_line)
    return line == med or line.startswith(med + " ")


def check_prescription(doctor_prescription, ai_suggestions):
    """
    Compares doctor's prescription against AI medicine suggestions.

    doctor_prescription = list of medicine names doctor prescribed
                          e.g. ["Anastrozole", "Metformin 500mg", "Omega-3 Fish Oil"]

    ai_suggestions      = output from medicine_db.get_medicine_suggestions()

    The score is per flagged issue: an issue counts as covered when the doctor
    prescribed ANY of the options suggested for it. One medicine can cover
    several issues (Metformin covers High Glucose and High HbA1c), and the
    doctor is not penalised for picking one option out of several.

    Returns a detailed match report
    """

    # Remove blank and duplicate lines, keeping the doctor's order
    prescribed = []
    for line in doctor_prescription:
        if line.strip() and _normalize(line) not in [_normalize(p) for p in prescribed]:
            prescribed.append(line.strip())

    # Only issues that have at least one medicine option can be scored
    issues = [s for s in ai_suggestions if s.get("medicines")]

    matched    = []   # doctor prescribed AND AI suggested
    missed     = []   # issues where the doctor prescribed none of the AI options
    used_lines = set()

    for issue in issues:
        options = [med["name"] for med in issue["medicines"]]
        hits = [
            (line, name)
            for line in prescribed
            for name in options
            if _is_prescribed(name, line)
        ]
        if hits:
            for line, name in hits:
                used_lines.add(line)
                matched.append({
                    "medicine": name,
                    "test":     issue["test"],
                    "issue":    issue["issue"]
                })
        else:
            missed.append({
                "name":    " or ".join(options),
                "options": options,
                "test":    issue["test"],
                "issue":   issue["issue"]
            })

    # Doctor prescribed but AI did NOT suggest
    extra = [line for line in prescribed if line not in used_lines]

    # Calculate match score (0-100)
    if not issues:
        match_score = 100  # no suggestions = nothing to match
    else:
        match_score = round((len(issues) - len(missed)) / len(issues) * 100)

    unique_suggested = {med["name"] for issue in issues for med in issue["medicines"]}

    return {
        "match_score":         match_score,
        "matched":             matched,
        "extra_prescriptions": extra,    # doctor added these (not in AI list)
        "missed_suggestions":  missed,   # issues the doctor did not cover
        "total_issues":        len(issues),
        "covered_issues":      len(issues) - len(missed),
        "total_ai_suggested":  len(unique_suggested),
        "total_prescribed":    len(prescribed),
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
        print(f"\n⚠️  Not Covered ({len(report['missed_suggestions'])}) — no suggested option was prescribed:")
        for m in report["missed_suggestions"]:
            print(f"   • {m['name']}  →  for {m['test']} ({m['issue']})")

    print(f"\n📊 Summary:")
    print(f"   Issues covered  : {report['covered_issues']}/{report['total_issues']}")
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