"""Money tip: a proof of preferential origin can lower or remove the EU customs duty.

Why (business need): shipments from partner countries often pay full duty only because the proof is missing.
This is not a review trigger (it is not a risk): it is a saving the team should not miss. A person checks that the
goods really meet the origin rules of the agreement; the agent never claims a preference by itself.
Rates: always check TARIC for the shipment date.
"""
from __future__ import annotations

from . import rules

# partner -> (agreement, proof the importer usually needs). Kept short and general on purpose.
AGREEMENTS = {
    "TR": ("EU-Türkiye customs union", "A.TR movement certificate"),
    "GB": ("EU-UK Trade and Cooperation Agreement", "statement on origin on the invoice, or importer's knowledge"),
    "CH": ("EU-Switzerland free trade agreement", "EUR.1 or origin declaration"),
    "NO": ("European Economic Area (EEA)", "EUR.1 or origin declaration"),
    "JP": ("EU-Japan Economic Partnership Agreement", "statement on origin, or importer's knowledge"),
    "KR": ("EU-Korea free trade agreement", "origin declaration on the invoice"),
    "CA": ("EU-Canada CETA", "origin declaration on the invoice"),
}
# German wording for the app in German (same facts, checked against the English text)
AGREEMENTS_DE = {
    "TR": "Zollunion EU-Türkei", "GB": "Handels- und Kooperationsabkommen EU-UK",
    "CH": "Freihandelsabkommen EU-Schweiz", "NO": "Europäischer Wirtschaftsraum (EWR)",
    "JP": "Wirtschaftspartnerschaftsabkommen EU-Japan", "KR": "Freihandelsabkommen EU-Korea", "CA": "CETA (EU-Kanada)",
}
PROOF_DE = {
    "A.TR movement certificate": "Warenverkehrsbescheinigung A.TR",
    "EUR.1 (steel products are outside the customs union)": "EUR.1, da Stahlprodukte nicht zur Zollunion gehören",
    "statement on origin on the invoice, or importer's knowledge": "Erklärung zum Ursprung auf der Rechnung oder Kenntnis des Einführers",
    "EUR.1 or origin declaration": "EUR.1 oder Ursprungserklärung",
    "statement on origin, or importer's knowledge": "Erklärung zum Ursprung oder Kenntnis des Einführers",
    "origin declaration on the invoice": "Ursprungserklärung auf der Rechnung",
}
PROOF_WORDS = ("a.tr", "atr", "eur.1", "eur1", "statement on origin", "origin declaration", "ursprungserklärung", "warenverkehrsbescheinigung")


def tip(shipment, hs_code: str) -> dict | None:
    """Return {agreement, proof, message, has_proof} when a preference may be possible, else None."""
    origin = (shipment.origin or "").upper()
    if origin not in AGREEMENTS or rules.region(shipment.destination) != "EU":
        return None
    agreement, proof = AGREEMENTS[origin]
    if origin == "TR" and hs_code.replace(".", "")[:2] in ("72", "73"):
        proof = "EUR.1 (steel products are outside the customs union)"
    text = (shipment.description + " " + " ".join(shipment.documents_provided)).lower()
    has = any(w in text for w in PROOF_WORDS)
    msg = (f"Preference possible under the {agreement}: with the proof ({proof}) the EU duty can be lower or zero. "
           + ("Proof mentioned: check it is valid." if has else "No proof found: ask the supplier before shipping, or the full duty applies.")
           + " A person checks the origin rules; rate in TARIC for the shipment date.")
    msg_de = (f"Präferenz möglich ({AGREEMENTS_DE[origin]}): mit dem Nachweis „{PROOF_DE.get(proof, proof)}“ "
              "kann der EU-Zoll niedriger oder null sein. "
              + ("Nachweis erwähnt: Gültigkeit prüfen." if has else
                 "Kein Nachweis gefunden: vor dem Versand beim Lieferanten anfordern, sonst gilt der volle Zollsatz.")
              + " Eine Person prüft die Ursprungsregeln; Zollsatz in TARIC zum Versanddatum.")
    return {"agreement": agreement, "proof": proof, "has_proof": has, "message": msg, "message_de": msg_de}
