# ai_analyzer.py (updated to use new google-genai library)

from google import genai          # new library name
from google.genai import types
import json
import logging
import os
from typing import List, Literal

from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

# Reads GEMINI_API_KEY from a local .env file (if there is one).
# On Streamlit Cloud, app.py copies st.secrets into the environment instead.
load_dotenv()

_client = None


def get_client():
    """Creates the Gemini client the first time it's needed. Returns None if no API key is set."""
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return None
        _client = genai.Client(api_key=api_key)
    return _client


# Updated model name (gemini-1.5-flash is deprecated, use this instead)
MODEL = "gemini-2.5-flash-lite"   # 1000 free requests/day - most generous free model


# The exact shape we want back. Gemini is told to follow this schema,
# and we check the reply against it before the rest of the app uses it.
class FlaggedValue(BaseModel):
    test:             str   # name exactly as in our results, e.g. "Estradiol"
    value:            str   # value with unit, e.g. "42 pg/mL"
    issue:            Literal["High", "Low"]
    explanation:      str
    within_hrt_scope: bool
    action:           Literal["Monitor", "Refer to Specialist", "Adjust Treatment"]


class BloodAnalysis(BaseModel):
    summary:             str
    flagged_values:      List[FlaggedValue]
    within_scope_count:  int
    refer_to_specialist: bool
    referral_reason:     str
    overall_status:      Literal["Good", "Needs Attention", "Urgent"]


def build_prompt(blood_values, patient_info=None):
    """
    Builds the instruction we send to Gemini.
    The better our prompt, the better the AI response.
    """
    values_text = ""
    for test, data in blood_values.items():
        ref = data.get("ref_range", "N/A")
        values_text += f"  - {test}: {data['value']} {data['unit']} (Status: {data['status']}, Reference: {ref})\n"

    # Age and sex change what's normal for hormones, so tell the AI when we know them
    patient_info = patient_info or {}
    patient_text = ", ".join(
        part for part in (
            f"{patient_info['age']} years old" if patient_info.get("age") else "",
            patient_info.get("sex", ""),
        ) if part
    ) or "unknown"

    prompt = f"""
You are a medical data analyst assistant for an HRT (Hormone Replacement Therapy) clinic.
Your job is to review blood test results and provide a structured analysis.

IMPORTANT RULES:
1. You are NOT a doctor. Never give a diagnosis.
2. Only flag issues - do not prescribe treatment.
3. If you see something outside HRT scope (e.g. cancer markers, heart disease),
   mark it as "REFER TO SPECIALIST" immediately.
4. Keep language simple and clear.

PATIENT: {patient_text}

PATIENT BLOOD TEST RESULTS:
{values_text}
Fill in the response fields like this:
- summary: 2-3 sentence plain English overview of the results
- flagged_values: one entry per test whose Status is High or Low (empty if all are normal).
  Use each test name exactly as it is written in the results above.
  Skip tests whose Status is Unknown, but you may mention them in the summary.
- within_scope_count: number of flagged issues within HRT scope
- referral_reason: reason if refer_to_specialist is true, else an empty string
"""
    return prompt


def _strip_code_fence(text):
    """Removes ```json ... ``` in case the model wraps its JSON anyway."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    return cleaned.strip()


def _was_cut_off(response):
    candidates = getattr(response, "candidates", None) or []
    return bool(candidates) and getattr(candidates[0], "finish_reason", None) == types.FinishReason.MAX_TOKENS


def analyze_blood_report(blood_values, patient_info=None):
    """
    Sends blood values to Gemini and returns structured analysis.
    Always returns a dict — on failure it has an "error" key.
    """
    logger.info("🤖 Sending blood values to Gemini AI...")

    client = get_client()
    if client is None:
        return {"error": "GEMINI_API_KEY not found. Add it to your .env file or Streamlit secrets."}

    prompt = build_prompt(blood_values, patient_info)

    try:
        # New way to call Gemini with updated library
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,   # low temperature = more consistent/factual responses
                max_output_tokens=4096,
                response_mime_type="application/json",   # ask for JSON only...
                response_schema=BloodAnalysis,           # ...in exactly this shape
            )
        )
    except Exception as e:
        logger.error("❌ Error calling Gemini API: %s", e)
        return {"error": str(e)}

    raw_response = response.text or ""
    logger.info("✅ Got response from Gemini!")

    if _was_cut_off(response):
        logger.warning("⚠️  AI response was cut off")
        return {"raw_response": raw_response, "error": "AI response was cut off before it finished"}

    if not raw_response:
        return {"error": "AI returned an empty response (it may have been blocked by safety filters)"}

    try:
        analysis = BloodAnalysis.model_validate(json.loads(_strip_code_fence(raw_response)))
    except json.JSONDecodeError:
        logger.warning("⚠️  AI response was not valid JSON, returning raw text")
        return {"raw_response": raw_response, "error": "Could not parse JSON"}
    except ValidationError as e:
        logger.warning("⚠️  AI response did not match the expected format: %s", e)
        return {"raw_response": raw_response, "error": "AI response did not match the expected format"}

    return analysis.model_dump()


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

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    analysis = analyze_blood_report(test_blood_values)
    print_analysis(analysis)