import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import build_ai_response


def test_build_ai_response_uses_fallback_when_key_missing(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    result = build_ai_response("Hello")
    assert "fallback" in result.lower()
