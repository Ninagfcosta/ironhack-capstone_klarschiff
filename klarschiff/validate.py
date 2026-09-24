"""Step 2 - Validate: compare the invoice with the packing list, line by line.

Deterministic on purpose: a mismatch in quantity or weight is a fact, not an opinion, so no LLM is needed.
"""
from __future__ import annotations

from difflib import SequenceMatcher

from .models import Line, ValidationIssue

WEIGHT_TOLERANCE = 0.02   # 2 % difference in gross weight is accepted (scales, packaging)


def _similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def compare(invoice: list[Line], packing: list[Line]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not invoice or not packing:
        return issues
    if len(invoice) != len(packing):
        issues.append(ValidationIssue(field="lines", severity="high",
                                      detail=f"Invoice has {len(invoice)} line(s), packing list has {len(packing)}."))
    for i, (inv, pk) in enumerate(zip(invoice, packing), start=1):
        if inv.description and pk.description and _similar(inv.description, pk.description) < 0.6:
            issues.append(ValidationIssue(field=f"line {i} description", severity="medium",
                                          detail=f"'{inv.description}' (invoice) vs '{pk.description}' (packing list)."))
        if inv.quantity is not None and pk.quantity is not None and abs(inv.quantity - pk.quantity) > 1e-9:
            issues.append(ValidationIssue(field=f"line {i} quantity", severity="high",
                                          detail=f"{inv.quantity:g} {inv.unit or ''} on the invoice vs {pk.quantity:g} {pk.unit or ''} on the packing list."))
        if inv.gross_weight_kg and pk.gross_weight_kg:
            diff = abs(inv.gross_weight_kg - pk.gross_weight_kg) / max(inv.gross_weight_kg, pk.gross_weight_kg)
            if diff > WEIGHT_TOLERANCE:
                issues.append(ValidationIssue(field=f"line {i} gross weight", severity="medium",
                                              detail=f"{inv.gross_weight_kg:g} kg vs {pk.gross_weight_kg:g} kg ({diff:.0%} difference)."))
    return issues
