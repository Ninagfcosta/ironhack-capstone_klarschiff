# KlarSchiff v2.2: pilot readiness

Version 2.1 is the one presented on 10 October (branch `main`). Version 2.2 (branch `v2.2-pro`) adds what a real
pilot at a German importer needs. Same agent, same rules, same review triggers; 24 offline tests pass.

| Gap (from the professional review) | What v2.2 adds | Where |
|---|---|---|
| Documents arrive as scans and phone photos | The Intake step reads scanned PDFs and photos with a vision model; says what it could **not** read; unreadable parts → a person | `klarschiff/vision.py`, app upload "Scan or photo" |
| Invoices in Turkish or Chinese | Language check; translation to English before classifying; original shown next to the translation; translated shipments → a person | `klarschiff/language.py` |
| German clients do not want data to leave the EU | Provider switch in one place: OpenAI or any OpenAI-compatible EU provider (e.g. Mistral AI) | `klarschiff/llm.py`, `.env.example` |
| A demo app is not a production service | Password login, Docker image (non-root, health check), HTTPS proxy, daily backup, daily monitor, EU server guide | `Dockerfile`, `deploy/`, `scripts/backup_data.sh` |
| Our tests are optimistic (E6) | Blind-test runner for broker-labelled real shipments, with the go / no-go rule | `evaluation/blind_test.py`, `evaluation/blind_test_template.csv` |
| "Not stated" documents | Option "this list is complete": every required document not listed counts as missing | App checkbox, `Shipment.documents_list_complete` |

## Try it

```bash
git checkout v2.2-pro
pip install -r requirements.txt
python -m pytest -q                                   # 24 tests
streamlit run mvp/app.py                              # upload mvp/sample_data/scan_invoice_TR.jpg (fictional Turkish invoice)
python evaluation/blind_test.py evaluation/blind_test_template.csv
```

## Still not code (and more important than code)

1. A licensed customs broker as pilot partner (labels the blind test, reviews the rules quarterly).
2. Real, anonymised shipments from the client.
3. Company form, terms with limitation of liability, professional indemnity insurance.
4. Data-processing agreements with the model provider, LangSmith and the hosting company.
