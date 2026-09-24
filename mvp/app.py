"""KlarSchiff MVP - Streamlit app.

Run from the repository root:   streamlit run mvp/app.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from klarschiff import agent, config, intake, monitor, report  # noqa: E402
from klarschiff.intake import DOC_PATTERNS  # noqa: E402
from klarschiff.models import Shipment  # noqa: E402

NAVY, TEAL = "#081A2B", "#00B8C8"
st.set_page_config(page_title="KlarSchiff · Pre-shipment co-pilot", page_icon="⚓", layout="wide")
st.markdown(f"""<style>
.ks-title {{font-size:2.2rem;font-weight:800;color:{NAVY};margin-bottom:0}} .ks-title span{{color:{TEAL}}}
.ks-sub {{color:#5b6b7b;margin-top:0}}
.ks-card {{border:1px solid #d6e2ea;border-radius:12px;padding:16px 18px;background:#f7fbfc}}
.ks-big {{font-size:2rem;font-weight:800;color:{NAVY}}}
.ks-ok {{background:#e7f8ef;border-left:6px solid #1f9d55;padding:12px 16px;border-radius:8px}}
.ks-warn {{background:#fff4e0;border-left:6px solid #d97706;padding:12px 16px;border-radius:8px}}
</style>""", unsafe_allow_html=True)
st.markdown(f'<div style="font-size:44px;font-weight:800;color:{NAVY};line-height:1.1">Klar<span style="color:{TEAL}">Schiff</span></div>'
            '<div style="color:#5b6b7b;margin:4px 0 12px 0">AI pre-shipment co-pilot · HS code suggestion, document check and '
            'tariff monitor · <b>Clear answers. Human decisions.</b></div>', unsafe_allow_html=True)

if not config.llm_available():
    st.info("Running in **offline mode** (no OpenAI key found): keyword matching only, every result goes to manual review. "
            "Add OPENAI_API_KEY to `.env` for the full agent.", icon="ℹ️")

SAMPLES = {"(write your own)": None}
for line in (ROOT / "evaluation" / "dataset.jsonl").read_text(encoding="utf-8").splitlines():
    c = json.loads(line)
    SAMPLES[f"{c['id']} · {c['inputs']['description'][:70]}"] = c["inputs"]

tab_check, tab_monitor, tab_log, tab_about = st.tabs(["🔎 Check a shipment", "📡 Tariff monitor", "🗂️ Decisions & metrics", "ℹ️ How it works"])

# ---------------------------------------------------------------- CHECK
with tab_check:
    left, right = st.columns([1, 1.25], gap="large")
    with left:
        st.subheader("1 · Shipment (Sendung)")
        sample = st.selectbox("Load an example", list(SAMPLES))
        base = SAMPLES[sample] or {}
        desc = st.text_area("Goods description, as on the invoice (Warenbeschreibung)", base.get("description", ""), height=110,
                            placeholder="e.g. Invoice: 500 bags Portland cement CEM I 42.5, 25 kg each. DoP and CE label attached.")
        c1, c2, c3 = st.columns(3)
        origin = c1.text_input("Origin (ISO)", base.get("origin", "TR"), max_chars=2).upper()
        dest = c2.text_input("Destination (ISO)", base.get("destination", "DE"), max_chars=2).upper()
        use = c3.selectbox("Use", ["construction", "other"])
        docs = st.multiselect("Documents you have (Unterlagen vorhanden)", list(DOC_PATTERNS))
        with st.expander("Optional: invoice, packing list, PDF or e-invoice"):
            inv_csv = st.file_uploader("Invoice lines (CSV)", type=["csv"], key="inv")
            pk_csv = st.file_uploader("Packing list lines (CSV)", type=["csv"], key="pk")
            pdf = st.file_uploader("Invoice PDF (text PDF)", type=["pdf"], key="pdf")
            xml = st.file_uploader("E-invoice (XRechnung / ZUGFeRD XML)", type=["xml"], key="xml")
            st.caption("CSV columns: description, quantity, unit, gross_weight_kg, value_eur · examples in mvp/sample_data/")
        go = st.button("Check shipment", type="primary", width="stretch")

    if go:
        try:
            inv = intake.lines_from_csv(inv_csv.getvalue().decode("utf-8")) if inv_csv else [
                l for l in (base.get("invoice_lines") or [])]
            pk = intake.lines_from_csv(pk_csv.getvalue().decode("utf-8")) if pk_csv else [
                l for l in (base.get("packing_lines") or [])]
            text = desc
            if pdf:
                text = (desc + "\n" + intake.text_from_pdf(pdf.getvalue())).strip()
            if xml:
                inv = intake.lines_from_einvoice(xml.getvalue())
                text = (text + "\n" + "; ".join(l.description for l in inv)).strip()
            if len(text.strip()) < 5:
                st.warning("Please describe the goods first.")
                st.stop()
            s = Shipment(shipment_id=(sample.split(" ·")[0] if SAMPLES[sample] else "manual"), description=text,
                         origin=origin, destination=dest, intended_use=use, documents_provided=docs,
                         invoice_lines=inv, packing_lines=pk)
            with st.spinner("Checking documents, rules and tariffs…"):
                st.session_state["result"] = agent.run(s)
        except ValueError as e:
            st.error(str(e))
        except Exception as e:  # never show a stack trace to the user
            st.error(f"Something went wrong ({type(e).__name__}). The shipment was not checked; please try again or check it manually.")

    r = st.session_state.get("result")
    with right:
        st.subheader("2 · Suggestion (Vorschlag)")
        if not r:
            st.caption("The result appears here.")
        else:
            if r.manual_review:
                st.markdown('<div class="ks-warn"><b>⚠️ Manual review needed (Prüfung erforderlich)</b></div>', unsafe_allow_html=True)
                for x in r.review_reasons:
                    st.markdown(f"- {x}")
            else:
                st.markdown('<div class="ks-ok"><b>✅ All checks passed.</b> A person still approves before filing.</div>', unsafe_allow_html=True)
            k1, k2, k3 = st.columns(3)
            k1.markdown(f'<div class="ks-card">HS code<br><span class="ks-big">{r.hs_code}</span></div>', unsafe_allow_html=True)
            k2.markdown(f'<div class="ks-card">Confidence<br><span class="ks-big">{r.confidence:.0%}</span></div>', unsafe_allow_html=True)
            k3.markdown(f'<div class="ks-card">Category<br><span class="ks-big">{r.category}</span> / 3</div>', unsafe_allow_html=True)
            st.markdown(f"**{r.hs_title}**")
            st.markdown(f"**Why:** {r.reasoning}")
            if r.evidence:
                st.markdown("**Evidence:** " + ", ".join(f"`{e}`" for e in r.evidence))
            for reason in r.category_reasons:
                st.caption("• " + reason)

            st.markdown("#### Documents (Unterlagen)")
            st.dataframe(pd.DataFrame([{"Document": d.name, "Type": "required" if d.mandatory else "recommended",
                                        "Status": {"provided": "✅ provided", "missing": "❌ missing", "not stated": "❔ not stated"}[d.status],
                                        "Legal basis": d.legal_ref} for d in r.required_documents]),
                         hide_index=True, width="stretch")
            if r.validation_issues:
                st.markdown("#### Invoice vs packing list")
                for i in r.validation_issues:
                    st.markdown(f"- **{i.field}** ({i.severity}): {i.detail}")
            if r.measures:
                st.markdown("#### Trade measures and rules")
                for m in r.measures:
                    with st.expander(f"{'🔴' if m.volatility in ('high', 'very high') else '🟡'} {m.name}"):
                        st.write(m.effect)
                        st.caption(f"{m.legal_ref} · verified {m.last_verified}{' · ⚠️ re-verify' if m.stale else ''} · [source]({m.source_url})")
            if r.alerts:
                st.error(f"{len(r.alerts)} open tariff alert(s) for this code: see the Tariff monitor tab.")
            st.markdown("**Check live before filing:** " + " · ".join(f"[{k}]({v})" for k, v in r.links.items()))
            with st.expander("Retrieved candidates (RAG) and alternatives"):
                st.dataframe(pd.DataFrame([c.model_dump() for c in r.candidates]), hide_index=True)
                st.write("Alternatives considered by the model:", ", ".join(r.alternatives) or "-")
            st.caption(f"Mode: {r.mode} · model: {r.model} · knowledge base {r.kb_version} · {r.tariff_data_as_of}")

            st.markdown("#### 3 · Your decision (Ihre Entscheidung)")
            d1, d2 = st.columns([1, 1])
            decision = d1.radio("Decision", ["approved", "corrected", "rejected"], horizontal=True)
            final_hs = d2.text_input("Final HS code", r.hs_code if decision == "approved" else "")
            comment = st.text_input("Comment (why?)", "")
            b1, b2 = st.columns(2)
            if b1.button("Save decision", width="stretch"):
                if decision == "corrected" and not final_hs:
                    st.warning("Please enter the corrected HS code.")
                else:
                    report.log_decision(r, decision, final_hs, comment=comment)
                    st.success("Saved to the decision log (audit trail).")
            b2.download_button("Download review pack for the broker", report.review_pack(r, decision, final_hs, comment),
                               file_name=f"klarschiff_{r.shipment_id}_review_pack.md", width="stretch")
            st.caption(r.disclaimer)

# ---------------------------------------------------------------- MONITOR
with tab_monitor:
    st.subheader("Tariff & regulation monitor")
    st.write("Tariffs change fast (US Section 232 and general surcharges; EU steel measure from 1 Jul 2026; CBAM from 1 Jan 2026). "
             "The monitor checks official sources and opens an **alert** when something changes. While an alert is open, "
             "affected shipments always go to a person.")
    st.caption(f"Last run: {monitor.last_run()}  ·  runs daily via GitHub Actions (.github/workflows/tariff_monitor.yml) or on demand here.")
    if st.button("Run the monitor now"):
        with st.spinner("Checking the Federal Register, USITC HTS and EU pages…"):
            rep = monitor.run()
        st.success(f"{len(rep['new_alerts'])} new alert(s).")
        for e in rep["errors"]:
            st.warning("Source not reachable: " + e)
    alerts = monitor.load_alerts()
    open_a = [a for a in alerts if a["status"] == "open"]
    st.metric("Open alerts", len(open_a))
    for a in open_a[:50]:
        with st.expander(f"🔔 {a['source']} · {a['title'][:110]}"):
            st.write(a.get("detail", ""))
            st.write(f"Affects HS: {', '.join(a['affects_hs_prefixes']) or 'all'} · [open source]({a['url']})")
            note = st.text_input("Review note", key="n" + a["id"])
            if st.button("Mark as reviewed", key="b" + a["id"]):
                monitor.mark_reviewed(a["id"], note)
                st.rerun()
    from klarschiff.rules import load_measures
    st.markdown("#### Rules in force (versioned)")
    st.dataframe(pd.DataFrame([{"Measure": m["name"], "Legal reference": m["legal_ref"], "From": m["effective_from"],
                                "Volatility": m["volatility"], "Re-check every (days)": m["review_every_days"],
                                "Last verified": m["last_verified"]} for m in load_measures()["measures"]]),
                 hide_index=True, width="stretch")

# ---------------------------------------------------------------- LOG
with tab_log:
    st.subheader("Decisions and quality metrics")
    stats = report.override_rate()
    c1, c2 = st.columns(2)
    c1.metric("Decisions logged", stats["decisions"])
    c2.metric("Override rate (team level)", "-" if stats["override_rate"] is None else f"{stats['override_rate']:.0%}")
    st.caption("A very low override rate over time can mean automation bias (people stop checking). "
               "Measured per team, not per person (works-council rules in Germany, §87 BetrVG).")
    if report.LOG.exists():
        st.dataframe(pd.read_csv(report.LOG), hide_index=True, width="stretch")

# ---------------------------------------------------------------- ABOUT
with tab_about:
    st.markdown("""
**KlarSchiff checks shipment documents before the goods leave, so errors are caught at the desk, not at the border.**

1. **Intake** reads the description, CSV lines, text PDFs or e-invoices (XRechnung/ZUGFeRD).
2. **Validate** compares invoice and packing list line by line.
3. **Recommend** finds candidate headings in a reviewed knowledge base (RAG) and the LLM picks one, with reasons.
4. **Rules** (versioned, with legal references) decide category, documents and trade measures.
5. **Monitor** watches official sources for tariff changes and raises alerts.
6. **A person decides.** Every decision is logged. Nothing is ever filed automatically.

Limits: curated knowledge base (construction materials only), no OCR for scans yet, rules must be re-verified by a customs professional.
""")
