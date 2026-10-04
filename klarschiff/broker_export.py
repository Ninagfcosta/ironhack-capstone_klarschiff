"""Data for the customs broker in a structured file, so nobody types it again (fewer errors, fewer billed hours).

The fields follow the information a broker needs for the declaration. It is a proposal: the broker checks and files.
"""
from __future__ import annotations

import json

from . import preference


def declaration_data(result, shipment, decision: str = "pending", final_hs: str = "") -> dict:
    lines = [l.model_dump() for l in shipment.invoice_lines]
    pref = preference.tip(shipment, final_hs or result.hs_code)
    return {
        "shipment_id": result.shipment_id,
        "status": decision,
        "hs_code_6": final_hs or result.hs_code,
        "national_line": (result.national or {}).get("suggested", ""),
        "goods_description": shipment.description,
        "origin_country": shipment.origin,
        "destination_country": shipment.destination,
        "gross_weight_kg": sum(l.get("gross_weight_kg") or 0 for l in lines) or None,
        "invoice_value_eur": sum(l.get("value_eur") or 0 for l in lines) or None,
        "documents": [{"name": d.name, "status": d.status, "legal_basis": d.legal_ref} for d in result.required_documents],
        "trade_measures": [{"name": m.name, "legal_ref": m.legal_ref} for m in result.measures],
        "preferential_origin": pref,
        "manual_review": result.manual_review,
        "review_reasons": result.review_reasons,
        "generated_at": result.generated_at,
        "note": "Proposal from KlarSchiff. The customs broker checks and files the declaration.",
    }


def to_json(result, shipment, decision: str = "pending", final_hs: str = "") -> str:
    return json.dumps(declaration_data(result, shipment, decision, final_hs), indent=2, ensure_ascii=False)
