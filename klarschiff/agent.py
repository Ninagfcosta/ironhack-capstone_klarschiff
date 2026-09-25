"""The KlarSchiff agent: Intake -> Validate -> Recommend -> (rules) -> Prepare, with Monitor alerts.

Every run is traced in LangSmith when LANGSMITH_TRACING=true (see .env.example).
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from langsmith import traceable

from . import config, intake, language, master_list, monitor, recommend, retrieval, rules, validate
from .models import AgentResult, Candidate, Classification, Shipment


def taric_link(hs_code: str, origin: str, on: date | None = None) -> str:
    on = on or date.today()
    code10 = hs_code.replace(".", "").ljust(10, "0")
    area = (origin or "").upper()
    return (f"https://ec.europa.eu/taxation_customs/dds2/taric/measures.jsp?Lang=en&Taric={code10}"
            f"&Area={area}&SimDate={on.strftime('%Y%m%d')}")


@traceable(name="klarschiff_agent", run_type="chain")
def run(s: Shipment, today: date | None = None) -> AgentResult:
    today = today or date.today()
    pre_reasons: list[str] = []

    # 1. Intake: language, legibility, documents mentioned in the text + structured lines
    original = s.description
    lang = language.detect_language(original)
    translated = ""
    if lang == "de":
        # v2.3: German descriptions are translated for the search over the (English) HS texts; no review needed
        if config.llm_available():
            try:
                translated = language.to_english(original).get("english", "")
            except Exception:
                translated = ""  # the German glossary still works
    elif lang != "en/de":
        if config.llm_available():
            try:
                t = language.to_english(original)
                translated = t.get("english", "")
                # Use our own detector for the label: the model sometimes answers with the target language ('en').
                note = f"Translated from '{lang}': a person checks the translation."
                if t.get("uncertain_terms"):
                    note += " Uncertain terms: " + ", ".join(map(str, t["uncertain_terms"][:5])) + "."
                pre_reasons.append(note)
            except Exception as e:
                pre_reasons.append(f"Text in '{lang}' could not be translated ({type(e).__name__}).")
        else:
            pre_reasons.append(f"Text in '{lang}' and no AI model available to translate it.")
    if translated:
        s = s.model_copy(update={"description": translated})
    if not s.legible:
        pre_reasons.append("Document partly unreadable: " + ("; ".join(s.unreadable_parts[:3]) or "check the original") + ".")

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
    candidates = retrieval.search(query, k=8)

    # 3a. Master list (Produktstamm): the product, not the part number, carries the approved code
    master_reasons: list[str] = []
    m = master_list.lookup(s.part_number, s.description)
    p = m.product
    if m.kind in ("part_number", "same_description") and p and p.hs_code:
        cls = Classification(hs_code=p.hs_code, confidence=0.95,
                             reasoning=f"Approved in the master list: product {p.product_id} '{p.description}' "
                                       f"(HS {p.hs_code}, approved {p.approved_on or 'on import'}). No new classification needed.",
                             evidence=[p.description])
        mode = "master list"
        if m.kind == "same_description" and s.part_number:
            master_reasons.append(f"New part number {master_list.normalise_pn(s.part_number)} matches product {p.product_id} "
                                  f"by description: confirm the link (HS {p.hs_code}).")
        elif m.kind == "part_number" and len(retrieval.tokenize(s.description)) >= config.MIN_CONTENT_WORDS:
            # same part number, clearly different text: maybe the part number was re-used for another product
            if master_list.similarity(p.description, s.description) < master_list.SIMILAR:
                diff = master_list.describe_differences(p.description, s.description)
                master_reasons.append(f"Known part number, but the description changed ({'; '.join(diff) or 'wording'}): "
                                      f"check product {p.product_id}.")
    else:
        if m.kind in ("part_number", "same_description") and p and not p.hs_code:
            master_reasons.append(f"Master list conflict for product {p.product_id}: codes differ in the list; a person decides.")
        if m.kind == "similar" and p:
            master_reasons.append(f"Similar to product {p.product_id} (HS {p.hs_code or '?'}) but not the same "
                                  f"({'; '.join(m.differences) or 'wording'}): a person decides.")
            if p.hs_code and p.hs_code not in [c.code for c in candidates]:
                candidates.insert(0, Candidate(code=p.hs_code, title=f"Master list: {p.description}", score=0.0, reviewed=True))
        cls, mode = recommend.classify(s, candidates)
    heading = retrieval.get_heading(cls.hs_code)
    flags = (heading or {}).get("flags", {})
    if s.intended_use != "construction":
        flags = {k: v for k, v in flags.items() if k != "cpr_hen"}

    # Rules: measures, documents, category
    measures = rules.applicable_measures(cls.hs_code, flags, s, today)
    docs = rules.required_documents(measures, provided, stated_missing)
    if s.documents_list_complete:
        for d in docs:
            if d.status == "not stated":
                d.status = "missing"
    cat, cat_reasons = rules.category(flags, measures)
    missing = [d.name for d in docs if d.mandatory and d.status == "missing"]
    not_stated = [d.name for d in docs if d.mandatory and d.status == "not stated"]

    # 5. Monitor: open alerts for this code
    alerts = monitor.open_alerts_for(cls.hs_code)

    # Review triggers (a person decides whenever one is true)
    reasons = list(pre_reasons) + master_reasons
    if cls.confidence < config.CONFIDENCE_THRESHOLD:
        reasons.append(f"Confidence {cls.confidence:.2f} is below {config.CONFIDENCE_THRESHOLD:.2f}.")
    if heading is None:
        reasons.append(f"Code {cls.hs_code} is not a valid HS 2022 subheading.")
    elif not heading.get("reviewed") and mode != "master list":
        reasons.append(f"Code {cls.hs_code} is not in the reviewed knowledge base.")
    content_words = set(retrieval.tokenize(s.description))
    if len(content_words) < config.MIN_CONTENT_WORDS and m.kind != "part_number":
        reasons.append(f"Description too vague ({len(content_words)} meaningful word(s)): material, form or use is missing.")
    if mode != "master list" and len(candidates) > 1 and candidates[1].score >= config.CLOSE_CALL_RATIO * candidates[0].score \
            and cls.hs_code in (candidates[0].code, candidates[1].code):
        reasons.append(f"Close call between {candidates[0].code} and {candidates[1].code}: a person must choose.")
    if cls.missing_information:
        reasons.append("Information missing: " + "; ".join(cls.missing_information[:3]))
    if missing:
        reasons.append("Required document(s) missing: " + "; ".join(missing))
    if issues:
        reasons.append(f"{len(issues)} invoice/packing-list mismatch(es).")
    if cat == 3:
        reasons.append("Category 3: additional trade measures or controls always need a person.")
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
        shipment_id=s.shipment_id, hs_code=cls.hs_code, hs_title=(heading or {}).get("title", "Not a valid HS 2022 code"),
        confidence=round(cls.confidence, 2), category=cat, category_reasons=cat_reasons,
        required_documents=docs, missing_documents=missing + [f"(not stated) {n}" for n in not_stated],
        validation_issues=issues, measures=measures, alerts=alerts,
        manual_review=bool(reasons), review_reasons=reasons, reasoning=cls.reasoning, evidence=cls.evidence,
        alternatives=cls.alternatives, candidates=candidates,
        links={"TARIC (EU, live)": taric_link(cls.hs_code, s.origin, today),
               "EZT-online (German customs tariff)": "https://auskunft.ezt-online.de",
               "HTS (US, live)": "https://hts.usitc.gov/search?query=" + cls.hs_code.replace(".", "")},
        mode=mode, model=config.MODEL if mode == "llm" else ("none (master list)" if mode == "master list" else "none (offline)"),
        master=(m.model_dump() if m.kind != "none" else None),
        kb_version=retrieval.load_kb()["_meta"]["version"] + " + " + retrieval.load_hs()["_meta"]["version"],
        tariff_data_as_of=f"rules {rules.load_measures()['_meta']['version']} · monitor last run {monitor.last_run()}",
        generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        source_language=lang, original_description=original, translated_description=translated,
    )
