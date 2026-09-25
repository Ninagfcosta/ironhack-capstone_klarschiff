# Deploy KlarSchiff on a server in the EU (pilot setup)

**Goal:** the pilot runs on a server in Germany, behind HTTPS and a password, with daily backups and a daily tariff monitor. Real shipment data never goes to a public demo.

| Option | When | Data location |
|---|---|---|
| Streamlit Community Cloud | Demos with **fictional** data only | Not guaranteed EU |
| **Own EU server (this guide)** | **Pilot with real, anonymised documents** | Germany (e.g. Hetzner, Nuremberg/Falkenstein) |

## 1. Server

1. Create a small Linux server in a German data centre (Ubuntu 24.04, 2 vCPU, 4 GB RAM is enough).
2. Log in with SSH keys (no password login). Open only ports 22, 80, 443:
   ```bash
   sudo ufw allow OpenSSH && sudo ufw allow 80 && sudo ufw allow 443 && sudo ufw enable
   ```
3. Install Docker: `curl -fsSL https://get.docker.com | sh`
4. Point a domain (e.g. `klarschiff.example.de`) to the server's IP and put it in `deploy/Caddyfile`.

## 2. App

```bash
git clone <private repository URL> klarschiff && cd klarschiff
cp .env.example .env && nano .env        # keys + a long KLARSCHIFF_APP_PASSWORD
docker compose -f deploy/docker-compose.yml up -d --build
```

Open `https://klarschiff.example.de`: you see the password screen first.

**`.env` for the pilot (minimum):**
```
OPENAI_API_KEY=...                 # or the EU provider below
KLARSCHIFF_APP_PASSWORD=...        # long, shared only with the pilot team
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=...
LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com
```

**EU model provider (optional, see `klarschiff/llm.py`):**
```
KLARSCHIFF_LLM_BASE_URL=https://api.mistral.ai/v1
KLARSCHIFF_LLM_API_KEY=...
KLARSCHIFF_MODEL=mistral-small-latest
KLARSCHIFF_VISION_MODEL=pixtral-large-latest
```
Re-run `python evaluation/run_eval.py --local` after any provider or model change and compare with the last result before using it.

## 3. Daily jobs (crontab -e)

```
0 5 * * *  cd ~/klarschiff && docker compose -f deploy/docker-compose.yml exec -T klarschiff python -m klarschiff.monitor
0 2 * * *  cd ~/klarschiff && ./scripts/backup_data.sh
```

## 4. Checklist before real data

- [ ] HTTPS works, password set, only ports 22/80/443 open
- [ ] Data-processing agreements signed (model provider, LangSmith, hosting)
- [ ] Pilot users trained (AI literacy, how to escalate)
- [ ] Documents anonymised or cropped before upload (names, signatures, addresses)
- [ ] Backup restored once as a test
- [ ] Blind test done (`evaluation/blind_test.py`) and results reviewed with the broker

## 5. Update

```bash
git pull && docker compose -f deploy/docker-compose.yml up -d --build
```
