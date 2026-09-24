# EU AI Act compliance: KlarSchiff

**Version:** Round 2 · 25 September 2026 · Regulation (EU) 2024/1689 (AI Act), as amended by the 2026 Digital Omnibus on AI (final Council approval 29 June 2026)
*This is a consultant's assessment for a capstone project, not legal advice. Re-check at every project milestone.*

## 1. Result in one line

KlarSchiff is an **AI system with minimal risk**: not prohibited, not high-risk, and not subject to the Article 50 transparency duties in the way it is used. It must still meet the **general obligations** (AI literacy) and we apply **voluntary high-risk-style controls** because customs errors are costly.

## 2. Roles

| Role (AI Act) | Who | Why |
|---|---|---|
| Provider of the AI system | Janaina Hoffmann (KlarSchiff) | Develops the system and puts it into service under her name |
| Deployer | I&E LLC | Uses the system in its business |
| Provider of the general-purpose AI model | OpenAI (GPT-4o-mini) | GPAI obligations apply to OpenAI since 2 Aug 2025 |

## 3. Classification, step by step

| Question | Answer | Reasoning |
|---|---|---|
| Is it an **AI system** (Art. 3(1))? | **Yes** | It infers from input (shipment text) how to generate output (a classification suggestion) using an LLM. The rule engine alone would not be AI; the combination is. |
| Is it a **prohibited practice** (Art. 5)? | **No** | No manipulation, social scoring, biometric identification or emotion recognition. |
| **High-risk via Annex I** (safety component of a regulated product)? | **No** | It is not a safety component of a construction product and is not itself a product under EU harmonisation law. It only *checks* whether documents such as the DoP exist. |
| **High-risk via Annex III** (the eight listed areas)? | **No** | The closest area is point 7 (migration, asylum and **border control management**), which covers systems used **by or on behalf of public authorities**. KlarSchiff is used by a private company to prepare its own documents. It does not decide about natural persons (no employment, credit, education or public-service decisions). |
| **Transparency duties** (Art. 50)? | **Not triggered** | It is not a chatbot for the public and does not publish generated text or deepfakes. We still label every output as an AI suggestion (good practice). |
| Result | **Minimal risk** | Voluntary codes of conduct (Art. 95) may be followed. |

**What would change the class** (re-assess immediately if any becomes true):
- the system **files declarations automatically** or is used **by a customs authority** → possible Annex III point 7;
- it is used to evaluate **employees' performance** → possible Annex III point 4 (employment);
- it becomes a **safety component** of a product placed on the market.

## 4. Obligations that apply anyway

| Obligation | Status |
|---|---|
| **AI literacy** (Art. 4, in force since 2 Feb 2025; wording adjusted by the 2026 Digital Omnibus) | Kept as a contractual deliverable: 2-day training for users (what the agent can and cannot do, automation bias, when to escalate), attendance list |
| GPAI model obligations (Art. 53) | OpenAI's duty. We keep OpenAI's model documentation and usage policies on file |
| Other EU law | GDPR (see `gdpr_documentation.md`), CPR, CBAM, customs law: the AI does not change who is responsible |

## 5. Timeline check (after the Digital Omnibus)

| Date | What applies | Relevant for KlarSchiff? |
|---|---|---|
| 2 Feb 2025 | Prohibitions, AI literacy | Yes (AI literacy) |
| 2 Aug 2025 | GPAI model obligations | Indirectly (OpenAI) |
| 2 Dec 2026 | Transparency rules for AI-generated content (Art. 50) | Only if the use changes |
| 2 Dec 2027 | Stand-alone high-risk systems (Annex III), moved from 2 Aug 2026 | Only if reclassified |
| 2 Aug 2028 | High-risk systems in products (Annex I) | No |

## 6. Voluntary controls we apply (conformity summary)

Because a wrong code can cost money and penalties, KlarSchiff follows the spirit of the high-risk requirements:

| High-risk requirement (Art. 9-15) | What KlarSchiff does |
|---|---|
| Risk management (Art. 9) | Risk register with 12 risks and owners (`roi_risk_assessment.md`) |
| Data and data governance (Art. 10) | Reviewed, versioned knowledge base and rules with sources and `last_verified` dates |
| Technical documentation (Art. 11) | This repository (see outline below) |
| Record-keeping (Art. 12) | LangSmith traces + decision log with model and knowledge-base version |
| Transparency to users (Art. 13) | Every result shows reasons, evidence, sources, data date and limits |
| Human oversight (Art. 14) | A person approves, corrects or rejects every result; 13 review triggers; nothing is filed automatically |
| Accuracy and robustness (Art. 15) | 20-case evaluation, 16 unit tests, offline fallback, format checks, error analysis |

## 7. Technical documentation outline

1. System description and intended purpose → `use_case_definition.md`
2. Architecture and components → `poc/poc_documentation.md`, `klarschiff/`
3. Data: knowledge base, rules, sources, update process → `klarschiff/knowledge/`, `klarschiff/monitor.py`
4. Model: provider, version, prompt, settings → `klarschiff/recommend.py`, `.env.example`
5. Human oversight design → `mvp/mvp_documentation.md`
6. Testing and metrics, known errors → `evaluation/langsmith.md`, `tests/`
7. Risk management → `roi_risk_assessment.md`
8. Change log and re-evaluation rule (re-run the evaluation before any model or rule change) → `README.md`
