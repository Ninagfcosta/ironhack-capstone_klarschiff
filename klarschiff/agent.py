"""The KlarSchiff agent: Intake -> Validate -> Recommend -> (rules) -> Prepare, with Monitor alerts.

Every run is traced in LangSmith when LANGSMITH_TRACING=true (see .env.example).
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from langsmith import traceable

from . import config, intake, monitor, recommend, retrieval, rules, validate
from .models import AgentResult, Shipment


def taric_link(hs_code: str, origin: str, on: date | None = None) -> str:
    on = on or date.today()
    code10 = hs_code.replace(".", "").ljust(10, "0")
    area = (origin or "").upper()
    return (f"https://ec.europa.eu/taxation_customs/dds2/taric/measures.jsp?Lang=en&Taric={code10}"
            f"&Area={area}&SimDate={on.strftime('%Y%m%d')}")


@traceable(name="klarschiff_agent", run_type="chain")
def run(s: Shipment, today: date | None = None) -> AgentResult:
    today = today or date.today()

    # 1. Intake: documents mentioned in the text + structured lines
    provided_txt, missing_txt = intake.detect_documents(s.description)
    provided = list(dict.fromkeys(s.documents_provided + provided_txt))
    stated_missing = [d for d in missing_txt if d not in s.documents_provided]
    tonnes = intake.extract_tonnes(s.description)
    if tonnes is None and s.invoice_lines:
        w = sum(l.gross_weight_kg or 0 for l in s.invoice_lines)
        tonnes = w / 1000 if w else None

    # 2. Validate: invoice vs packing list
    issues = validate.compare(s.invoice_lines, s.packing_lines)

    # 3. Recommend: retrieval (RAG) + LLM choice
    query = s.description + " " + " ".join(l.description for l in s.invoice_lines)
    candidates = retrieval.search(query, k=5)
    cls, mode = recommend.classify(s, candidates)
    heading = retrieval.get_heading(cls.hs_code)
    flags = (heading or {}).get("flags", {})
    if s.intended_use != "construction":
        flags = {k: v for k, v in flags.items() if k != "cpr_hen"}

    # Rules: measures, documents, category
    measures = rules.applicable_measures(cls.hs_code, flags, s, today)
    docs = rules.required_documents(measures, provided, stated_missing)
    cat, cat_reasons = rules.category(flags, measures)
    missing = [d.name for d in docs if d.mandatory and d.status == "missing"]
    not_stated = [d.name for d in docs if d.mandatory and d.status == "not stated"]

    # 5. Monitor: open alerts for this code
    alerts = monitor.open_alerts_for(cls.hs_code)

    # Review triggers (a person decides whenever one is true)
    reasons = []
    if cls.confidence < config.CONFIDENCE_THRESHOLD:
        reasons.append(f"Confidence {cls.confidence:.2f} is below {config.CONFIDENCE_THRESHOLD:.2f}.")
    if heading is None:
        reasons.append(f"Code {cls.hs_code} is not in the reviewed knowledge base.")
    if cls.missing_information:
        reasons.append("Information missing: " + "; ".join(cls.missing_information[:3]))
    if missing:
        reasons.append("Required document(s) missing: " + "; ".join(missing))
    if issues:
        reasons.append(f"{len(issues)} invoice/packing-list mismatch(es).")
    if cat == 3:
        reasons.append("Category 3: additional trade measures always need a person.")
    if tonnes and tonnes >= config.LARGE_SHIPMENT_TONNES:
        reasons.append(f"Large shipment (~{tonnes:g} t).")
    if tonnes and any(m.id == "EU_CBAM" for m in measures) and tonnes >= config.CBAM_THRESHOLD_TONNES:
        reasons.append(f"CBAM: this shipment alone (~{tonnes:g} t) is above the 50 t yearly threshold.")
    if any(m.stale for m in measures):
        reasons.append("Rule data older than its review interval: re-verify the source.")
    if alerts:
        reasons.append(f"{len(alerts)} open tariff/regulation alert(s) for this code.")
    if mode == "offline":
        reasons.append("Offline mode (no LLM): keyword match only.")

    return AgentResult(
        shipment_id=s.shipment_id, hs_code=cls.hs_code, hs_title=(heading or {}).get("title", "Not in knowledge base"),
        confidence=round(cls.confidence, 2), category=cat, category_reasons=cat_reasons,
        required_documents=docs, missing_documents=missing + [f"(not stated) {n}" for n in not_stated],
        validation_issues=issues, measures=measures, alerts=alerts,
        manual_review=bool(reasons), review_reasons=reasons, reasoning=cls.reasoning, evidence=cls.evidence,
        alternatives=cls.alternatives, candidates=candidates,
        links={"TARIC (EU, live)": taric_link(cls.hs_code, s.origin, today),
               "EZT-online (German customs tariff)": "https://auskunft.ezt-online.de",
               "HTS (US, live)": "https://hts.usitc.gov/search?query=" + cls.hs_code.replace(".", "")},
        mode=mode, model=config.MODEL if mode == "llm" else "none (offline)",
        kb_version=retrieval.load_kb()["_meta"]["version"],
        tariff_data_as_of=f"rules {rules.load_measures()['_meta']['version']} · monitor last run {monitor.last_run()}",
        generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )
