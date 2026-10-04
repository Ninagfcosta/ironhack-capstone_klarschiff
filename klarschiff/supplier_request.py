"""Draft an e-mail to the supplier that asks for missing documents. A person reads, edits and sends it.

Why (pilot need): chasing missing documents is slow, repetitive e-mail work.
The draft names each missing document and its legal basis, in English or German.
Nothing is sent automatically: the app only shows the text (copy or download).
"""
from __future__ import annotations

from . import config, llm
from .guard import DATA_RULE

SYSTEM = ("You write short, polite, professional business e-mails for a logistics team. "
          "Write to a supplier and ask for the missing shipment documents listed. Name each document and why it is "
          "needed (legal basis). Do not invent facts, dates, prices or names. Use the placeholder [Name] for the "
          "contact and [Your name] for the signature. Answer as JSON: {\"subject\": \"...\", \"body\": \"...\"}. "
          + DATA_RULE)


def missing_items(result) -> list[tuple[str, str]]:
    return [(d.name, d.legal_ref) for d in result.required_documents if d.mandatory and d.status in ("missing", "not stated")]


def template(result, lang: str = "en") -> dict:
    items = missing_items(result)
    lines = "\n".join(f"- {n} ({ref})" if ref else f"- {n}" for n, ref in items) or "- (no document missing)"
    if lang == "de":
        return {"subject": f"Fehlende Unterlagen für Sendung {result.shipment_id}",
                "body": f"Sehr geehrte/r [Name],\n\nfür die Sendung {result.shipment_id} (HS {result.hs_code}) fehlen uns "
                        f"noch folgende Unterlagen:\n{lines}\n\nKönnten Sie uns diese bitte vor dem Versand schicken? "
                        f"So vermeiden wir Verzögerungen beim Zoll.\n\nVielen Dank und freundliche Grüße\n[Your name]"}
    return {"subject": f"Missing documents for shipment {result.shipment_id}",
            "body": f"Dear [Name],\n\nfor shipment {result.shipment_id} (HS {result.hs_code}) we still need the following "
                    f"documents:\n{lines}\n\nCould you please send them before the goods are shipped? This helps us "
                    f"avoid a delay at customs.\n\nThank you and kind regards,\n[Your name]"}


def draft(result, lang: str = "en") -> dict:
    """LLM draft when a key is set, otherwise the fixed template. Always returns {subject, body}."""
    if not missing_items(result) or not config.llm_available():
        return template(result, lang)
    language = "German" if lang == "de" else "English"
    items = "\n".join(f"- {n}: {ref}" for n, ref in missing_items(result))
    user = (f"Language: {language}\nShipment: {result.shipment_id}\nHS code: {result.hs_code} ({result.hs_title})\n"
            f"Missing documents:\n<document>\n{items}\n</document>")
    try:
        out = llm.chat_json(SYSTEM, user)
        if out.get("subject") and out.get("body"):
            return {"subject": str(out["subject"]), "body": str(out["body"])}
    except Exception:
        pass
    return template(result, lang)
