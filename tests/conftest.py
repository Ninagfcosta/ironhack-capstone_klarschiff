"""Unit tests never call a paid AI model: without this, a real key in .env would make every test call OpenAI.
Tests that need the model path set llm_available to True themselves and mock the call."""
import os
import sys
from pathlib import Path

import pytest

os.environ["LANGSMITH_TRACING"] = "false"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(autouse=True)
def no_paid_llm(monkeypatch):
    from klarschiff import config
    monkeypatch.setattr(config, "llm_available", lambda: False)
