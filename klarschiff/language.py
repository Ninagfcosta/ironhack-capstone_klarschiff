"""Multilingual invoices (v2.2): detect the language and translate to English before classifying.

The knowledge base and the rules are in English (with a German glossary). Invoices from Türkiye or China
often arrive in Turkish or Chinese. We translate the goods description, keep the original next to it,
and always send translated shipments to a person (a mistranslation can change the HS code).
"""
from __future__ import annotations

import re

from langsmith import traceable

from . import config, guard

TURKISH = re.compile(r"[ğĞışŞİçÇ]")  # ç added 25/09 after the manual test (çimentosu was missed)
CJK = re.compile(r"[㐀-鿿豈-﫿]")
TURKISH_WORDS = re.compile(r"\b(fatura|çimento|cimento|torba|adet|ton|çelik|celik|inşaat|insaat|nervürlü|nervurlu|seramik|karo|ahşap|ahsap)\w*", re.I)  # \w* = Turkish suffixes, e.g. çimentosu, torbalar

GERMAN = re.compile(r"[äöüßÄÖÜ]")
GERMAN_WORDS = re.compile(r"\b(und|mit|ohne|für|fuer|aus|der|die|das|stück|stueck|rechnung|lieferung|ersatzteil|anbei|fehlt)\b", re.I)

TRANSLATE_PROMPT = """You translate shipping-document goods descriptions into English for customs classification.
Keep every technical detail: material, grade (e.g. CEM I 42.5, B500B), dimensions, quantities, units, and statements
about documents (e.g. 'Declaration of Performance missing'). Do not add or interpret anything.
Reply with JSON only: {"language": "ISO 639-1 code", "english": "the translation", "uncertain_terms": ["terms you were not sure about"]}
""" + guard.DATA_RULE


def detect_language(text: str) -> str:
    """Cheap, offline first check. Returns 'zh', 'tr', 'de' or 'en/de' (English).

    German is the home language of the users: it is translated for the search when an AI model is available,
    but it does not force a review (the glossary covers German offline). Turkish and Chinese always go to a person.
    """
    if CJK.search(text):
        return "zh"
    if TURKISH.search(text) or len(TURKISH_WORDS.findall(text)) >= 2:
        return "tr"
    if GERMAN.search(text) or len(GERMAN_WORDS.findall(text)) >= 2:
        return "de"
    return "en/de"


@traceable(name="translate_description", run_type="chain")
def to_english(text: str) -> dict:
    from . import llm

    if not config.llm_available():
        raise RuntimeError("Translation needs the AI model (no API key found).")
    data = llm.chat_json(TRANSLATE_PROMPT, guard.wrap(text))
    data.setdefault("english", "")
    data.setdefault("uncertain_terms", [])
    return data
