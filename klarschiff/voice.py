"""Voice notes: warehouse staff describe the goods by voice; Whisper turns it into text (course lab: Whisper).

The transcript is shown to the person and added to the goods description; it is checked like typed text.
Needs an AI key. Audio is sent to the speech model only for transcription; do not record names or addresses.
"""
from __future__ import annotations

import io

from . import config

MODEL = "whisper-1"


def transcribe(audio: bytes, filename: str = "note.m4a") -> str:
    if not config.llm_available():
        raise RuntimeError("No AI key: voice notes need the speech model.")
    from openai import OpenAI
    kw = {"api_key": config.LLM_API_KEY, "timeout": 60}
    if config.LLM_BASE_URL:
        kw["base_url"] = config.LLM_BASE_URL
    f = io.BytesIO(audio); f.name = filename
    return OpenAI(**kw).audio.transcriptions.create(model=MODEL, file=f).text.strip()
