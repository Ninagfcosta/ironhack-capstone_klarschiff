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
import time  # noqa: E402

from klarschiff import agent, batch, config, intake, master_list, monitor, precedents, report, tariff_lines, vision  # noqa: E402
from klarschiff import quality, recheck, review_queue, semantic_search, supplier_request, voice  # noqa: E402
from klarschiff import assistant, broker_export, inbox, learning, llm, preference  # noqa: E402
from klarschiff.intake import DOC_PATTERNS  # noqa: E402
from klarschiff.models import Shipment  # noqa: E402

sys.path.insert(0, str(ROOT / "mvp"))
from i18n import ABOUT, LANGS, reason, t  # noqa: E402

# Brand colours (light theme, Oct 2026): white page, dark plum text, sunset orange accents, same logo as the presentation.
# CREAM = main text colour and logo square; INK = the check inside the logo.
INK, CREAM, MUTED, CARD, LINE = "#FFF4EA", "#1E1433", "#5E5470", "#FAF7FC", "#E4DAEE"
ORANGE, AMBER, CORAL, GREEN, VIOLET = "#E8622C", "#F2A93B", "#E5484D", "#1F9D6B", "#8E5BD6"
st.set_page_config(page_title="KlarSchiff · Pre-shipment co-pilot", page_icon="✅", layout="wide")
st.markdown(f"""<style>
.ks-bar {{height:6px;border-radius:6px;background:linear-gradient(90deg,{AMBER},{ORANGE},{CORAL},{VIOLET});margin:6px 0 14px 0}}
.ks-pill {{display:inline-block;border:1px solid {LINE};background:{CARD};color:{CREAM};border-radius:999px;padding:3px 12px;margin:2px 6px 2px 0;font-size:.85rem}}
.ks-card {{border:1px solid {LINE};border-radius:14px;padding:14px 16px;background:{CARD};min-height:150px}}
.ks-label {{color:{MUTED};font-size:.8rem;text-transform:uppercase;letter-spacing:.08em}}
.ks-big {{font-size:2rem;font-weight:800;color:{CREAM};line-height:1.15}}
.ks-small {{color:{MUTED};font-size:.85rem}}
.ks-ok {{background:#EAF7F0;border:1px solid #BFE6D2;border-left:8px solid {GREEN};padding:14px 18px;border-radius:12px;color:{CREAM}}}
.ks-warn {{background:#FFF1E8;border:1px solid #F6CDB2;border-left:8px solid {ORANGE};padding:14px 18px;border-radius:12px;color:{CREAM}}}
.ks-verdict {{font-size:1.35rem;font-weight:800}}
.ks-step {{border:1px solid {LINE};border-radius:12px;padding:10px 10px;background:{CARD};text-align:center;min-height:104px}}
.ks-step b {{display:block;color:{CREAM}}}
.ks-track {{height:10px;border-radius:6px;background:#ECE6F2;position:relative;margin-top:8px}}
.ks-fill {{height:10px;border-radius:6px}}
.ks-mark {{position:absolute;top:-4px;width:2px;height:18px;background:{CREAM}}}
</style>""", unsafe_allow_html=True)
# KlarSchiff mark (same as the presentation): a check (shipment cleared) above an orange route line
LOGO = (f'<svg width="60" height="60" viewBox="0 0 120 120" aria-label="KlarSchiff logo">'
        f'<rect width="120" height="120" rx="28" fill="{CREAM}"/>'
        f'<path d="M30 58 L52 80 L92 34" fill="none" stroke="{INK}" stroke-width="13" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<path d="M28 98 H92" stroke="#E8622C" stroke-width="7" stroke-linecap="round"/></svg>')
def short(text, n=70):
    """Shorten a long title at a word boundary."""
    return text if len(text) <= n else text[:n].rsplit(" ", 1)[0] + " …"


CATEGORY = {1: "Standard goods", 2: "CE-marked product", 3: "Trade measures or controls"}

# ---------------------------------------------------------------- LANGUAGE (English default, German on one click)
head, switch = st.columns([5, 1])
with switch:
    L = st.radio("🌐 Language / Sprache", list(LANGS), format_func=LANGS.get, horizontal=True, key="lang")
T = lambda text, *a: t(text, L, *a)  # noqa: E731
head.markdown(f'<div style="display:flex;align-items:center;gap:14px">{LOGO}'
              f'<div><div style="font-size:42px;font-weight:800;color:{CREAM};line-height:1.05">Klar<span style="color:{ORANGE}">Schiff</span></div>'
              f'<div style="color:{MUTED};margin-top:2px">{T("AI pre-shipment co-pilot · HS code suggestion, document check and tariff monitor")}'
              f' · <b style="color:{CREAM}">{T("Clear answers. Human decisions.")}</b></div></div></div>', unsafe_allow_html=True)
head.markdown('<div class="ks-bar"></div>' + "".join(f'<span class="ks-pill">{T(x)}</span>' for x in
              ["Suggests the customs code", "Checks the documents", "Applies official rules", "You decide"]),
              unsafe_allow_html=True)

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

tab_check, tab_inbox, tab_queue, tab_batch, tab_master, tab_ask, tab_monitor, tab_log, tab_about = st.tabs(
    [T(x) for x in ["🔎 Check a shipment", "📥 Inbox", "📋 Review queue", "📦 Batch", "📒 Master list", "💬 Ask KlarSchiff",
                    "📡 Tariff monitor", "📊 Dashboard", "ℹ️ How it works"]])

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
        new_client = st.checkbox(T("New client (first 30 days): a person reviews every shipment"), value=False, key="new_client")
        with st.expander(T("Optional: invoice, packing list, PDF, scan, photo or e-invoice")):
            inv_csv = st.file_uploader(T("Invoice lines (CSV)"), type=["csv"], key="inv")
            pk_csv = st.file_uploader(T("Packing list lines (CSV)"), type=["csv"], key="pk")
            pdf = st.file_uploader(T("Invoice PDF (text or scanned)"), type=["pdf"], key="pdf")
            photo = st.file_uploader(T("Scan or photo of the invoice (JPG / PNG)"), type=["png", "jpg", "jpeg"], key="photo")
            xml = st.file_uploader(T("E-invoice (XRechnung / ZUGFeRD XML)"), type=["xml"], key="xml")
            audio = st.file_uploader(T("Voice note from the warehouse (MP3 / M4A / WAV)"), type=["mp3", "m4a", "wav"], key="audio")
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
            if audio:
                with st.spinner(T("Turning the voice note into text…")):
                    spoken = voice.transcribe(audio.getvalue(), audio.name)
                st.session_state["voice_text"] = spoken
                text = (text + "\n" + spoken).strip()
            if xml:
                inv = intake.lines_from_einvoice(xml.getvalue())
                text = (text + "\n" + "; ".join(l.description for l in inv)).strip()
            if len(text.strip()) < 5:
                st.warning(T("Please describe the goods first."))
                st.stop()
            s = Shipment(shipment_id=(sample.split(" ·")[0] if SAMPLES[sample] else "manual"), description=text,
                         origin=origin, destination=dest, intended_use=use, documents_provided=docs,
                         invoice_lines=inv, packing_lines=pk, documents_list_complete=complete, legible=legible, unreadable_parts=unreadable, source=source,
                         part_number=part_no, new_client=new_client)
            st.session_state["shipment"] = s
            with st.spinner(T("Checking documents, rules and tariffs…")):
                st.session_state["result"] = agent.run(s)
            res = st.session_state["result"]
            st.session_state["ticket"] = review_queue.add(res, text) if res.manual_review else None
            st.session_state["shown_at"] = time.time()  # to measure the real review time
            st.session_state.pop("supplier_draft", None)
        except (ValueError, RuntimeError) as e:
            st.error(str(e))
        except Exception as e:  # never show a stack trace to the user
            st.error(T("Something went wrong ({}). The shipment was not checked; please try again or check it manually.", type(e).__name__))

    r = st.session_state.get("result")
    with right:
        st.subheader(T("2 · Suggestion"))
        if not r:
            st.markdown(f'<div class="ks-card"><b>{T("How the agent works")}</b><br>'
                        f'<span class="ks-small">{T("1 Intake → 2 Validate → 3 Recommend → 4 Rules → 5 You decide. The result appears here.")}</span></div>',
                        unsafe_allow_html=True)
        else:
            # --- the verdict: one clear sentence first
            if r.manual_review:
                items = "".join(f"<li>{reason(x, L)}</li>" for x in r.review_reasons)
                st.markdown(f'<div class="ks-warn"><div class="ks-verdict">🟠 {T("A person must review this shipment")}</div>'
                            f'<div class="ks-small">{T("{} reason(s):", len(r.review_reasons))}</div><ul style="margin:6px 0 0 0">{items}</ul></div>',
                            unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="ks-ok"><div class="ks-verdict">🟢 {T("All checks passed")}</div>'
                            f'<div>{T("A person still approves before filing.")}</div></div>', unsafe_allow_html=True)

            shp0 = st.session_state.get("shipment")
            tip = preference.tip(shp0, r.hs_code) if shp0 else None
            if tip:
                st.markdown(f'<div class="ks-card" style="min-height:0;border-left:8px solid {AMBER}"><b>💶 {T("Money tip")}</b><br>'
                            f'<span class="ks-small">{tip["message_de"] if L == "de" else tip["message"]}</span></div>', unsafe_allow_html=True)
            tk = st.session_state.get("ticket")
            if tk:
                st.caption(T("Review ticket {} opened · due {} · see the Review queue tab", tk["id"], tk["due"]))
            if st.session_state.get("voice_text"):
                st.caption(T("Voice note") + ": " + st.session_state["voice_text"])
            # --- the agent's steps, made visible
            missing = [d for d in r.required_documents if d.status == "missing" and d.mandatory]
            unknown = [d for d in r.required_documents if d.status == "not stated" and d.mandatory]
            low = r.confidence < config.CONFIDENCE_THRESHOLD
            steps = [("1 · Intake", "✅", T("translated") if r.translated_description else T("read")),
                     ("2 · Validate", "⚠️" if r.validation_issues else "✅", T("{} issue(s)", len(r.validation_issues))),
                     ("3 · Recommend", "⚠️" if low else "✅", f"HS {r.hs_code}"),
                     ("4 · Rules", "⚠️" if (missing or unknown) else "✅",
                      T("{} missing", len(missing)) if missing else (T("{} to confirm", len(unknown)) if unknown else T("documents OK"))),
                     ("5 · You decide", "👤", T("waiting for you"))]
            st.write("")
            for col, (name, icon, sub) in zip(st.columns(5), steps):
                col.markdown(f'<div class="ks-step"><span style="font-size:1.3rem">{icon}</span><b>{T(name)}</b>'
                             f'<span class="ks-small">{sub}</span></div>', unsafe_allow_html=True)

            # --- three key numbers
            st.write("")
            k1, k2, k3 = st.columns(3)
            k1.markdown(f'<div class="ks-card"><div class="ks-label">{T("HS code")}</div><div class="ks-big">{r.hs_code}</div>'
                        f'<div class="ks-small">{short(r.hs_title)}</div></div>', unsafe_allow_html=True)
            pct, thr = r.confidence, config.CONFIDENCE_THRESHOLD
            colour = GREEN if pct >= thr else ORANGE
            k2.markdown(f'<div class="ks-card"><div class="ks-label">{T("Confidence")}</div><div class="ks-big">{pct:.0%}</div>'
                        f'<div class="ks-track"><div class="ks-fill" style="width:{pct*100:.0f}%;background:{colour}"></div>'
                        f'<div class="ks-mark" style="left:{thr*100:.0f}%"></div></div>'
                        f'<div class="ks-small">{T("Band: {}", T(r.confidence_band or "-"))} · {T("below {:.0%}: a person reviews", thr)}</div></div>', unsafe_allow_html=True)
            k3.markdown(f'<div class="ks-card"><div class="ks-label">{T("Category")}</div><div class="ks-big">{r.category} / 3</div>'
                        f'<div class="ks-small">{T(CATEGORY.get(r.category, ""))}</div></div>', unsafe_allow_html=True)
            st.write("")

            # --- details in tabs: short screen, nothing hidden
            tw, tdoc, trule, tsrc = st.tabs([T("💬 Why"), T("📄 Documents"), T("⚖️ Rules"), T("🔗 Sources & data")])
            with tw:
                st.markdown(f"**{r.hs_title}**")
                st.markdown(f"**{T('Why')}:** {r.reasoning}")
                if L == "de":
                    st.caption(T("The AI model writes its reasoning in English."))
                if r.evidence:
                    st.markdown(f"**{T('Evidence')}:** " + ", ".join(f"`{e}`" for e in r.evidence))
                for cr in r.category_reasons:
                    st.caption("• " + reason(cr, L))
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
                if r.precedents:
                    with st.expander(T("📚 Similar official rulings in your library ({})", len(r.precedents))):
                        for pr in r.precedents:
                            badge = "✅" if pr.get("valid") else "⌛ " + T("expired")
                            st.markdown(f"- **{pr['reference']}** ({pr['source']}) · HS {pr['code']} · {badge}: {pr['description'][:160]}")
            with tdoc:
                status = {"provided": "✅ provided", "missing": "❌ missing", "not stated": "❔ not stated"}
                st.dataframe(pd.DataFrame([{T("Document"): d.name, T("Type"): T("required" if d.mandatory else "recommended"),
                                            T("Status"): T(status[d.status]), T("Legal basis"): d.legal_ref} for d in r.required_documents]),
                             hide_index=True, width="stretch")
                if supplier_request.missing_items(r):
                    if st.button(T("✉️ Draft an e-mail to the supplier"), key="draft_btn"):
                        st.session_state["supplier_draft"] = supplier_request.draft(r, L)
                    dr = st.session_state.get("supplier_draft")
                    if dr:
                        st.caption(T("Draft only: a person reads, edits and sends it. Nothing is sent automatically."))
                        subj = st.text_input(T("Subject"), dr["subject"], key="draft_subj")
                        body = st.text_area(T("Message"), dr["body"], height=230, key="draft_body")
                        st.download_button(T("Download the draft (.txt)"), f"{subj}\n\n{body}", file_name=f"request_{r.shipment_id}.txt")
                if r.validation_issues:
                    st.markdown("#### " + T("Invoice vs packing list"))
                    for i in r.validation_issues:
                        st.markdown(f"- **{i.field}** ({i.severity}): {i.detail}")
            with trule:
                if r.measures:
                    for m in r.measures:
                        icon = "⏳" if m.upcoming else ("🔴" if m.volatility in ("high", "very high") else "🟡")
                        label = f"{icon} {m.name}" + (f" · {T('from')} {m.effective_from}" if m.upcoming else "")
                        with st.expander(label):
                            st.write(m.effect)
                            st.caption(f"{m.legal_ref} · {T('verified')} {m.last_verified}{' · ⚠️ ' + T('re-verify') if m.stale else ''} · [{T('source')}]({m.source_url})")
                else:
                    st.caption(T("No special trade measures for this code."))
                if r.alerts:
                    st.error(T("{} open tariff alert(s) for this code: see the Tariff monitor tab.", len(r.alerts)))
                if r.national:
                    nat = r.national
                    with st.expander(T("🔢 Full code ({})", nat["system"]) + (f": {nat['suggested']}" if nat.get("suggested") else ""),
                                     expanded=True):
                        if nat.get("suggested"):
                            st.caption(T("Suggested by word match; a person confirms the line."))
                        else:
                            st.caption(T("Several lines fit: a person chooses."))
                        st.dataframe(pd.DataFrame(nat["lines"]), hide_index=True, width="stretch")
            with tsrc:
                st.markdown(f"**{T('Check live before filing')}:** " + " · ".join(f"[{k}]({v})" for k, v in r.links.items()))
                with st.expander(T("Retrieved candidates (RAG) and alternatives")):
                    st.dataframe(pd.DataFrame([c.model_dump() for c in r.candidates]), hide_index=True)
                    st.write(T("Alternatives considered by the model:"), ", ".join(r.alternatives) or "-")
                st.caption(f"{T('Mode')}: {r.mode} · {T('model')}: {r.model} · {T('knowledge base')} {r.kb_version} · {r.tariff_data_as_of}")
                if r.usage.get("calls"):
                    st.caption(T("AI use for this check: {} calls · {} tokens · about ${}", r.usage["calls"],
                                 r.usage["prompt_tokens"] + r.usage["completion_tokens"], f"{r.usage['est_cost_usd']:.5f}"))

            st.markdown("#### " + T("3 · Your decision"))
            st.caption(T("The agent suggests. You approve, correct or reject. Every decision is logged."))
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
                    if st.session_state.get("shown_at"):
                        quality.log_review_time(time.time() - st.session_state.pop("shown_at"), decision)
                    if decision == "corrected" and shp and learning.record_correction(shp, r.hs_code, final_hs, comment):
                        st.success(T("The correction is now a test case: the next evaluation checks it."))
                    if add_master and decision != "rejected" and final_hs and shp:
                        pid = (r.master or {}).get("product", {}) or {}
                        prod = master_list.approve(r.original_description or shp.description, final_hs, part_number=shp.part_number,
                                                   approved_by="reviewer",
                                                   product_id=pid.get("product_id", "") if (r.master or {}).get("kind") != "similar" else "")
                        st.success(T("Master list updated: product {}.", prod.product_id))
            b2.download_button(T("Download review pack for the broker"), report.review_pack(r, decision, final_hs, comment),
                               file_name=f"klarschiff_{r.shipment_id}_review_pack.md", width="stretch")
            if shp:
                b2.download_button(T("Download data for the broker (JSON)"), broker_export.to_json(r, shp, decision, final_hs),
                                   file_name=f"klarschiff_{r.shipment_id}_declaration_data.json", width="stretch")
            st.caption(T(r.disclaimer))

# ---------------------------------------------------------------- INBOX (v2.6)
with tab_inbox:
    st.subheader(T("E-mail inbox"))
    st.write(T("Supplier e-mails with documents are saved here by n8n (n8n/email_inbox_workflow.json: Gmail → save "
               "attachment → Telegram). One click checks them all: no download, no copy-paste. Nothing is sent to the supplier."))
    waiting = inbox.pending()
    i1, i2 = st.columns(2)
    i1.metric(T("Waiting in the inbox"), len(waiting))
    i2.metric(T("Checked from e-mail"), len(inbox.history(10_000)))
    st.caption(T("Inbox folder: {}", str(inbox.folder())))
    for f in waiting[:20]:
        st.markdown(f"- 📎 `{f.name}`")
    if waiting and st.button(T("Check all"), type="primary"):
        with st.spinner(T("Checking documents, rules and tariffs…")):
            st.session_state["inbox_rows"] = inbox.check_all()
        st.rerun()
    hist = inbox.history()
    if hist:
        st.markdown("#### " + T("Last checked"))
        st.dataframe(pd.DataFrame([{T("File"): h["file"], T("From"): h["from"], "HS": h["hs_code"], T("Category"): h["category"],
                                    T("Needs a person"): T("yes") if h["manual_review"] else T("no"),
                                    T("Missing documents"): " | ".join(h["missing_documents"]), T("Ticket"): h["ticket"]}
                                   for h in hist]), hide_index=True, width="stretch")
    elif not waiting:
        st.caption(T("The inbox is empty. Test it: put a fictional invoice (PDF, CSV, XML or TXT) into the inbox folder."))

# ---------------------------------------------------------------- REVIEW QUEUE
with tab_queue:
    st.subheader(T("Review queue"))
    st.write(T("Every shipment that needs a person gets a ticket with an owner and a due date, so nothing is forgotten. "
               "Optional: an n8n workflow (n8n/review_queue_workflow.json) copies each ticket to Airtable and alerts the team on Telegram."))
    qs = review_queue.stats()
    q1, q2, q3 = st.columns(3)
    q1.metric(T("Open"), qs["open"])
    q2.metric(T("Overdue"), qs["overdue"])
    q3.metric(T("Average time to close (hours)"), "-" if qs["avg_hours_to_close"] is None else qs["avg_hours_to_close"])
    st.caption(T("n8n alerts: on") if review_queue.WEBHOOK else T("n8n alerts: off (set KLARSCHIFF_N8N_WEBHOOK in .env to turn them on)"))
    tickets = review_queue.load()
    open_t = [x for x in tickets if x["status"] != "done"]
    for x in open_t[::-1][:30]:
        with st.expander(f"{x['id']} · {x['shipment_id']} · HS {x['hs_code']} · {T('due')} {x['due']}"):
            for rr in x["reasons"]:
                st.markdown(f"- {reason(rr, L)}")
            o1, o2, o3 = st.columns([2, 1, 1])
            owner = o1.text_input(T("Owner (team or role)"), x["owner"], key="own" + x["id"])
            if o2.button(T("Save owner"), key="so" + x["id"]):
                review_queue.update(x["id"], owner=owner)
                st.rerun()
            if o3.button(T("Mark as done"), key="done" + x["id"]):
                review_queue.update(x["id"], status="done")
                st.rerun()
    if tickets:
        st.download_button(T("Download the queue (JSON)"), json.dumps(tickets, indent=1, ensure_ascii=False),
                           file_name="klarschiff_review_queue.json")

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
        c1, c2, c3 = st.columns(3)
        c1.metric(T("Repeated lines reused"), summ["reused_results"])
        c2.metric(T("AI checks saved"), summ["ai_checks_saved"])
        c3.metric(T("Money tips"), summ["money_tips"])
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

    st.markdown("#### " + T("🔍 Search by meaning"))
    st.caption(T("Finds the same product even when it is written differently (also German). Uses embeddings when an AI key is set."))
    sq = st.text_input(T("Describe the product"), key="sem_q", placeholder="Steinwolle-Platte 100 mm")
    if sq:
        hits = semantic_search.search(sq)
        if hits:
            st.dataframe(pd.DataFrame(hits), hide_index=True, width="stretch")
        else:
            st.caption(T("The master list is empty: import it above first."))

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

# ---------------------------------------------------------------- ASK (v2.6)
with tab_ask:
    st.subheader(T("Ask KlarSchiff"))
    st.write(T("Quick questions about rules, documents and approved products, answered only from KlarSchiff's own "
               "knowledge, with sources. It informs; a person decides. The same assistant can run on Telegram "
               "(n8n/telegram_assistant_workflow.json)."))
    examples = ["Which proof of origin do I need for goods from Turkey?", "What does CBAM mean for steel?",
                "Do I need a safety data sheet for chemicals?"]
    ex = st.selectbox(T("Example questions"), [""] + examples, format_func=lambda x: x or T("(write your own)"), key="ask_ex")
    qtext = st.text_input(T("Your question"), ex, key="ask_q_" + (ex or "own"))
    if st.button(T("Ask"), type="primary") and qtext.strip():
        with st.spinner(T("Searching the KlarSchiff knowledge…")):
            st.session_state["ask"] = assistant.answer(qtext)
    a = st.session_state.get("ask")
    if a:
        st.markdown(f'<div class="ks-card" style="min-height:0">{a["answer"]}</div>', unsafe_allow_html=True)
        st.caption(T("Mode: {}", a["mode"]))
        for i, src in enumerate(a["sources"], 1):
            link = f"[{src['source']}]({src['source']})" if str(src["source"]).startswith("http") else src["source"]
            st.markdown(f"**[{i}]** {src['kind']} · {src['title']} · {link}")

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
    st.markdown("#### " + T("🔁 Re-check after a rule change"))
    st.caption(T("Lists the approved products in the master list whose HS code is affected by an open alert, so a person reviews them."))
    if st.button(T("Find affected products")):
        st.session_state["affected"] = recheck.affected_products()
    aff = st.session_state.get("affected")
    if aff is not None:
        if aff:
            st.dataframe(pd.DataFrame(aff), hide_index=True, width="stretch")
            st.download_button(T("Download for the batch check (CSV)"), pd.DataFrame(aff).to_csv(index=False),
                               file_name="klarschiff_recheck.csv")
        else:
            st.success(T("No approved product is affected by an open alert."))
    from klarschiff.rules import load_measures
    st.markdown("#### " + T("Rules in force (versioned)"))
    st.dataframe(pd.DataFrame([{T("Measure"): m["name"], T("Legal reference"): m["legal_ref"], T("From"): m["effective_from"],
                                T("Volatility"): m["volatility"], T("Re-check every (days)"): m["review_every_days"],
                                T("Last verified"): m["last_verified"]} for m in load_measures()["measures"]]),
                 hide_index=True, width="stretch")

# ---------------------------------------------------------------- LOG
with tab_log:
    st.subheader(T("Dashboard: decisions and quality"))
    stats = report.override_rate()
    c1, c2 = st.columns(2)
    c1.metric(T("Decisions logged"), stats["decisions"])
    c2.metric(T("Override rate (team level)"), "-" if stats["override_rate"] is None else f"{stats['override_rate']:.0%}")
    st.caption(T("A very low override rate over time can mean automation bias (people stop checking). "
                 "Measured per team, not per person (works-council rules in Germany, §87 BetrVG)."))
    sm = quality.summary()
    d1, d2, d3 = st.columns(3)
    d1.metric(T("Open reviews"), sm["queue"]["open"])
    d2.metric(T("Overdue reviews"), sm["queue"]["overdue"])
    d3.metric(T("Average time to close (hours)"), "-" if sm["queue"]["avg_hours_to_close"] is None else sm["queue"]["avg_hours_to_close"])
    e1, e2 = st.columns(2)
    e1.metric(T("Median review time (minutes, measured)"), "-" if sm["median_review_minutes"] is None else sm["median_review_minutes"])
    e2.metric(T("Corrections turned into test cases"), sm["learned_cases"])
    cs = llm.cache_stats()
    f1, f2 = st.columns(2)
    f1.metric(T("AI answers reused from the cache"), cs["hits"])
    f2.metric(T("Share of AI calls saved"), "-" if cs["saved_share"] is None else f"{cs['saved_share']:.0%}")
    st.caption(T("Measured review time replaces the illustrative ROI numbers during the pilot."))
    if sm["top_reasons"]:
        st.markdown("#### " + T("Why shipments go to a person"))
        st.bar_chart(pd.DataFrame(sm["top_reasons"], columns=[T("Reason"), T("Count")]).set_index(T("Reason")), horizontal=True)
    st.markdown("#### " + T("Weekly second look (5–10% sample)"))
    st.caption(T("A second person re-checks a random sample of last week's approved decisions. The broker stays responsible."))
    if st.button(T("Draw this week's sample (10%)")):
        st.session_state["sample_rows"] = quality.weekly_sample(0.1)
    srows = st.session_state.get("sample_rows")
    if srows is not None:
        if srows:
            st.dataframe(pd.DataFrame(srows), hide_index=True, width="stretch")
            st.download_button(T("Download the sample (CSV)"), pd.DataFrame(srows).to_csv(index=False), file_name="klarschiff_weekly_sample.csv")
        else:
            st.caption(T("No approved decisions in the last 7 days."))
    if report.LOG.exists():
        st.markdown("#### " + T("Decision log"))
        st.dataframe(pd.read_csv(report.LOG), hide_index=True, width="stretch")

# ---------------------------------------------------------------- ABOUT
with tab_about:
    st.markdown(ABOUT[L])
