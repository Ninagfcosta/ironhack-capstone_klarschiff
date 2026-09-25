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

import hmac  # noqa: E402

from klarschiff import agent, batch, config, intake, master_list, monitor, precedents, report, tariff_lines, vision  # noqa: E402
from klarschiff.intake import DOC_PATTERNS  # noqa: E402
from klarschiff.models import Shipment  # noqa: E402

sys.path.insert(0, str(ROOT / "mvp"))
from i18n import ABOUT, LANGS, reason, t  # noqa: E402

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
# ---------------------------------------------------------------- LANGUAGE (English default, German on one click)
head, switch = st.columns([5, 1])
with switch:
    L = st.radio("🌐 Language / Sprache", list(LANGS), format_func=LANGS.get, horizontal=True, key="lang")
T = lambda text, *a: t(text, L, *a)  # noqa: E731
head.markdown(f'<div style="font-size:44px;font-weight:800;color:{NAVY};line-height:1.1">Klar<span style="color:{TEAL}">Schiff</span></div>'
              f'<div style="color:#5b6b7b;margin:4px 0 12px 0">{T("AI pre-shipment co-pilot · HS code suggestion, document check and tariff monitor")}'
              f' · <b>{T("Clear answers. Human decisions.")}</b></div>', unsafe_allow_html=True)

# ---------------------------------------------------------------- LOGIN (set KLARSCHIFF_APP_PASSWORD on any shared server)
if config.APP_PASSWORD and not st.session_state.get("auth"):
    pw = st.text_input(T("Password"), type="password")
    if st.button(T("Log in")):
        if hmac.compare_digest(pw.encode(), config.APP_PASSWORD.encode()):
            st.session_state["auth"] = True
            st.rerun()
        else:
            st.error(T("Wrong password."))
    st.stop()

if not config.llm_available():
    st.info(T("Running in **offline mode** (no AI key found): keyword matching only, every result goes to manual review. "
              "Add OPENAI_API_KEY to `.env` for the full agent."), icon="ℹ️")

SAMPLES = {"(write your own)": None}
for line in (ROOT / "evaluation" / "dataset.jsonl").read_text(encoding="utf-8").splitlines():
    c = json.loads(line)
    SAMPLES[f"{c['id']} · {c['inputs']['description'][:70]}"] = c["inputs"]

tab_check, tab_batch, tab_master, tab_monitor, tab_log, tab_about = st.tabs(
    [T(x) for x in ["🔎 Check a shipment", "📦 Batch", "📒 Master list", "📡 Tariff monitor", "🗂️ Decisions & metrics",
                    "ℹ️ How it works"]])

# ---------------------------------------------------------------- CHECK
with tab_check:
    left, right = st.columns([1, 1.25], gap="large")
    with left:
        st.subheader(T("1 · Shipment"))
        # keys include the language so labels re-render; the chosen value is carried over (Streamlit keeps text inputs by key)
        opts = list(SAMPLES)
        sample = st.selectbox(T("Load an example"), opts, format_func=T, key="sample_" + L,
                              index=opts.index(st.session_state.get("sample_val", opts[0])))
        st.session_state["sample_val"] = sample
        base = SAMPLES[sample] or {}
        desc = st.text_area(T("Goods description, as on the invoice"), base.get("description", ""), height=110, key="desc_" + sample,
                            placeholder=T("e.g. Invoice: 500 bags Portland cement CEM I 42.5, 25 kg each. DoP and CE label attached."))
        c1, c2, c3 = st.columns(3)
        origin = c1.text_input(T("Origin (ISO)"), base.get("origin", "TR"), max_chars=2, key="origin_" + sample).upper()
        dest = c2.text_input(T("Destination (ISO)"), base.get("destination", "DE"), max_chars=2, key="dest_" + sample).upper()
        uses = ["construction", "other"]
        use = c3.selectbox(T("Use"), uses, format_func=T, key="use_" + L, index=uses.index(st.session_state.get("use_val", "construction")))
        st.session_state["use_val"] = use
        part_no = st.text_input(T("Part number (optional)"), base.get("part_number", ""), key="pn_" + sample,
                                help=T("Used to find the product in the master list, even when the part number changed."))
        docs = st.multiselect(T("Documents you have"), list(DOC_PATTERNS), key="docs", placeholder=T("Choose options"))
        complete = st.checkbox(T("This list is complete: anything not selected is missing"), value=False, key="complete")
        with st.expander(T("Optional: invoice, packing list, PDF, scan, photo or e-invoice")):
            inv_csv = st.file_uploader(T("Invoice lines (CSV)"), type=["csv"], key="inv")
            pk_csv = st.file_uploader(T("Packing list lines (CSV)"), type=["csv"], key="pk")
            pdf = st.file_uploader(T("Invoice PDF (text or scanned)"), type=["pdf"], key="pdf")
            photo = st.file_uploader(T("Scan or photo of the invoice (JPG / PNG)"), type=["png", "jpg", "jpeg"], key="photo")
            xml = st.file_uploader(T("E-invoice (XRechnung / ZUGFeRD XML)"), type=["xml"], key="xml")
            st.caption(T("CSV columns: description, quantity, unit, gross_weight_kg, value_eur · examples in mvp/sample_data/ · "
                         "Scans and photos are read by the AI model: cover names, signatures and addresses before uploading."))
        go = st.button(T("Check shipment"), type="primary", width="stretch")

    if go:
        st.session_state["vision"] = None
        try:
            inv = intake.lines_from_csv(inv_csv.getvalue().decode("utf-8")) if inv_csv else [
                l for l in (base.get("invoice_lines") or [])]
            pk = intake.lines_from_csv(pk_csv.getvalue().decode("utf-8")) if pk_csv else [
                l for l in (base.get("packing_lines") or [])]
            text, legible, unreadable, source = desc, True, [], "typed"

            vr = None
            if pdf:
                try:
                    text = (desc + "\n" + intake.text_from_pdf(pdf.getvalue())).strip()
                    source = "text PDF"
                except ValueError:
                    with st.spinner(T("Scanned PDF: reading it with the AI model…")):
                        vr = vision.read_scanned_pdf(pdf.getvalue())
                    source = "scanned PDF"
            if photo:
                with st.spinner(T("Reading the photo with the AI model…")):
                    mime = "image/png" if photo.name.lower().endswith(".png") else "image/jpeg"
                    vr = vision.read_image(photo.getvalue(), mime)
                source = "photo"
            if vr is not None:
                text = (desc + "\n" + (vr.get("text") or "") + "\n" + ". ".join(vr.get("documents_mentioned") or [])).strip()
                legible, unreadable = bool(vr.get("legible")), list(vr.get("unreadable_parts") or [])
                if not inv and vr.lines:
                    inv = vr.lines
                st.session_state["vision"] = dict(vr)
            if xml:
                inv = intake.lines_from_einvoice(xml.getvalue())
                text = (text + "\n" + "; ".join(l.description for l in inv)).strip()
            if len(text.strip()) < 5:
                st.warning(T("Please describe the goods first."))
                st.stop()
            s = Shipment(shipment_id=(sample.split(" ·")[0] if SAMPLES[sample] else "manual"), description=text,
                         origin=origin, destination=dest, intended_use=use, documents_provided=docs,
                         invoice_lines=inv, packing_lines=pk, documents_list_complete=complete, legible=legible, unreadable_parts=unreadable, source=source,
                         part_number=part_no)
            st.session_state["shipment"] = s
            with st.spinner(T("Checking documents, rules and tariffs…")):
                st.session_state["result"] = agent.run(s)
        except ValueError as e:
            st.error(str(e))
        except Exception as e:  # never show a stack trace to the user
            st.error(T("Something went wrong ({}). The shipment was not checked; please try again or check it manually.", type(e).__name__))

    r = st.session_state.get("result")
    with right:
        st.subheader(T("2 · Suggestion"))
        if not r:
            st.caption(T("The result appears here."))
        else:
            if r.manual_review:
                st.markdown(f'<div class="ks-warn"><b>{T("⚠️ Manual review needed")}</b></div>', unsafe_allow_html=True)
                for x in r.review_reasons:
                    st.markdown(f"- {reason(x, L)}")
            else:
                st.markdown(f'<div class="ks-ok"><b>{T("✅ All checks passed.")}</b> {T("A person still approves before filing.")}</div>', unsafe_allow_html=True)
            k1, k2, k3 = st.columns(3)
            k1.markdown(f'<div class="ks-card">{T("HS code")}<br><span class="ks-big">{r.hs_code}</span></div>', unsafe_allow_html=True)
            k2.markdown(f'<div class="ks-card">{T("Confidence")}<br><span class="ks-big">{r.confidence:.0%}</span></div>', unsafe_allow_html=True)
            k3.markdown(f'<div class="ks-card">{T("Category")}<br><span class="ks-big">{r.category}</span> / 3</div>', unsafe_allow_html=True)
            st.markdown(f"**{r.hs_title}**")
            if r.master:
                mp = r.master.get("product") or {}
                kind = {"part_number": "📒 Known part number", "same_description": "📒 New part number, same product",
                        "similar": "📒 Similar product in the master list"}.get(r.master["kind"], "📒 Master list")
                with st.expander(T(kind) + f": {mp.get('product_id', '')}", expanded=True):
                    st.markdown(f"**{mp.get('description', '')}** · HS **{mp.get('hs_code') or '-'}**")
                    if mp.get("description_de"):
                        st.markdown(f"🇩🇪 {mp['description_de']}")
                    st.caption(T("Part numbers") + ": " + (", ".join(mp.get("part_numbers") or []) or "-"))
                    for dff in r.master.get("differences") or []:
                        st.warning(dff)
            if r.national:
                nat = r.national
                with st.expander(T("🔢 Full code ({})", nat["system"]) + (f": {nat['suggested']}" if nat.get("suggested") else ""),
                                 expanded=True):
                    if nat.get("suggested"):
                        st.caption(T("Suggested by word match; a person confirms the line."))
                    else:
                        st.caption(T("Several lines fit: a person chooses."))
                    st.dataframe(pd.DataFrame(nat["lines"]), hide_index=True, width="stretch")
            if r.precedents:
                with st.expander(T("📚 Similar official rulings in your library ({})", len(r.precedents))):
                    for pr in r.precedents:
                        badge = "✅" if pr.get("valid") else "⌛ " + T("expired")
                        st.markdown(f"- **{pr['reference']}** ({pr['source']}) · HS {pr['code']} · {badge}: {pr['description'][:160]}")
            if r.translated_description:
                with st.expander(T("🌐 Translated from '{}': original and English", r.source_language), expanded=True):
                    st.markdown(f"**{T('Original')}:** {r.original_description}")
                    st.markdown(f"**{T('English (used for the check)')}:** {r.translated_description}")
            if st.session_state.get("vision"):
                v = st.session_state["vision"]
                with st.expander(T("📷 Read from the scan/photo ({}, legible: {})", v.get('document_type', 'document'), v.get('legible'))):
                    st.write(v.get("text", ""))
                    if v.get("unreadable_parts"):
                        st.warning(T("Not readable") + ": " + "; ".join(v["unreadable_parts"]))
            st.markdown(f"**{T('Why')}:** {r.reasoning}")
            if L == "de":
                st.caption(T("The AI model writes its reasoning in English."))
            if r.evidence:
                st.markdown(f"**{T('Evidence')}:** " + ", ".join(f"`{e}`" for e in r.evidence))
            for cr in r.category_reasons:
                st.caption("• " + reason(cr, L))

            st.markdown("#### " + T("Documents"))
            status = {"provided": "✅ provided", "missing": "❌ missing", "not stated": "❔ not stated"}
            st.dataframe(pd.DataFrame([{T("Document"): d.name, T("Type"): T("required" if d.mandatory else "recommended"),
                                        T("Status"): T(status[d.status]), T("Legal basis"): d.legal_ref} for d in r.required_documents]),
                         hide_index=True, width="stretch")
            if r.validation_issues:
                st.markdown("#### " + T("Invoice vs packing list"))
                for i in r.validation_issues:
                    st.markdown(f"- **{i.field}** ({i.severity}): {i.detail}")
            if r.measures:
                st.markdown("#### " + T("Trade measures and rules"))
                for m in r.measures:
                    icon = "⏳" if m.upcoming else ("🔴" if m.volatility in ("high", "very high") else "🟡")
                    label = f"{icon} {m.name}" + (f" · {T('from')} {m.effective_from}" if m.upcoming else "")
                    with st.expander(label):
                        st.write(m.effect)
                        st.caption(f"{m.legal_ref} · {T('verified')} {m.last_verified}{' · ⚠️ ' + T('re-verify') if m.stale else ''} · [{T('source')}]({m.source_url})")
            if r.alerts:
                st.error(T("{} open tariff alert(s) for this code: see the Tariff monitor tab.", len(r.alerts)))
            st.markdown(f"**{T('Check live before filing')}:** " + " · ".join(f"[{k}]({v})" for k, v in r.links.items()))
            with st.expander(T("Retrieved candidates (RAG) and alternatives")):
                st.dataframe(pd.DataFrame([c.model_dump() for c in r.candidates]), hide_index=True)
                st.write(T("Alternatives considered by the model:"), ", ".join(r.alternatives) or "-")
            st.caption(f"{T('Mode')}: {r.mode} · {T('model')}: {r.model} · {T('knowledge base')} {r.kb_version} · {r.tariff_data_as_of}")
            if r.usage.get("calls"):
                st.caption(T("AI use for this check: {} calls · {} tokens · about ${}", r.usage["calls"],
                             r.usage["prompt_tokens"] + r.usage["completion_tokens"], f"{r.usage['est_cost_usd']:.5f}"))

            st.markdown("#### " + T("3 · Your decision"))
            d1, d2 = st.columns([1, 1])
            dec_opts = ["approved", "corrected", "rejected"]
            decision = d1.radio(T("Decision"), dec_opts, horizontal=True, format_func=T, key="decision_" + L,
                                index=dec_opts.index(st.session_state.get("decision_val", "approved")))
            st.session_state["decision_val"] = decision
            final_hs = d2.text_input(T("Final HS code"), r.hs_code if decision == "approved" else "")
            comment = st.text_input(T("Comment (why?)"), "", key="comment")
            shp = st.session_state.get("shipment")
            add_master = st.checkbox(T("Add to the master list (links the part number to the product)"),
                                     value=bool(shp and shp.part_number), key="add_master")
            b1, b2 = st.columns(2)
            if b1.button(T("Save decision"), width="stretch"):
                if decision == "corrected" and not final_hs:
                    st.warning(T("Please enter the corrected HS code."))
                else:
                    report.log_decision(r, decision, final_hs, comment=comment)
                    st.success(T("Saved to the decision log (audit trail)."))
                    if add_master and decision != "rejected" and final_hs and shp:
                        pid = (r.master or {}).get("product", {}) or {}
                        prod = master_list.approve(r.original_description or shp.description, final_hs, part_number=shp.part_number,
                                                   approved_by="reviewer",
                                                   product_id=pid.get("product_id", "") if (r.master or {}).get("kind") != "similar" else "")
                        st.success(T("Master list updated: product {}.", prod.product_id))
            b2.download_button(T("Download review pack for the broker"), report.review_pack(r, decision, final_hs, comment),
                               file_name=f"klarschiff_{r.shipment_id}_review_pack.md", width="stretch")
            st.caption(T(r.disclaimer))

# ---------------------------------------------------------------- BATCH
with tab_batch:
    st.subheader(T("Batch check"))
    st.write(T("Check many shipments at once and download one report. Columns: shipment_id, description, origin, "
               "destination, part_number, documents_provided (separated by ;), intended_use · example: "
               "mvp/sample_data/batch_sample.csv"))
    bup = st.file_uploader(T("Shipments CSV"), type=["csv"], key="batch_csv")
    if bup and st.button(T("Run the batch check"), type="primary"):
        with st.spinner(T("Checking documents, rules and tariffs…")):
            st.session_state["batch"] = batch.run_csv(bup.getvalue().decode("utf-8-sig"))
    if st.session_state.get("batch"):
        rows, summ = st.session_state["batch"]
        b1, b2, b3, b4 = st.columns(4)
        b1.metric(T("Shipments"), summ["shipments"])
        b2.metric(T("To review"), summ["to_review"])
        b3.metric(T("Master-list hits"), summ["master_list_hits"])
        b4.metric(T("AI cost (estimate)"), f"${summ['est_cost_usd_total']:.4f}")
        st.caption(T("Per line: about ${} · categories 1/2/3: {} / {} / {} · {} s", f"{summ['est_cost_usd_per_line']:.5f}",
                     summ["by_category"][1], summ["by_category"][2], summ["by_category"][3], summ["seconds"]))
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        st.download_button(T("Download report (CSV)"), batch.to_csv(rows), file_name="klarschiff_batch_report.csv")

# ---------------------------------------------------------------- MASTER LIST
with tab_master:
    st.subheader(T("Master list (Produktstamm)"))
    st.write(T("Part numbers change, the product stays. Each product keeps ONE approved HS code and ONE approved German "
               "description; part numbers are linked to it. A new part number with the same description reuses the code, "
               "and a person confirms."))
    products = master_list.load()
    m1, m2, m3 = st.columns(3)
    m1.metric(T("Products"), len(products))
    m2.metric(T("Part numbers"), sum(len(p.part_numbers) for p in products))
    m3.metric(T("Without HS code (conflicts)"), sum(1 for p in products if not p.hs_code))
    with st.expander(T("Import the client's list (CSV)"), expanded=not products or bool(st.session_state.get("ml_report"))):
        st.caption(T("Columns: part_number, description, description_de, hs_code · example: mvp/sample_data/master_list_sample.csv · "
                     "importing replaces the current list"))
        up = st.file_uploader(T("Master list CSV"), type=["csv"], key="ml_csv")
        if up and st.button(T("Import and check the list"), type="primary"):
            st.session_state["ml_report"] = master_list.import_csv(up.getvalue().decode("utf-8-sig"))
            st.rerun()  # refresh the counters above
        rep = st.session_state.get("ml_report")
        if rep:
            st.success(T("{} rows → {} products · {} part numbers merged · {} conflict(s)", rep["rows"], rep["products"],
                         rep["merged_part_numbers"], len(rep["conflicts"])))
            for c in rep["conflicts"]:
                st.error(T("Same product, different HS codes: {} ({}), part numbers {}: a person decides.",
                           c["description"], " / ".join(c["hs_codes"]), ", ".join(c["part_numbers"])))
    if products:
        st.dataframe(pd.DataFrame([{"ID": p.product_id, "HS": p.hs_code or "⚠️", T("Description"): p.description,
                                    T("German description"): p.description_de, T("Part numbers"): ", ".join(p.part_numbers)}
                                   for p in products]), hide_index=True, width="stretch")
        st.download_button(T("Download master list (CSV)"), master_list.to_csv(products), file_name="klarschiff_master_list.csv")
        st.markdown("#### " + T("Find a product"))
        f1, f2 = st.columns([1, 2])
        q_pn = f1.text_input(T("Part number"), key="q_pn")
        q_d = f2.text_input(T("Description"), key="q_d")
        if q_pn or q_d:
            mm = master_list.lookup(q_pn, q_d, products)
            if mm.product:
                kinds = {"part_number": "Known part number", "same_description": "New part number, same product",
                         "similar": "Similar product"}
                st.info(f"{T(kinds[mm.kind])} · {mm.product.product_id} · HS {mm.product.hs_code or '-'} · {mm.product.description}")
                for dff in mm.differences:
                    st.warning(dff)
            else:
                st.caption(T("No product found: the agent classifies it and, after approval, adds it to the list."))

    st.markdown("#### " + T("📚 Rulings library (EBTI / CROSS)"))
    st.caption(T("Add official rulings your team looked up (EU EBTI, US CROSS). The agent shows similar ones as evidence. "
                 "Columns: reference, source, code, description, issued, valid_until, url"))
    st.markdown("[EBTI](https://ec.europa.eu/taxation_customs/dds2/ebti/ebti_consultation.jsp?Lang=en) · "
                "[CROSS](https://rulings.cbp.gov/)")
    rl = st.file_uploader(T("Rulings CSV"), type=["csv"], key="rul_csv")
    if rl and st.button(T("Add rulings")):
        rep = precedents.import_csv(rl.getvalue().decode("utf-8-sig"))
        st.success(T("{} rulings added · {} in the library", rep["imported"], rep["total"]))
    st.caption(T("Rulings in the library: {}", len(precedents.load())))

# ---------------------------------------------------------------- MONITOR
with tab_monitor:
    st.subheader(T("Tariff & regulation monitor"))
    st.write(T("Tariffs change fast (US Section 232 and general surcharges; EU steel measure from 1 Jul 2026; CBAM from 1 Jan 2026). "
               "The monitor checks official sources and opens an **alert** when something changes. While an alert is open, "
               "affected shipments always go to a person."))
    st.caption(T("Last run: {}  ·  runs daily via GitHub Actions (.github/workflows/tariff_monitor.yml) or on demand here.", monitor.last_run()))
    if st.button(T("Run the monitor now")):
        with st.spinner(T("Checking the Federal Register, USITC HTS and EU pages…")):
            rep = monitor.run()
        st.success(T("{} new alert(s).", len(rep['new_alerts'])))
        for e in rep["errors"]:
            st.warning(T("Source not reachable: ") + e)
    alerts = monitor.load_alerts()
    open_a = [a for a in alerts if a["status"] == "open"]
    st.metric(T("Open alerts"), len(open_a))
    for a in open_a[:50]:
        with st.expander(f"🔔 {a['source']} · {a['title'][:110]}"):
            st.write(a.get("detail", ""))
            st.write(f"{T('Affects HS')}: {', '.join(a['affects_hs_prefixes']) or T('all')} · [{T('open source')}]({a['url']})")
            note = st.text_input(T("Review note"), key="n" + a["id"])
            if st.button(T("Mark as reviewed"), key="b" + a["id"]):
                monitor.mark_reviewed(a["id"], note)
                st.rerun()
    from klarschiff.rules import load_measures
    st.markdown("#### " + T("Rules in force (versioned)"))
    st.dataframe(pd.DataFrame([{T("Measure"): m["name"], T("Legal reference"): m["legal_ref"], T("From"): m["effective_from"],
                                T("Volatility"): m["volatility"], T("Re-check every (days)"): m["review_every_days"],
                                T("Last verified"): m["last_verified"]} for m in load_measures()["measures"]]),
                 hide_index=True, width="stretch")

# ---------------------------------------------------------------- LOG
with tab_log:
    st.subheader(T("Decisions and quality metrics"))
    stats = report.override_rate()
    c1, c2 = st.columns(2)
    c1.metric(T("Decisions logged"), stats["decisions"])
    c2.metric(T("Override rate (team level)"), "-" if stats["override_rate"] is None else f"{stats['override_rate']:.0%}")
    st.caption(T("A very low override rate over time can mean automation bias (people stop checking). "
                 "Measured per team, not per person (works-council rules in Germany, §87 BetrVG)."))
    if report.LOG.exists():
        st.dataframe(pd.read_csv(report.LOG), hide_index=True, width="stretch")

# ---------------------------------------------------------------- ABOUT
with tab_about:
    st.markdown(ABOUT[L])
