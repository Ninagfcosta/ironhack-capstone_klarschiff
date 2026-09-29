# GDPR documentation: KlarSchiff

**Version:** Round 2 · 25 September 2026 · GDPR (Regulation (EU) 2016/679) and German BDSG
*Consultant's assessment for a capstone project, not legal advice. To be confirmed by I&E's data protection officer before the pilot.*

## 1. Is personal data processed?

**Yes, a little.** Shipping documents are about goods, but they also contain personal data: contact names, e-mail addresses and phone numbers of supplier and buyer staff, signatures, and sometimes the names of sole traders. The app's decision log stores no personal names (team level only).

| Data | Personal? | Needed for the check? | Treatment |
|---|---|---|---|
| Goods description, quantities, weights, HS code | No | Yes | Processed |
| Company names, addresses | Usually no (legal persons); yes for sole traders | No | **Removed before sending to the LLM** (pilot procedure) |
| Contact persons, e-mails, phones, signatures | Yes | No | Not entered; removed from PDFs before upload |
| Reviewer identity | Yes | No | Not stored; log is per team |
| App login (if hosted) | Yes | For access control | Minimal account data |

**Principle:** the agent only needs *what the goods are*, not *who sent them*. Data minimisation (Art. 5(1)(c)) is built into the process.

## 2. Data flow

```
Logistics user ──(goods description, documents list)──► KlarSchiff app (EU hosting)
        │                                                     │
        │                                                     ├──► OpenAI API (description + candidate codes only)   processor, DPA, EU data residency option
        │                                                     ├──► LangSmith (traces)                                processor, DPA, EU region endpoint
        │                                                     └──► decision_log.csv (no personal names)              I&E, retention see §5
        └──► review pack (Markdown) ──► customs broker (existing relationship, own GDPR basis)
Monitor: reads public government sources only; no personal data.
```

## 3. Legal bases (Art. 6)

| Purpose | Legal basis |
|---|---|
| Checking shipment documents before export/import | Art. 6(1)(b) performance of the contracts with buyers/suppliers, and Art. 6(1)(c) legal obligation (customs law requires correct declarations) |
| Minimal contact data that cannot be removed | Art. 6(1)(f) legitimate interest (correct customs processing); balancing test documented below |
| Audit trail of decisions | Art. 6(1)(c) and (f) (demonstrating diligence to customs authorities) |

**Balancing test (legitimate interest):** the interest (avoiding customs errors) is real; the data is business contact data that people expect to be used for shipping; impact is low; minimisation and deletion limits apply → interest prevails.

## 4. DPIA (Art. 35): screening

| Criterion (EDPB / DSK list) | Present? |
|---|---|
| Systematic evaluation or scoring of people | No |
| Automated decision with legal effect on people (Art. 22) | No (decisions are about goods, and a person decides) |
| Large-scale or sensitive data | No |
| Systematic monitoring of employees | **No, by design** (team-level metrics only) |
| New technology (AI) | Yes |
| Transfer outside the EU | Possible (US AI provider) |

**Result:** two criteria at most → a full DPIA is **not mandatory**, but we write a **short DPIA** anyway because of the AI and transfer aspects. Risks and measures are the table in §6.

## 5. Retention

| Data | Retention | Reason |
|---|---|---|
| Decision log | At least 3 years | Customs records must be kept at least 3 years (Art. 51 Union Customs Code); longer only if I&E's tax advisor classifies the log as a business record under German retention rules (AO/HGB) |
| LangSmith traces | 14 days (Developer plan) or as configured | Debugging and evaluation only |
| OpenAI API data | Per OpenAI API data policy (no training on API data by default); request zero-data-retention for the pilot if available | Processing only |
| Uploaded PDFs | Not stored by the app | |

## 6. Processors and international transfers

| Processor | Role | Safeguard |
|---|---|---|
| OpenAI | LLM inference | Data Processing Addendum; EU-US Data Privacy Framework and/or Standard Contractual Clauses; EU data residency if available on the plan; only goods descriptions sent |
| LangSmith (LangChain) | Tracing / evaluation | DPA; **EU region endpoint** (`eu.api.smith.langchain.com`) |
| Hosting (e.g. Streamlit Community Cloud for demos, EU cloud for the pilot) | App hosting | DPA; **no real data on the public demo** |

**Plan B for German clients who do not want US providers:** the model is configurable; an EU-hosted model (e.g. a European provider or an EU Azure region) can replace GPT-4o-mini after re-running the evaluation.

## 7. Data subject rights (Art. 12-22)

Access, rectification, erasure and objection requests go to I&E (controller). Because KlarSchiff stores no personal names in its log and traces are short-lived, most requests are answered with "no personal data held in KlarSchiff", after checking LangSmith traces within their retention window. Contact: I&E data protection contact [to be named].

## 8. Security

Keys only in `.env` / platform secrets, never in code or Git (`.gitignore`; secret scanning on GitHub); least-privilege access to the app; HTTPS; audit log; incident procedure: notify I&E within 24 hours so it can meet the 72-hour duty under Art. 33.

## 9. v2.2 additions (scans, photos, translation)

- **Scans and photos** are sent to the model provider as whole images. They can contain names, signatures and addresses. Rule for the pilot: **cover or crop personal data before uploading**; the vision prompt also tells the model not to return names, signatures, phone numbers or e-mail addresses.
- **Translation** sends only the goods description.
- For clients who require EU processing, set an EU provider in `.env` (`KLARSCHIFF_LLM_BASE_URL`, see `klarschiff/llm.py`) and re-run the evaluation.
- For the pilot, the app runs on a server in Germany behind HTTPS and a password (set up with the client's IT).
