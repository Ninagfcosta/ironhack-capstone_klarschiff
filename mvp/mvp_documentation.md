# MVP documentation: KlarSchiff app

A small web app (Streamlit) where a logistics employee checks a shipment before it leaves and records a decision.

## 1. What a user does (2 minutes)

1. Paste the goods description from the invoice (or load an example, upload invoice/packing-list CSVs, a text PDF or an e-invoice XML).
2. Set origin, destination and the documents already available.
3. Click **Check shipment**.
4. Read the result: HS code, confidence, category, **documents table (provided / missing / not stated)**, trade measures with legal references and source links, invoice-vs-packing-list issues, and the reasons for manual review.
5. Decide: **approve, correct or reject**, add a comment, save. Download the **review pack** for the customs broker.

A second tab shows the **tariff monitor** (open alerts, rules in force with their verification dates). A third tab shows the decision log and the **override rate** (team level).

## 2. Screens

| Tab | Content |
|---|---|
| Check a shipment | Input form, result, decision, review-pack download |
| Tariff monitor | Run the monitor, open alerts, mark as reviewed, versioned rule table |
| Decisions & metrics | Decision log (audit trail), override rate |
| How it works | The five steps and the limits, in plain language |

### Interface language (v2.2)
The app opens in **English**. The switch **🌐 Language / Sprache** (top right) changes every screen to **German** in one click,
because the pilot users are German customs, logistics and construction teams. Inputs and results stay on screen when switching.
- All interface texts live in `mvp/i18n.py` (English text → German text).
- The agent's review reasons are translated by pattern; anything unknown stays in English (never hidden).
- Not translated on purpose: legal names (CBAM, CE, DoP, TARIC), HS titles from the knowledge base, and the model's free-text reasoning (the app says so).

### Master list / Produktstamm (v2.3)
Problem in the fictional client scenario (I&E LLC): the product master list is keyed by the supplier's part number.
Part numbers change (revision, new supplier, new ERP) while the description stays the same, so the lookup finds nothing and
the approved HS code and German description are lost. People re-classify, and the same product can get different codes.
- Tab **📒 Master list**: import the client's CSV (`part_number, description, description_de, hs_code`). Rows with the same
  description become ONE product with several part numbers; **conflicts** (same description, different codes) are shown.
- In **Check a shipment**, enter the part number. Known part number → approved code reused. New part number, same
  description → code reused and a person confirms the link. Similar description → a person decides, with the differences
  (e.g. `m10x40 → m12x40`, `a2 → a4`).
- Saving a decision with "Add to the master list" links the part number to the product and writes the history.

## 3. Run it

```bash
pip install -r requirements.txt
cp .env.example .env    # add OPENAI_API_KEY (and LANGSMITH_API_KEY for traces)
streamlit run mvp/app.py
```

Without an OpenAI key the app still runs in **offline mode**: keyword match only, and every result goes to manual review. This keeps a demo working even without internet.

**Online (optional):** Streamlit Community Cloud → "New app" → this GitHub repository → main file `mvp/app.py` → add the keys under *Secrets*. Use only fictional or anonymised shipments on a public demo.

## 4. Error handling

| Situation | What the app does |
|---|---|
| No API key / API down / quota | Falls back to offline mode, confidence capped at 0.6, reason shown, manual review |
| LLM returns an invalid code | Format check lowers confidence to ≤ 0.4 → manual review |
| Scanned PDF without text | Clear message: "OCR is planned for the pilot; please type the description" |
| Empty description | Asks for a description, nothing is run |
| Any other error | Short message, no stack trace, nothing is saved |
| Monitor source unreachable | That source is skipped and listed; the others still run |

## 5. Data stored

`data/decision_log.csv` (shipment id, suggested and final code, decision, **team** not person, comment, model, knowledge-base version) and `data/alerts.json` / `data/monitor_state.json`. No invoice text is stored by the app. LangSmith traces contain the shipment description: use the EU LangSmith region and anonymised text in the pilot (see `compliance/gdpr_documentation.md`).

## 6. Demo script (video, 2-3 minutes)

1. TC04 precast wall panels, DoP missing → red "missing" row, manual review.
2. TC16 German invoice "Betonstahl in Ringen" → coiled rebar, CBAM + EU steel measure, Category 3.
3. TC17 OSB boards → invoice says 500, packing list 450 → mismatch.
4. TC15 kitchen sinks → out of scope, low confidence → the agent admits it and asks a person.
5. Tariff monitor tab → rules with dates, open alerts.
6. Approve TC04 after correction → decision log → download the review pack.

## 7. Known limits

v2.3: any product can be classified (full HS 2022), but only reviewed headings and master-list products pass without extra review; translations and scans always go to a person; rules must be re-verified by a licensed customs professional; duty rates are linked, not calculated.

## v2.4 (Oct 2026): pilot features, built with the course tools

| Need (from customs brokers and importers) | What the app does now | Course tool |
|---|---|---|
| Reviews get forgotten | **Review queue** tab: every orange result opens a ticket (owner, due date, status). Optional n8n workflow `n8n/review_queue_workflow.json`: Webhook → Set → Airtable → Telegram alert | n8n, Airtable, Telegram |
| Chasing missing documents | **Draft an e-mail to the supplier** (EN/DE) in the Documents tab. A person edits and sends it; nothing is sent automatically | OpenAI |
| Rules change, old codes go stale | **Re-check after a rule change** (Tariff monitor tab): approved products affected by an open alert | Python, monitor |
| Same product, different codes | **Search by meaning** in the master list (embeddings, local cache; Pinecone is the production option) | RAG, OpenAI embeddings |
| Proof of quality | **Weekly second look**: 10% random sample of approved decisions (Dashboard tab) and an optional **LLM-as-judge** (`python evaluation/run_eval.py --local --judge`) | LangSmith, LLM judges |
| Confidence is not yes/no | **Three bands**: high ≥ 0.90, medium ≥ 0.75, low < 0.75 (to calibrate in the pilot) | Python |
| Management wants numbers | **Dashboard**: open and overdue reviews, time to close, why shipments go to a person, decision log | Streamlit |
| Warehouse staff do not type | **Voice note** upload → Whisper transcript → checked like typed text | Whisper |
| New clients are a risk | **New client (first 30 days)** checkbox: every shipment goes to a person | Python |

Look: the app uses the presentation colours and the KlarSchiff mark (`.streamlit/config.toml`).

## v2.5 (Oct 2026): save time and money (expert review)

| Need | What the app does now | Course tool |
|---|---|---|
| Invoices repeat the same products | **Batch**: identical lines are checked once and the result is reused (no second AI call); master-list hits need no AI at all. The report shows "AI checks saved" | Python, master list |
| The agent should learn from people | **Learning loop**: every correction becomes a test case in `evaluation/dataset_learned.jsonl`; run `python evaluation/run_eval.py --local --dataset learned` (or `--langsmith`) | LangSmith datasets |
| Duty paid only because a proof is missing | **Money tip**: for partner countries (Türkiye A.TR, UK, CH, NO, JP, KR, CA) the app reminds the team to get the proof of preferential origin. Not a review trigger; a person checks the origin rules | Rules, Python |
| Brokers retype the data | **Download data for the broker (JSON)**: code, line, origin, destination, documents, measures, preference | Python (structured output) |
| ROI was illustrative | **Measured review time** (result on screen → decision saved) in the Dashboard | Streamlit |

## v2.6: three more savings (Oct 2026, same course tools)

| Improvement | Pilot need | How (course tools) | Saves |
|---|---|---|---|
| E-mail inbox (`klarschiff/inbox.py`, tab **Inbox**, `n8n/email_inbox_workflow.json`) | Documents arrive as e-mail attachments; downloading and re-typing takes time and causes mistakes | n8n: Gmail Trigger → save attachment + `.meta.json` (sender, subject, date) into `data/inbox/` → Telegram alert. In the app, **Check all** runs the agent on every file, opens review tickets and moves files to `data/inbox/done/`. Scanned PDFs are flagged for a person. Nothing is sent to the supplier. | Time (no copy-paste) |
| AI answer cache (`klarschiff/llm.py`) | Re-checks and repeated products ask the model the same question again | Identical requests (same model, prompt, temperature 0) are answered from `data/llm_cache.json`. Dashboard shows reused answers and the share of AI calls saved. Off with `KLARSCHIFF_LLM_CACHE=false`; `llm.clear_cache()` after a model or prompt change, then re-run the evaluation. | Money (fewer API calls) and speed |
| Ask KlarSchiff (`klarschiff/assistant.py`, tab **Ask KlarSchiff**, `n8n/telegram_assistant_workflow.json`) | The team interrupts the customs lead with the same small questions | RAG: BM25 search over the rule base, the master list and the origin table → GPT-4o-mini answers only from those sources, with citations, or says "I don't know". Prompt-injection guard blocks instruction-like questions. On Telegram: n8n AI Agent + OpenAI chat model + Airtable tool (master list). It informs; a person decides. | Expert time |

Tested offline (no key): 3 inbox files checked, 3 tickets opened, files moved to `done/`; cache: 3 requests → 2 API calls, 1 reused; assistant: correct sources for Türkiye origin proof, CBAM, construction products (German question), safety data sheet; "what is the weather" → "I don't know"; injection text → blocked.

### v2.6b fixes (4 Oct 2026)
- **E11 (found while checking the German screenshot):** "Leistungserklärung fehlt" was not flagged as a missing DoP, because the word pattern stopped in the middle of the word ("leistungserkl|ärung") and the word "fehlt" was not seen. Same for "CE marking missing" and "Mill certificate missing". Fix in `klarschiff/intake.py`: the check now reads to the end of the word. Re-tested: all five sentences correct; offline evaluation unchanged (no regressions).
- German app: the money tip and the document names in the review reasons are now in German (`klarschiff/preference.py`, `mvp/i18n.py`).
