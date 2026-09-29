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
- All interface texts live in `mvp/i18n.py`; `tests/test_i18n.py` fails if a text has no German version.
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
