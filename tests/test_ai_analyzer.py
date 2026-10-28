import json
from types import SimpleNamespace

import pytest
from google.genai import types

import ai_analyzer


class FakeClient:
    """Stands in for the Gemini client so tests never call the real API."""

    def __init__(self, text, finish_reason=types.FinishReason.STOP):
        self.calls = []

        def generate_content(**kwargs):
            self.calls.append(kwargs)
            return SimpleNamespace(text=text, candidates=[SimpleNamespace(finish_reason=finish_reason)])

        self.models = SimpleNamespace(generate_content=generate_content)


VALUES = {"Glucose": {"value": 112, "unit": "mg/dL", "status": "High", "ref_range": "70 - 100"}}
ANALYSIS = {
    "summary": "Fasting glucose is slightly high.",
    "flagged_values": [{
        "test": "Glucose", "value": "112 mg/dL", "issue": "High",
        "explanation": "Blood sugar is above the normal range.",
        "within_hrt_scope": True, "action": "Monitor",
    }],
    "within_scope_count": 1,
    "refer_to_specialist": False,
    "referral_reason": "",
    "overall_status": "Needs Attention",
}


@pytest.fixture
def use_client(monkeypatch):
    def _use(text, **kwargs):
        client = FakeClient(text, **kwargs)
        monkeypatch.setattr(ai_analyzer, "_client", client)
        return client
    return _use


def test_missing_api_key_returns_error(monkeypatch):
    monkeypatch.setattr(ai_analyzer, "_client", None)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    result = ai_analyzer.analyze_blood_report(VALUES)
    assert "GEMINI_API_KEY" in result["error"]


def test_parses_valid_json(use_client):
    use_client(json.dumps(ANALYSIS))
    assert ai_analyzer.analyze_blood_report(VALUES) == ANALYSIS


def test_asks_for_schema_json(use_client):
    client = use_client(json.dumps(ANALYSIS))
    ai_analyzer.analyze_blood_report(VALUES)
    config = client.calls[0]["config"]
    assert config.response_mime_type == "application/json"
    assert config.response_schema is ai_analyzer.BloodAnalysis


def test_strips_markdown_code_fence(use_client):
    use_client("```json\n" + json.dumps(ANALYSIS) + "\n```")
    assert ai_analyzer.analyze_blood_report(VALUES) == ANALYSIS


def test_invalid_json_returns_error(use_client):
    use_client("Sorry, I can't help with that.")
    result = ai_analyzer.analyze_blood_report(VALUES)
    assert result["error"] == "Could not parse JSON"


def test_wrong_shape_returns_error(use_client):
    bad = {**ANALYSIS, "overall_status": "Fine"}  # not one of the allowed values
    use_client(json.dumps(bad))
    result = ai_analyzer.analyze_blood_report(VALUES)
    assert result["error"] == "AI response did not match the expected format"


def test_missing_field_returns_error(use_client):
    bad = {k: v for k, v in ANALYSIS.items() if k != "flagged_values"}
    use_client(json.dumps(bad))
    assert "error" in ai_analyzer.analyze_blood_report(VALUES)


def test_cut_off_response_returns_error(use_client):
    use_client(json.dumps(ANALYSIS)[:50], finish_reason=types.FinishReason.MAX_TOKENS)
    result = ai_analyzer.analyze_blood_report(VALUES)
    assert "cut off" in result["error"]


def test_empty_response_returns_error(use_client):
    use_client(None)  # e.g. response blocked by safety filters
    assert "empty" in ai_analyzer.analyze_blood_report(VALUES)["error"]


def test_api_exception_returns_error(monkeypatch):
    def boom(**kwargs):
        raise RuntimeError("429 quota exceeded")

    monkeypatch.setattr(ai_analyzer, "_client", SimpleNamespace(models=SimpleNamespace(generate_content=boom)))
    assert ai_analyzer.analyze_blood_report(VALUES) == {"error": "429 quota exceeded"}


def test_prompt_lists_every_value():
    prompt = ai_analyzer.build_prompt(VALUES)
    assert "Glucose: 112 mg/dL (Status: High, Reference: 70 - 100)" in prompt
    assert "PATIENT: unknown" in prompt


def test_prompt_includes_patient_info():
    prompt = ai_analyzer.build_prompt(VALUES, {"age": 52, "sex": "Female", "report_date": "01/02/2024"})
    assert "PATIENT: 52 years old, Female" in prompt
