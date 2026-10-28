import json
from types import SimpleNamespace

import pytest

import ai_analyzer


class FakeClient:
    """Stands in for the Gemini client so tests never call the real API."""

    def __init__(self, text):
        self.models = SimpleNamespace(generate_content=lambda **kwargs: SimpleNamespace(text=text))


VALUES = {"Glucose": {"value": 112, "unit": "mg/dL", "status": "High", "ref_range": "70 - 100"}}
ANALYSIS = {"summary": "s", "flagged_values": [], "overall_status": "Good"}


@pytest.fixture
def use_client(monkeypatch):
    def _use(text):
        monkeypatch.setattr(ai_analyzer, "_client", FakeClient(text))
    return _use


def test_missing_api_key_returns_error(monkeypatch):
    monkeypatch.setattr(ai_analyzer, "_client", None)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    result = ai_analyzer.analyze_blood_report(VALUES)
    assert "GEMINI_API_KEY" in result["error"]


def test_parses_plain_json(use_client):
    use_client(json.dumps(ANALYSIS))
    assert ai_analyzer.analyze_blood_report(VALUES) == ANALYSIS


def test_strips_markdown_code_fence(use_client):
    use_client("```json\n" + json.dumps(ANALYSIS) + "\n```")
    assert ai_analyzer.analyze_blood_report(VALUES) == ANALYSIS


def test_invalid_json_returns_error(use_client):
    use_client("Sorry, I can't help with that.")
    result = ai_analyzer.analyze_blood_report(VALUES)
    assert result["error"] == "Could not parse JSON"


def test_empty_response_returns_error(use_client):
    use_client(None)  # e.g. response blocked by safety filters
    assert "error" in ai_analyzer.analyze_blood_report(VALUES)


def test_prompt_lists_every_value():
    prompt = ai_analyzer.build_prompt(VALUES)
    assert "Glucose: 112 mg/dL (Status: High, Reference: 70 - 100)" in prompt
