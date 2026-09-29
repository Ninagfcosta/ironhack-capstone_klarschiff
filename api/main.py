"""KlarSchiff REST API: the "plug" other systems (TMS, ERP, a customs broker's software) can call.

Run:   uvicorn api.main:app --port 8000        then open http://localhost:8000/docs (interactive docs)
Auth:  set KLARSCHIFF_API_KEY in .env; clients send it in the header  X-API-Key.  Empty = local demo only.

Endpoints
  GET  /health                 status, versions, whether an AI model is configured
  POST /check                  one shipment (JSON)            -> full result (code, category, documents, reasons ...)
  POST /batch                  CSV file (same columns as klarschiff.batch) -> summary + rows
  GET  /master-list/lookup     ?part_number=..&description=..  -> product match
The API never files anything: every answer is decision support and says whether a person must review it.
"""
from __future__ import annotations

import hmac
import os

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile

from klarschiff import agent, batch, config, master_list, retrieval, rules
from klarschiff.models import AgentResult, Shipment

API_KEY = os.getenv("KLARSCHIFF_API_KEY", "")
app = FastAPI(title="KlarSchiff API", version="2.3",
              description="Pre-shipment co-pilot: HS code suggestion, document check, trade measures, master list. "
                          "Decision support only: a qualified person confirms before any customs declaration.")


def auth(x_api_key: str = Header(default="")):
    if API_KEY and not hmac.compare_digest(x_api_key.encode(), API_KEY.encode()):
        raise HTTPException(status_code=401, detail="Missing or wrong X-API-Key")


@app.get("/health")
def health():
    return {"status": "ok", "llm_configured": config.llm_available(), "model": config.MODEL,
            "hs": retrieval.load_hs()["_meta"]["version"], "rules": rules.load_measures()["_meta"]["version"]}


@app.post("/check", response_model=AgentResult, dependencies=[Depends(auth)])
def check(shipment: Shipment):
    return agent.run(shipment)


@app.post("/batch", dependencies=[Depends(auth)])
async def check_batch(file: UploadFile = File(...)):
    text = (await file.read()).decode("utf-8-sig")
    rows, summary = batch.run_csv(text)
    if len(rows) > 5000:
        raise HTTPException(status_code=413, detail="Max 5,000 rows per call")
    return {"summary": summary, "rows": rows}


@app.get("/master-list/lookup", dependencies=[Depends(auth)])
def lookup(part_number: str = "", description: str = ""):
    return master_list.lookup(part_number, description).model_dump()
