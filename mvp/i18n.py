"""Interface language for the KlarSchiff app: English (default) and German.

Why: the pilot users are German customs, logistics and construction teams. The code, the rule base and the
course deliverables stay in English; only what people see on screen changes.

How it works:
- `UI` maps every English interface text to its German version. `t(text, lang)` returns the right one.
- The agent's review reasons are generated in English. `reason(text, lang)` translates the known patterns
  (regular expressions below) and leaves anything unknown in English, so nothing is ever hidden.
- Legal names (CBAM, CE, DoP, TARIC, HTS) are not translated.
"""
from __future__ import annotations

import re

LANGS = {"en": "English", "de": "Deutsch"}

UI: dict[str, str] = {
    # interface redesign (Oct 2026)
    'Money tip': 'Spartipp',
    'The correction is now a test case: the next evaluation checks it.': 'Die Korrektur ist jetzt ein Testfall: die nächste Auswertung prüft ihn.',
    'Download data for the broker (JSON)': 'Daten für den Zollvertreter herunterladen (JSON)',
    'Repeated lines reused': 'Wiederholte Positionen übernommen',
    'AI checks saved': 'Eingesparte KI-Prüfungen',
    'Money tips': 'Spartipps',
    'Median review time (minutes, measured)': 'Median der Prüfzeit (Minuten, gemessen)',
    'Corrections turned into test cases': 'Korrekturen als Testfälle',
    'Measured review time replaces the illustrative ROI numbers during the pilot.': 'Die gemessene Prüfzeit ersetzt im Pilot die beispielhaften ROI-Zahlen.',
    '📋 Review queue': '📋 Prüfliste',
    '📊 Dashboard': '📊 Dashboard',
    'New client (first 30 days): a person reviews every shipment': 'Neuer Kunde (erste 30 Tage): eine Person prüft jede Sendung',
    'Voice note from the warehouse (MP3 / M4A / WAV)': 'Sprachnachricht aus dem Lager (MP3 / M4A / WAV)',
    'Turning the voice note into text…': 'Sprachnachricht wird in Text umgewandelt…',
    'Band: {}': 'Stufe: {}',
    'below {:.0%}: a person reviews': 'unter {:.0%}: eine Person prüft',
    'high': 'hoch',
    'medium': 'mittel',
    'low': 'niedrig',
    'Review ticket {} opened · due {} · see the Review queue tab': 'Prüfticket {} eröffnet · fällig {} · siehe Reiter Prüfliste',
    'Voice note': 'Sprachnachricht',
    '✉️ Draft an e-mail to the supplier': '✉️ E-Mail an den Lieferanten entwerfen',
    'Draft only: a person reads, edits and sends it. Nothing is sent automatically.': 'Nur ein Entwurf: eine Person liest, ändert und sendet ihn. Nichts wird automatisch gesendet.',
    'Subject': 'Betreff',
    'Message': 'Nachricht',
    'Download the draft (.txt)': 'Entwurf herunterladen (.txt)',
    'Review queue': 'Prüfliste',
    'Every shipment that needs a person gets a ticket with an owner and a due date, so nothing is forgotten. Optional: an n8n workflow (n8n/review_queue_workflow.json) copies each ticket to Airtable and alerts the team on Telegram.': 'Jede Sendung, die eine Person braucht, bekommt ein Ticket mit Zuständigkeit und Fälligkeit, damit nichts vergessen wird. Optional: ein n8n-Workflow (n8n/review_queue_workflow.json) kopiert jedes Ticket nach Airtable und informiert das Team per Telegram.',
    'Open': 'Offen',
    'Overdue': 'Überfällig',
    'Average time to close (hours)': 'Ø Zeit bis zum Abschluss (Stunden)',
    'n8n alerts: on': 'n8n-Hinweise: an',
    'n8n alerts: off (set KLARSCHIFF_N8N_WEBHOOK in .env to turn them on)': 'n8n-Hinweise: aus (KLARSCHIFF_N8N_WEBHOOK in .env setzen)',
    'due': 'fällig',
    'Owner (team or role)': 'Zuständig (Team oder Rolle)',
    'Save owner': 'Speichern',
    'Mark as done': 'Erledigt',
    'Download the queue (JSON)': 'Liste herunterladen (JSON)',
    '🔍 Search by meaning': '🔍 Suche nach Bedeutung',
    'Finds the same product even when it is written differently (also German). Uses embeddings when an AI key is set.': 'Findet dasselbe Produkt, auch wenn es anders geschrieben ist (auch auf Deutsch). Nutzt Embeddings, wenn ein KI-Schlüssel gesetzt ist.',
    'Describe the product': 'Produkt beschreiben',
    'The master list is empty: import it above first.': 'Der Produktstamm ist leer: bitte oben zuerst importieren.',
    '🔁 Re-check after a rule change': '🔁 Neu prüfen nach einer Regeländerung',
    'Lists the approved products in the master list whose HS code is affected by an open alert, so a person reviews them.': 'Zeigt freigegebene Produkte, deren HS-Code von einem offenen Hinweis betroffen ist, damit eine Person sie prüft.',
    'Find affected products': 'Betroffene Produkte finden',
    'Download for the batch check (CSV)': 'Für die Sammelprüfung herunterladen (CSV)',
    'No approved product is affected by an open alert.': 'Kein freigegebenes Produkt ist von einem offenen Hinweis betroffen.',
    'Dashboard: decisions and quality': 'Dashboard: Entscheidungen und Qualität',
    'Open reviews': 'Offene Prüfungen',
    'Overdue reviews': 'Überfällige Prüfungen',
    'Why shipments go to a person': 'Warum Sendungen zu einer Person gehen',
    'Reason': 'Grund',
    'Count': 'Anzahl',
    'Weekly second look (5–10% sample)': 'Wöchentliche Zweitprüfung (Stichprobe 5–10 %)',
    "A second person re-checks a random sample of last week's approved decisions. The broker stays responsible.": 'Eine zweite Person prüft eine Zufallsstichprobe der freigegebenen Entscheidungen der letzten Woche. Der Zollvertreter bleibt verantwortlich.',
    "Draw this week's sample (10%)": 'Stichprobe dieser Woche ziehen (10 %)',
    'Download the sample (CSV)': 'Stichprobe herunterladen (CSV)',
    'No approved decisions in the last 7 days.': 'Keine freigegebenen Entscheidungen in den letzten 7 Tagen.',
    'Decision log': 'Entscheidungsprotokoll',
    'You decide': 'Sie entscheiden',
    'Applies official rules': 'Wendet offizielle Regeln an',
    'Checks the documents': 'Prüft die Unterlagen',
    'Suggests the customs code': 'Schlägt den Zolltarif vor',
    '{} to confirm': '{} zu bestätigen',
    '🧭 Suggests the customs code': '🧭 Schlägt den Zolltarif vor',
    '📄 Checks the documents': '📄 Prüft die Unterlagen',
    '⚖️ Applies official rules': '⚖️ Wendet offizielle Regeln an',
    '👤 You decide': '👤 Sie entscheiden',
    'How the agent works': 'So arbeitet der Agent',
    '1 Intake → 2 Validate → 3 Recommend → 4 Rules → 5 You decide. The result appears here.': '1 Eingang → 2 Abgleich → 3 Vorschlag → 4 Regeln → 5 Sie entscheiden. Das Ergebnis erscheint hier.',
    'A person must review this shipment': 'Eine Person muss diese Sendung prüfen',
    '{} reason(s):': '{} Grund/Gründe:',
    'All checks passed': 'Alle Prüfungen bestanden',
    'translated': 'übersetzt',
    'read': 'gelesen',
    '{} issue(s)': '{} Abweichung(en)',
    '{} missing': '{} fehlt/fehlen',
    'documents OK': 'Unterlagen OK',
    'waiting for you': 'wartet auf Sie',
    '1 · Intake': '1 · Eingang',
    '2 · Validate': '2 · Abgleich',
    '3 · Recommend': '3 · Vorschlag',
    '4 · Rules': '4 · Regeln',
    '5 · You decide': '5 · Sie entscheiden',
    'Below {:.0%}: a person reviews': 'Unter {:.0%}: eine Person prüft',
    'Standard goods': 'Standardware',
    'CE-marked product': 'CE-gekennzeichnetes Produkt',
    'Trade measures or controls': 'Handelsmaßnahmen oder Kontrollen',
    '💬 Why': '💬 Warum',
    '📄 Documents': '📄 Unterlagen',
    '⚖️ Rules': '⚖️ Regeln',
    '🔗 Sources & data': '🔗 Quellen & Daten',
    'No special trade measures for this code.': 'Keine besonderen Handelsmaßnahmen für diesen Code.',
    'The agent suggests. You approve, correct or reject. Every decision is logged.': 'Der Agent schlägt vor. Sie bestätigen, korrigieren oder lehnen ab. Jede Entscheidung wird protokolliert.',
    # header and general
    "AI pre-shipment co-pilot · HS code suggestion, document check and tariff monitor":
        "KI-Co-Pilot vor dem Versand · HS-Code-Vorschlag, Dokumentenprüfung und Zollmonitor",
    "Clear answers. Human decisions.": "Klare Antworten. Menschliche Entscheidungen.",
    "Language": "Sprache",
    "Password": "Passwort",
    "Log in": "Anmelden",
    "Wrong password.": "Falsches Passwort.",
    "Running in **offline mode** (no AI key found): keyword matching only, every result goes to manual review. Add OPENAI_API_KEY to `.env` for the full agent.":
        "**Offline-Modus** (kein KI-Schlüssel gefunden): nur Stichwortsuche, jedes Ergebnis geht in die manuelle Prüfung. "
        "OPENAI_API_KEY in `.env` eintragen für den vollständigen Agenten.",
    # tabs
    "🔎 Check a shipment": "🔎 Sendung prüfen",
    "📡 Tariff monitor": "📡 Zollmonitor",
    "🗂️ Decisions & metrics": "🗂️ Entscheidungen & Kennzahlen",
    "ℹ️ How it works": "ℹ️ So funktioniert es",
    # check - input
    "1 · Shipment": "1 · Sendung",
    "Load an example": "Beispiel laden",
    "(write your own)": "(selbst eingeben)",
    "Goods description, as on the invoice": "Warenbeschreibung, wie auf der Rechnung",
    "e.g. Invoice: 500 bags Portland cement CEM I 42.5, 25 kg each. DoP and CE label attached.":
        "z. B. Rechnung: 500 Sack Portlandzement CEM I 42,5, je 25 kg. Leistungserklärung (DoP) und CE-Kennzeichnung beigefügt.",
    "Origin (ISO)": "Ursprung (ISO)",
    "Destination (ISO)": "Bestimmung (ISO)",
    "Use": "Verwendung",
    "construction": "Bau",
    "other": "Sonstiges",
    "Documents you have": "Vorhandene Unterlagen",
    "Choose options": "Bitte auswählen",
    "This list is complete: anything not selected is missing": "Diese Liste ist vollständig: alles nicht Ausgewählte fehlt",
    "Optional: invoice, packing list, PDF, scan, photo or e-invoice": "Optional: Rechnung, Packliste, PDF, Scan, Foto oder E-Rechnung",
    "Invoice lines (CSV)": "Rechnungspositionen (CSV)",
    "Packing list lines (CSV)": "Packlistenpositionen (CSV)",
    "Invoice PDF (text or scanned)": "Rechnung als PDF (Text oder gescannt)",
    "Scan or photo of the invoice (JPG / PNG)": "Scan oder Foto der Rechnung (JPG / PNG)",
    "E-invoice (XRechnung / ZUGFeRD XML)": "E-Rechnung (XRechnung / ZUGFeRD XML)",
    "CSV columns: description, quantity, unit, gross_weight_kg, value_eur · examples in mvp/sample_data/ · Scans and photos are read by the AI model: cover names, signatures and addresses before uploading.":
        "CSV-Spalten: description, quantity, unit, gross_weight_kg, value_eur · Beispiele in mvp/sample_data/ · "
        "Scans und Fotos liest das KI-Modell: Namen, Unterschriften und Adressen vor dem Hochladen abdecken.",
    "Check shipment": "Sendung prüfen",
    "Scanned PDF: reading it with the AI model…": "Gescanntes PDF: das KI-Modell liest es…",
    "Reading the photo with the AI model…": "Das KI-Modell liest das Foto…",
    "Please describe the goods first.": "Bitte zuerst die Ware beschreiben.",
    "Checking documents, rules and tariffs…": "Unterlagen, Regeln und Zölle werden geprüft…",
    "Something went wrong ({}). The shipment was not checked; please try again or check it manually.":
        "Etwas ist schiefgelaufen ({}). Die Sendung wurde nicht geprüft; bitte erneut versuchen oder manuell prüfen.",
    # check - result
    "2 · Suggestion": "2 · Vorschlag",
    "The result appears here.": "Das Ergebnis erscheint hier.",
    "⚠️ Manual review needed": "⚠️ Prüfung erforderlich",
    "✅ All checks passed.": "✅ Alle Prüfungen bestanden.",
    "A person still approves before filing.": "Vor der Anmeldung gibt trotzdem ein Mensch frei.",
    "HS code": "HS-Code",
    "Confidence": "Sicherheit",
    "Category": "Kategorie",
    "🌐 Translated from '{}': original and English": "🌐 Übersetzt aus '{}': Original und Englisch",
    "Original": "Original",
    "English (used for the check)": "Englisch (für die Prüfung verwendet)",
    "📷 Read from the scan/photo ({}, legible: {})": "📷 Aus Scan/Foto gelesen ({}, lesbar: {})",
    "Not readable": "Nicht lesbar",
    "Why": "Begründung",
    "The AI model writes its reasoning in English.": "Das KI-Modell schreibt seine Begründung auf Englisch.",
    "Evidence": "Beleg",
    "Documents": "Unterlagen",
    "Document": "Dokument",
    "Type": "Art",
    "required": "Pflicht",
    "recommended": "empfohlen",
    "Status": "Status",
    "✅ provided": "✅ vorhanden",
    "❌ missing": "❌ fehlt",
    "❔ not stated": "❔ nicht angegeben",
    "Legal basis": "Rechtsgrundlage",
    "Invoice vs packing list": "Rechnung vs. Packliste",
    "Trade measures and rules": "Handelsmaßnahmen und Regeln",
    "verified": "geprüft am",
    "re-verify": "erneut prüfen",
    "source": "Quelle",
    "{} open tariff alert(s) for this code: see the Tariff monitor tab.": "{} offene Zollwarnung(en) für diesen Code: siehe Reiter Zollmonitor.",
    "Check live before filing": "Vor der Anmeldung live prüfen",
    "Retrieved candidates (RAG) and alternatives": "Gefundene Kandidaten (RAG) und Alternativen",
    "Alternatives considered by the model:": "Vom Modell erwogene Alternativen:",
    "Mode": "Modus",
    "model": "Modell",
    "knowledge base": "Wissensbasis",
    # decision
    "3 · Your decision": "3 · Ihre Entscheidung",
    "Decision": "Entscheidung",
    "approved": "freigegeben",
    "corrected": "korrigiert",
    "rejected": "abgelehnt",
    "Final HS code": "Endgültiger HS-Code",
    "Comment (why?)": "Kommentar (warum?)",
    "Save decision": "Entscheidung speichern",
    "Please enter the corrected HS code.": "Bitte den korrigierten HS-Code eingeben.",
    "Saved to the decision log (audit trail).": "Im Entscheidungsprotokoll gespeichert (Prüfpfad).",
    "Download review pack for the broker": "Prüfpaket für den Zollagenten herunterladen",
    "Decision support only. A qualified person must confirm the classification and the documents before any customs declaration. Check the live tariff (TARIC / HTS) for the shipment date.":
        "Nur Entscheidungsunterstützung. Eine qualifizierte Person muss Einreihung und Unterlagen vor jeder Zollanmeldung bestätigen. "
        "Den aktuellen Tarif (TARIC / HTS) für das Versanddatum prüfen.",
    # monitor
    "Tariff & regulation monitor": "Zoll- und Regelungsmonitor",
    "Tariffs change fast (US Section 232 and general surcharges; EU steel measure from 1 Jul 2026; CBAM from 1 Jan 2026). The monitor checks official sources and opens an **alert** when something changes. While an alert is open, affected shipments always go to a person.":
        "Zölle ändern sich schnell (US Section 232 und allgemeine Aufschläge; EU-Stahlmaßnahme ab 1. Juli 2026; CBAM ab 1. Januar 2026). "
        "Der Monitor prüft amtliche Quellen und öffnet eine **Warnung**, wenn sich etwas ändert. Solange eine Warnung offen ist, "
        "gehen betroffene Sendungen immer an einen Menschen.",
    "Last run: {}  ·  runs daily via GitHub Actions (.github/workflows/tariff_monitor.yml) or on demand here.":
        "Letzter Lauf: {}  ·  läuft täglich über GitHub Actions (.github/workflows/tariff_monitor.yml) oder hier auf Knopfdruck.",
    "Run the monitor now": "Monitor jetzt starten",
    "Checking the Federal Register, USITC HTS and EU pages…": "Federal Register, USITC HTS und EU-Seiten werden geprüft…",
    "{} new alert(s).": "{} neue Warnung(en).",
    "Source not reachable: ": "Quelle nicht erreichbar: ",
    "Open alerts": "Offene Warnungen",
    "Affects HS": "Betrifft HS",
    "all": "alle",
    "open source": "Quelle öffnen",
    "Review note": "Prüfnotiz",
    "Mark as reviewed": "Als geprüft markieren",
    "Rules in force (versioned)": "Geltende Regeln (versioniert)",
    "Measure": "Maßnahme",
    "Legal reference": "Rechtsgrundlage",
    "From": "Ab",
    "Volatility": "Volatilität",
    "Re-check every (days)": "Erneut prüfen alle (Tage)",
    "Last verified": "Zuletzt geprüft",
    # log
    "Decisions and quality metrics": "Entscheidungen und Qualitätskennzahlen",
    "Decisions logged": "Protokollierte Entscheidungen",
    "Override rate (team level)": "Korrekturquote (Teamebene)",
    "A very low override rate over time can mean automation bias (people stop checking). Measured per team, not per person (works-council rules in Germany, §87 BetrVG).":
        "Eine dauerhaft sehr niedrige Korrekturquote kann Automation Bias bedeuten (Menschen prüfen nicht mehr). "
        "Gemessen pro Team, nicht pro Person (Mitbestimmung des Betriebsrats, §87 BetrVG).",
    # v2.3: master list and universal goods
    "📒 Master list": "📒 Produktstamm",
    "Master list (Produktstamm)": "Produktstamm (Master-Liste)",
    "Part numbers change, the product stays. Each product keeps ONE approved HS code and ONE approved German description; part numbers are linked to it. A new part number with the same description reuses the code, and a person confirms.":
        "Artikelnummern ändern sich, das Produkt bleibt. Jedes Produkt hat EINEN freigegebenen HS-Code und EINE freigegebene "
        "deutsche Beschreibung; Artikelnummern werden damit verknüpft. Eine neue Artikelnummer mit gleicher Beschreibung "
        "übernimmt den Code, und ein Mensch bestätigt.",
    "Products": "Produkte",
    "Part numbers": "Artikelnummern",
    "Part number": "Artikelnummer",
    "Part number (optional)": "Artikelnummer (optional)",
    "Used to find the product in the master list, even when the part number changed.":
        "Damit wird das Produkt im Produktstamm gefunden, auch wenn sich die Artikelnummer geändert hat.",
    "Without HS code (conflicts)": "Ohne HS-Code (Konflikte)",
    "Import the client's list (CSV)": "Liste des Kunden importieren (CSV)",
    "Columns: part_number, description, description_de, hs_code · example: mvp/sample_data/master_list_sample.csv · importing replaces the current list":
        "Spalten: part_number, description, description_de, hs_code · Beispiel: mvp/sample_data/master_list_sample.csv · "
        "der Import ersetzt die aktuelle Liste",
    "Master list CSV": "Produktstamm als CSV",
    "Import and check the list": "Liste importieren und prüfen",
    "{} rows → {} products · {} part numbers merged · {} conflict(s)": "{} Zeilen → {} Produkte · {} Artikelnummern zusammengeführt · {} Konflikt(e)",
    "Same product, different HS codes: {} ({}), part numbers {}: a person decides.":
        "Gleiches Produkt, verschiedene HS-Codes: {} ({}), Artikelnummern {}: ein Mensch entscheidet.",
    "Description": "Beschreibung",
    "German description": "Deutsche Beschreibung",
    "Download master list (CSV)": "Produktstamm herunterladen (CSV)",
    "Find a product": "Produkt suchen",
    "No product found: the agent classifies it and, after approval, adds it to the list.":
        "Kein Produkt gefunden: der Agent klassifiziert es und nimmt es nach der Freigabe in die Liste auf.",
    "Known part number": "Bekannte Artikelnummer",
    "New part number, same product": "Neue Artikelnummer, gleiches Produkt",
    "Similar product": "Ähnliches Produkt",
    "📒 Known part number": "📒 Bekannte Artikelnummer",
    "📒 New part number, same product": "📒 Neue Artikelnummer, gleiches Produkt",
    "📒 Similar product in the master list": "📒 Ähnliches Produkt im Produktstamm",
    "📒 Master list": "📒 Produktstamm",
    "Add to the master list (links the part number to the product)": "In den Produktstamm aufnehmen (verknüpft die Artikelnummer mit dem Produkt)",
    "Master list updated: product {}.": "Produktstamm aktualisiert: Produkt {}.",
    "from": "ab",
    # v2.3: batch, full codes, rulings, cost
    "📦 Batch": "📦 Stapelprüfung",
    "Batch check": "Stapelprüfung",
    "Check many shipments at once and download one report. Columns: shipment_id, description, origin, destination, part_number, documents_provided (separated by ;), intended_use · example: mvp/sample_data/batch_sample.csv":
        "Viele Sendungen auf einmal prüfen und einen Bericht herunterladen. Spalten: shipment_id, description, origin, "
        "destination, part_number, documents_provided (getrennt durch ;), intended_use · Beispiel: mvp/sample_data/batch_sample.csv",
    "Shipments CSV": "Sendungen als CSV",
    "Run the batch check": "Stapelprüfung starten",
    "Shipments": "Sendungen",
    "To review": "Zu prüfen",
    "Master-list hits": "Treffer im Produktstamm",
    "AI cost (estimate)": "KI-Kosten (Schätzung)",
    "Per line: about ${} · categories 1/2/3: {} / {} / {} · {} s": "Pro Zeile: etwa ${} · Kategorien 1/2/3: {} / {} / {} · {} s",
    "Download report (CSV)": "Bericht herunterladen (CSV)",
    "📚 Rulings library (EBTI / CROSS)": "📚 Entscheidungsbibliothek (EBTI / CROSS)",
    "Add official rulings your team looked up (EU EBTI, US CROSS). The agent shows similar ones as evidence. Columns: reference, source, code, description, issued, valid_until, url":
        "Amtliche Entscheidungen hinzufügen, die Ihr Team recherchiert hat (EU-EBTI, US-CROSS). Der Agent zeigt ähnliche als "
        "Beleg. Spalten: reference, source, code, description, issued, valid_until, url",
    "Rulings CSV": "Entscheidungen als CSV",
    "Add rulings": "Entscheidungen hinzufügen",
    "{} rulings added · {} in the library": "{} Entscheidungen hinzugefügt · {} in der Bibliothek",
    "Rulings in the library: {}": "Entscheidungen in der Bibliothek: {}",
    "AI use for this check: {} calls · {} tokens · about ${}": "KI-Nutzung für diese Prüfung: {} Aufrufe · {} Tokens · etwa ${}",
    "📚 Similar official rulings in your library ({})": "📚 Ähnliche amtliche Entscheidungen in Ihrer Bibliothek ({})",
    "🔢 Full code ({})": "🔢 Vollständiger Code ({})",
    "Suggested by word match; a person confirms the line.": "Per Wortabgleich vorgeschlagen; ein Mensch bestätigt die Position.",
    "Several lines fit: a person chooses.": "Mehrere Positionen passen: ein Mensch wählt.",
    "expired": "abgelaufen",
}

ABOUT = {
    "en": """
**KlarSchiff checks shipment documents before the goods leave, so errors are caught at the desk, not at the border.**

1. **Intake** reads the description, CSV lines, text PDFs, scans and photos (AI vision), e-invoices (XRechnung/ZUGFeRD), and translates Turkish or Chinese invoices.
   **Master list:** a known product (even with a new part number) reuses its approved HS code and German description.
2. **Validate** compares invoice and packing list line by line.
3. **Recommend** searches the whole Harmonized System 2022 (5,613 subheadings, RAG) and the LLM picks one, with reasons. Codes not yet reviewed by a person always go to review.
4. **Rules** (versioned, with legal references) decide category, documents and trade measures.
5. **Monitor** watches official sources for tariff changes and raises alerts.
   **Full code:** the 8-digit CN (EU) or HTS (US) line is suggested from free official data; similar official rulings
   from your library are shown as evidence. **Guard:** hidden instructions in documents are ignored and flagged.
6. **A person decides.** Every decision is logged. Nothing is ever filed automatically.

Limits: any product can be classified, but only reviewed codes and master-list products can pass without extra review;
rule packs (CE, export control, food/plants, deforestation, CBAM, trade defence) show indicative scope; translations and scans
always go to a person; rules must be re-verified by a customs professional.
""",
    "de": """
**KlarSchiff prüft Versandunterlagen, bevor die Ware das Lager verlässt: Fehler werden am Schreibtisch gefunden, nicht an der Grenze.**

1. **Erfassung** liest Beschreibung, CSV-Positionen, Text-PDFs, Scans und Fotos (KI-Bilderkennung), E-Rechnungen (XRechnung/ZUGFeRD) und übersetzt türkische oder chinesische Rechnungen.
   **Produktstamm:** ein bekanntes Produkt (auch mit neuer Artikelnummer) übernimmt seinen freigegebenen HS-Code und die deutsche Beschreibung.
2. **Abgleich** vergleicht Rechnung und Packliste Position für Position.
3. **Vorschlag** durchsucht das gesamte Harmonisierte System 2022 (5.613 Unterpositionen, RAG), das Sprachmodell wählt eine aus, mit Begründung. Noch nicht von einem Menschen geprüfte Codes gehen immer in die Prüfung.
4. **Regeln** (versioniert, mit Rechtsgrundlage) bestimmen Kategorie, Unterlagen und Handelsmaßnahmen.
5. **Monitor** beobachtet amtliche Quellen auf Zolländerungen und öffnet Warnungen.
   **Vollständiger Code:** die 8-stellige KN-Position (EU) oder HTS-Position (US) wird aus freien amtlichen Daten
   vorgeschlagen; ähnliche amtliche Entscheidungen aus Ihrer Bibliothek werden als Beleg gezeigt. **Schutz:** versteckte
   Anweisungen in Dokumenten werden ignoriert und gemeldet.
6. **Ein Mensch entscheidet.** Jede Entscheidung wird protokolliert. Nichts wird automatisch angemeldet.

Grenzen: jedes Produkt kann eingereiht werden, aber nur geprüfte Codes und Produkte aus dem Produktstamm kommen ohne
zusätzliche Prüfung durch; Regelpakete (CE, Exportkontrolle, Lebensmittel/Pflanzen, Entwaldung, CBAM, Handelsschutz)
zeigen einen indikativen Umfang; Übersetzungen und Scans gehen immer an einen Menschen; Regeln müssen von einer
Zollfachkraft erneut geprüft werden.
""",
}

# Agent review reasons: (English pattern, German template). Groups are reused in the German text.
REASONS: list[tuple[str, str]] = [
    (r"^Translated from '(.+?)': a person checks the translation\.(?: Uncertain terms: (.*))?$",
     "Übersetzt aus '{0}': ein Mensch prüft die Übersetzung.{1}"),
    (r"^Text in '(.+?)' could not be translated \((.+)\)\.$", "Text in '{0}' konnte nicht übersetzt werden ({1})."),
    (r"^Text in '(.+?)' and no AI model available to translate it\.$", "Text in '{0}' und kein KI-Modell zum Übersetzen verfügbar."),
    (r"^Document partly unreadable: (.*)$", "Dokument teilweise unleserlich: {0}"),
    (r"^Confidence (\S+) is below (\S+)\.$", "Sicherheit {0} liegt unter {1}."),
    (r"^Code (\S+) is not in the reviewed knowledge base\.$", "Code {0} ist nicht in der geprüften Wissensbasis."),
    (r"^Description too vague \((\d+) meaningful word\(s\)\): material, form or use is missing\.$",
     "Beschreibung zu ungenau ({0} aussagekräftige(s) Wort(e)): Material, Form oder Verwendung fehlt."),
    (r"^Close call between (\S+) and (\S+): a person must choose\.$", "Knappe Entscheidung zwischen {0} und {1}: ein Mensch muss wählen."),
    (r"^Information missing: (.*)$", "Fehlende Angaben: {0}"),
    (r"^Required document\(s\) missing: (.*)$", "Pflichtunterlage(n) fehlen: {0}"),
    (r"^(\d+) invoice/packing-list mismatch\(es\)\.$", "{0} Abweichung(en) zwischen Rechnung und Packliste."),
    (r"^Category 3: additional trade measures or controls always need a person\.$",
     "Kategorie 3: zusätzliche Handelsmaßnahmen oder Kontrollen brauchen immer einen Menschen."),
    (r"^Code (\S+) is not a valid HS 2022 subheading\.$", "Code {0} ist keine gültige HS-2022-Unterposition."),
    (r"^CE-marked product \((.+)\): EU Declaration of Conformity \+ CE marking\.$",
     "CE-pflichtiges Produkt ({0}): EU-Konformitätserklärung + CE-Kennzeichnung."),
    (r"^Special controls apply: (.*)\.$", "Besondere Kontrollen gelten: {0}."),
    (r"^Upcoming rule: (\S+) applies from (\S+)\.$", "Kommende Regel: {0} gilt ab {1}."),
    (r"^Possible hidden instructions for the AI in the document \((.*)\): they were ignored; a person checks the original\.$",
     "Mögliche versteckte Anweisungen an die KI im Dokument ({0}): sie wurden ignoriert; ein Mensch prüft das Original."),
    (r"^New part number (\S+) matches product (\S+) by description: confirm the link \(HS (\S+)\)\.$",
     "Neue Artikelnummer {0} passt laut Beschreibung zu Produkt {1}: Verknüpfung bestätigen (HS {2})."),
    (r"^Known part number, but the description changed \((.*)\): check product (\S+)\.$",
     "Bekannte Artikelnummer, aber die Beschreibung hat sich geändert ({0}): Produkt {1} prüfen."),
    (r"^Master list conflict for product (\S+): codes differ in the list; a person decides\.$",
     "Konflikt im Produktstamm für Produkt {0}: unterschiedliche Codes in der Liste; ein Mensch entscheidet."),
    (r"^Similar to product (\S+) \(HS (\S+)\) but not the same \((.*)\): a person decides\.$",
     "Ähnlich wie Produkt {0} (HS {1}), aber nicht gleich ({2}): ein Mensch entscheidet."),
    (r"^Large shipment \(~(.+?) t\)\.$", "Große Sendung (~{0} t)."),
    (r"^CBAM: this shipment alone \(~(.+?) t\) is above the 50 t yearly threshold\.$",
     "CBAM: diese Sendung allein (~{0} t) liegt über der Jahresschwelle von 50 t."),
    (r"^Rule data older than its review interval: re-verify the source\.$", "Regeldaten älter als ihr Prüfintervall: Quelle erneut prüfen."),
    (r"^(\d+) open tariff/regulation alert\(s\) for this code\.$", "{0} offene Zoll-/Regelungswarnung(en) für diesen Code."),
    (r"^Offline mode \(no LLM\): keyword match only\.$", "Offline-Modus (kein Sprachmodell): nur Stichwortsuche."),
    (r"^Construction product under a harmonised standard \((.+)\): CE marking \+ DoP/DoPC\.$",
     "Bauprodukt mit harmonisierter Norm ({0}): CE-Kennzeichnung + Leistungserklärung (DoP/DoPC)."),
    (r"^Additional trade measures apply: (.*)\.$", "Zusätzliche Handelsmaßnahmen gelten: {0}."),
    (r"^No product-specific marking or trade measure found in the rule base: standard documents\.$",
     "Keine produktspezifische Kennzeichnung oder Handelsmaßnahme in der Regelbasis: Standardunterlagen."),
]
_REASONS = [(re.compile(p), g) for p, g in REASONS]


def t(text: str, lang: str = "en", *args) -> str:
    """Interface text in the chosen language. Unknown texts stay in English (never empty)."""
    out = UI.get(text, text) if lang == "de" else text
    return out.format(*args) if args else out


def reason(text: str, lang: str = "en") -> str:
    """Translate one agent review reason; unknown reasons stay in English."""
    if lang != "de":
        return text
    for rx, tpl in _REASONS:
        m = rx.match(text)
        if m:
            groups = [g or "" for g in m.groups()]
            if tpl.startswith("Übersetzt aus") and groups[1]:
                groups[1] = " Unsichere Begriffe: " + groups[1]
            return tpl.format(*groups)
    return text
