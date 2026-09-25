"""Data models for the KlarSchiff agent (inputs, intermediate results and the final answer)."""
from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field


class Line(BaseModel):
    """One line of an invoice or packing list."""
    description: str
    quantity: Optional[float] = None
    unit: Optional[str] = None
    gross_weight_kg: Optional[float] = None
    value_eur: Optional[float] = None


class Shipment(BaseModel):
    """Everything the user gives the agent about one shipment."""
    shipment_id: str = "demo"
    description: str = Field(..., description="Free-text description of the goods, as on the invoice")
    origin: str = Field("", description="ISO country code of origin, e.g. TR")
    destination: str = Field("DE", description="ISO country code of destination, e.g. DE or US")
    documents_provided: list[str] = Field(default_factory=list)
    documents_list_complete: bool = Field(False, description="True = every document not listed as provided is missing")
    invoice_lines: list[Line] = Field(default_factory=list)
    packing_lines: list[Line] = Field(default_factory=list)
    intended_use: str = Field("construction", description="construction / other")
    legible: bool = Field(True, description="False when a scan or photo could not be read completely")
    unreadable_parts: list[str] = Field(default_factory=list)
    source: str = Field("typed", description="typed / text PDF / scan / photo / e-invoice")
    part_number: str = Field("", description="Client part number (Artikelnummer), optional; used for the master list")


class Candidate(BaseModel):
    code: str
    title: str
    score: float
    reviewed: bool = False  # True = heading in the reviewed layer (checked by a person, with rule flags)


class Classification(BaseModel):
    """What the LLM (or the offline fallback) returns."""
    hs_code: str = Field(..., description="6-digit HS code, format 0000.00")
    confidence: float = Field(..., ge=0, le=1)
    reasoning: str
    evidence: list[str] = Field(default_factory=list, description="Words from the description that support the code")
    alternatives: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)


class RequiredDocument(BaseModel):
    name: str
    reason: str
    legal_ref: str = ""
    mandatory: bool = True
    status: Literal["provided", "missing", "not stated"] = "not stated"


class MeasureHit(BaseModel):
    id: str
    name: str
    effect: str
    legal_ref: str
    source_url: str
    last_verified: str
    stale: bool = False
    volatility: str = "low"
    upcoming: bool = False  # starts within 180 days: shown as a warning, no documents required yet
    effective_from: str = ""


class ValidationIssue(BaseModel):
    field: str
    detail: str
    severity: Literal["low", "medium", "high"] = "medium"


class AgentResult(BaseModel):
    shipment_id: str
    hs_code: str
    hs_title: str
    confidence: float
    category: int
    category_reasons: list[str]
    required_documents: list[RequiredDocument]
    missing_documents: list[str]
    validation_issues: list[ValidationIssue]
    measures: list[MeasureHit]
    alerts: list[dict]
    manual_review: bool
    review_reasons: list[str]
    reasoning: str
    evidence: list[str]
    alternatives: list[str]
    candidates: list[Candidate]
    links: dict[str, str]
    mode: Literal["llm", "offline", "master list"]
    model: str
    kb_version: str
    tariff_data_as_of: str
    generated_at: str
    master: dict | None = None  # master-list match: kind, product, score, differences
    national: dict = Field(default_factory=dict)  # v2.3: CN (EU, 8 digits) or HTS (US) lines under the HS code
    precedents: list[dict] = Field(default_factory=list)  # v2.3: similar official rulings from the team's library
    usage: dict = Field(default_factory=dict)  # v2.3: tokens and estimated cost of the AI calls for this check
    source_language: str = "en/de"
    original_description: str = ""
    translated_description: str = ""
    disclaimer: str = (
        "Decision support only. A qualified person must confirm the classification and the documents "
        "before any customs declaration. Check the live tariff (TARIC / HTS) for the shipment date."
    )
