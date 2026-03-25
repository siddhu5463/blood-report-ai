# ai_analyzer.py (updated to use new google-genai library)

from google import genai          # new library name
from google.genai import types
import os
import json
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()

# Setup client with new library
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Updated model name (gemini-1.5-flash is deprecated, use this instead)
MODEL = "gemini-2.5-flash-lite"   # 1000 free requests/day - most generous free model


def build_prompt(blood_values, patient_info=None):
    """
    Builds the instruction we send to Gemini.
    The better our prompt, the better the AI response.
    """
    values_text = ""
    for test, data in blood_values.items():
        ref = data.get("ref_range", "N/A")
        values_text += f"  - {test}: {data['value']} {data['unit']} (Status: {data['status']}, Reference: {ref})\n"

    prompt = f"""
You are a medical data analyst assistant for an HRT (Hormone Replacement Therapy) clinic.
Your job is to review blood test results and provide a structured analysis.

IMPORTANT RULES:
1. You are NOT a doctor. Never give a diagnosis.
2. Only flag issues - do not prescribe treatment.
3. If you see something outside HRT scope (e.g. cancer markers, heart disease),
   mark it as "REFER TO SPECIALIST" immediately.
4. Keep language simple and clear.

PATIENT BLOOD TEST RESULTS:
{values_text}

Please respond ONLY with a valid JSON object in this exact format:
{{
  "summary": "2-3 sentence plain English overview of the results",
  "flagged_values": [
    {{
      "test": "test name",
      "value": "the value with unit",
      "issue": "High or Low",
      "explanation": "simple explanation of what this means",
      "within_hrt_scope": true or false,
      "action": "Monitor / Refer to Specialist / Adjust Treatment"
    }}
  ],
  "within_scope_count": number of issues within HRT scope,
  "refer_to_specialist": true or false,
  "referral_reason": "reason if refer_to_specialist is true, else empty string",
  "overall_status": "Good / Needs Attention / Urgent"
}}

Only include tests that are flagged High or Low in flagged_values.
If all values are normal return an empty array for flagged_values.
Return ONLY the JSON object. No extra text, no markdown, no code blocks.
"""
    return prompt


def analyze_blood_report(blood_values, patient_info=None):
    """
    Sends blood values to Gemini and returns structured analysis.
    """
    print("🤖 Sending blood values to Gemini AI...")

    prompt = build_prompt(blood_values, patient_info)

    try:
        # New way to call Gemini with updated library
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,   # low temperature = more consistent/factual responses
                max_output_tokens=1500,
            )
        )

        raw_response = response.text
        print("✅ Got response from Gemini!")

        # Clean up response in case AI adds ```json blocks anyway
        cleaned = raw_response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        cleaned = cleaned.strip()

        # Parse JSON
        analysis = json.loads(cleaned)
        return analysis

    except json.JSONDecodeError:
        print("⚠️  AI response was not valid JSON, returning raw text")
        return {"raw_response": raw_response, "error": "Could not parse JSON"}

    except Exception as e:
        print(f"❌ Error calling Gemini API: {e}")
        return {"error": str(e)}


def print_analysis(analysis):
    """
    Prints the AI analysis in a readable terminal format.
    """
    if "error" in analysis:
        print(f"❌ Error: {analysis['error']}")
        return

    print("\n" + "="*60)
    print("🧠 AI BLOOD REPORT ANALYSIS")
    print("="*60)

    status = analysis.get("overall_status", "Unknown")
    status_emoji = {"Good": "✅", "Needs Attention": "⚠️", "Urgent": "🚨"}.get(status, "❓")
    print(f"\n{status_emoji} Overall Status: {status}")

    print(f"\n📋 Summary:\n   {analysis.get('summary', 'N/A')}")

    flagged = analysis.get("flagged_values", [])
    if flagged:
        print(f"\n🚩 Flagged Values ({len(flagged)} issues found):")
        for item in flagged:
            scope = "✅ HRT Scope" if item.get("within_hrt_scope") else "⛔ Outside Scope"
            print(f"""
   Test:        {item.get('test')}
   Value:       {item.get('value')}
   Issue:       {item.get('issue')}
   Explanation: {item.get('explanation')}
   Scope:       {scope}
   Action:      {item.get('action')}
   {'-'*40}""")
    else:
        print("\n✅ No flagged values — all results look normal!")

    if analysis.get("refer_to_specialist"):
        print(f"\n🏥 REFER TO SPECIALIST: {analysis.get('referral_reason')}")

    print("="*60 + "\n")


# ---- TEST ----
if __name__ == "__main__":
    test_blood_values = {
        "Glucose":         {"value": 112,  "unit": "mg/dL", "status": "High",   "ref_range": "70 - 100"},
        "Testosterone":    {"value": 312,  "unit": "ng/dL", "status": "Normal", "ref_range": "300 - 1000"},
        "Estradiol":       {"value": 42,   "unit": "pg/mL", "status": "High",   "ref_range": "10 - 40"},
        "DHEA":            {"value": 82,   "unit": "ug/dL", "status": "Low",    "ref_range": "110 - 510"},
        "TSH":             {"value": 3.8,  "unit": "mIU/L", "status": "Normal", "ref_range": "0.4 - 4.0"},
        "LDL Cholesterol": {"value": 138,  "unit": "mg/dL", "status": "High",   "ref_range": "0 - 100"},
        "Triglycerides":   {"value": 178,  "unit": "mg/dL", "status": "High",   "ref_range": "0 - 150"},
        "HbA1c":           {"value": 5.9,  "unit": "%",     "status": "High",   "ref_range": "0 - 5.7"},
    }

    analysis = analyze_blood_report(test_blood_values)
    print_analysis(analysis)