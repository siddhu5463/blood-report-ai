import json
from types import SimpleNamespace

from google.genai import types

import ai_analyzer
import main


def fake_gemini(monkeypatch, reply):
    response = SimpleNamespace(text=reply, candidates=[SimpleNamespace(finish_reason=types.FinishReason.STOP)])
    client = SimpleNamespace(models=SimpleNamespace(generate_content=lambda **kwargs: response))
    monkeypatch.setattr(ai_analyzer, "_client", client)


ANALYSIS = {
    "summary": "s",
    "flagged_values": [
        {"test": "Estradiol (E2)", "value": "42 pg/mL", "issue": "High", "explanation": "e",
         "within_hrt_scope": True, "action": "Monitor"},
        {"test": "Glucose (Fasting)", "value": "112 mg/dL", "issue": "High", "explanation": "e",
         "within_hrt_scope": True, "action": "Monitor"},
    ],
    "refer_to_specialist": False,
    "referral_reason": "",
    "overall_status": "Needs Attention",
}


def test_full_pipeline_with_prescription(monkeypatch, sample_pdf, capsys):
    fake_gemini(monkeypatch, json.dumps(ANALYSIS))
    assert main.run_pipeline(sample_pdf, ["Anastrozole 0.5mg", "Aspirin"]) is True

    out = capsys.readouterr().out
    assert "AST                      42" in out           # Phase 1 values are printed
    assert "PHASE 4" in out
    assert "Match Score: 50/100" in out                  # Estradiol covered, Glucose not
    assert "Aspirin" in out


def test_pipeline_stops_after_ai_error(monkeypatch, sample_pdf, capsys):
    fake_gemini(monkeypatch, "not json")
    assert main.run_pipeline(sample_pdf, ["Anastrozole"]) is False
    out = capsys.readouterr().out
    assert "Could not parse JSON" in out
    assert "PHASE 3" not in out
