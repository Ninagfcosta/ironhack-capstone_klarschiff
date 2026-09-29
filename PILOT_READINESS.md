# KlarSchiff v2.2: pilot readiness

Version 2.1 is the one presented on 10 October (branch `main`). Version 2.2 (branch `v2.2-pro`) adds what a real
pilot at a German importer needs. Same agent, same rules, same review triggers; 24 offline tests pass.

| Gap (from the professional review) | What v2.2 adds | Where |
|---|---|---|
| Documents arrive as scans and phone photos | The Intake step reads scanned PDFs and photos with a vision model; says what it could **not** read; unreadable parts → a person | `klarschiff/vision.py`, app upload "Scan or photo" |
| Invoices in Turkish or Chinese | Language check; translation to English before classifying; original shown next to the translation; translated shipments → a person | `klarschiff/language.py` |
| German clients do not want data to leave the EU | Provider switch in one place: OpenAI or any OpenAI-compatible EU provider (e.g. Mistral AI) | `klarschiff/llm.py`, `.env.example` |
| A demo app is not a production service | Password login and a daily monitor; hosting on an EU server is planned for the pilot (with the client's IT) | app login, `.github/workflows/tariff_monitor.yml` |
| Our tests are optimistic (E6) | Blind-test runner for broker-labelled real shipments, with the go / no-go rule | `evaluation/blind_test.py`, `evaluation/blind_test_template.csv` |
| "Not stated" documents | Option "this list is complete": every required document not listed counts as missing | App checkbox, `Shipment.documents_list_complete` |

## Try it

```bash
git checkout v2.2-pro
pip install -r requirements.txt
streamlit run mvp/app.py                              # upload mvp/sample_data/scan_invoice_TR.jpg (fictional Turkish invoice)
python evaluation/blind_test.py evaluation/blind_test_template.csv
```

## Still not code (and more important than code)

1. A licensed customs broker as pilot partner (labels the blind test, reviews the rules quarterly).
2. Real, anonymised shipments from the client.
3. Company form, terms with limitation of liability, professional indemnity insurance.
4. Data-processing agreements with the model provider, LangSmith and the hosting company.


## Interface language
English by default, German with one click (`mvp/i18n.py`). German users see German labels, reasons and disclaimer; legal names stay as in the regulation.

## v2.3: any product + master list

| Before (v2.2) | Now (v2.3) |
|---|---|
| 50 construction headings | Full HS 2022 (5,613 subheadings) + 50 reviewed headings on top |
| Construction rules only | Rule packs: CE (machinery, electrical/radio + WEEE, batteries), export control (EU dual-use, US EAR), food/plants, EUDR (upcoming), CBAM full scope, trade defence |
| Lookup by description only | Master list: product ID with many part numbers; conflicts found on import |

**Honest limits:** retrieval over 5,613 short texts is harder than over 50 curated headings (offline keyword baseline on the
17 universal cases: 0.75 exact codes, see `evaluation/results/offline-baseline-universal.json`). Every code that is not
reviewed goes to a person, so trust grows product family by product family (the pilot starts with one family).
