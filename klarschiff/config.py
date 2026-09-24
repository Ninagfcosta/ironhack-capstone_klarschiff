"""Settings, read from environment variables (.env). Keys are never written in code."""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:  # python-dotenv is optional
    pass

ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = Path(__file__).resolve().parent / "knowledge"
DATA_DIR = Path(os.getenv("KLARSCHIFF_DATA_DIR", ROOT / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
# Pinned model version: re-run the evaluation before changing it (model changes can change answers).
MODEL = os.getenv("KLARSCHIFF_MODEL", "gpt-4o-mini")
TEMPERATURE = float(os.getenv("KLARSCHIFF_TEMPERATURE", "0"))

# Review rules (business decisions, documented in use_case_definition.md)
CONFIDENCE_THRESHOLD = float(os.getenv("KLARSCHIFF_CONFIDENCE_THRESHOLD", "0.75"))
LARGE_SHIPMENT_TONNES = float(os.getenv("KLARSCHIFF_LARGE_SHIPMENT_TONNES", "100"))
CBAM_THRESHOLD_TONNES = 50.0
# Added in v2.1 after error analysis (TC14 false all-clear, TC16 close call). The LLM's own confidence was
# almost always 0.9, so it is not trusted alone: these two independent checks can force a review.
MIN_CONTENT_WORDS = int(os.getenv("KLARSCHIFF_MIN_CONTENT_WORDS", "3"))
CLOSE_CALL_RATIO = float(os.getenv("KLARSCHIFF_CLOSE_CALL_RATIO", "0.85"))

EU_COUNTRIES = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IE", "IT", "LV",
    "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE", "EU",
}


def llm_available() -> bool:
    return bool(OPENAI_API_KEY) and not OPENAI_API_KEY.startswith("your_")
