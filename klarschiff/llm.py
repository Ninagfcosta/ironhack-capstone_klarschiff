"""One place to talk to the language model, so the provider can be changed without touching the agent.

Default: OpenAI (GPT-4o-mini). European option: any provider with an OpenAI-compatible API, for example
Mistral AI (Paris):
    KLARSCHIFF_LLM_BASE_URL=https://api.mistral.ai/v1
    KLARSCHIFF_LLM_API_KEY=<your Mistral key>
    KLARSCHIFF_MODEL=mistral-small-latest
    KLARSCHIFF_VISION_MODEL=pixtral-large-latest
Always re-run `python evaluation/run_eval.py --local` after changing the provider or the model.
"""
from __future__ import annotations

import base64
import hashlib
import json

from . import config


# token usage of the current agent run (for the cost estimate); reset by the agent at the start of each run
USAGE = {"prompt_tokens": 0, "completion_tokens": 0, "calls": 0, "cache_hits": 0}


def reset_usage() -> None:
    USAGE.update(prompt_tokens=0, completion_tokens=0, calls=0, cache_hits=0)


def usage_with_cost() -> dict:
    from . import config
    cost = USAGE["prompt_tokens"] * config.PRICE_IN_PER_M / 1e6 + USAGE["completion_tokens"] * config.PRICE_OUT_PER_M / 1e6
    return {**USAGE, "est_cost_usd": round(cost, 6)}


def client():
    from openai import OpenAI
    from langsmith.wrappers import wrap_openai

    kwargs = {"api_key": config.LLM_API_KEY, "timeout": 45, "max_retries": 2}
    if config.LLM_BASE_URL:
        kwargs["base_url"] = config.LLM_BASE_URL
    return wrap_openai(OpenAI(**kwargs))


def chat_json(system: str, user, model: str | None = None) -> dict:
    """Send one chat request and return the JSON object the model answers with.

    `user` is a string, or a list of content parts (text + images) for vision requests.
    v2.6 answer cache: the same question to the same model (temperature 0) is answered from data/llm_cache.json,
    so a repeated product or a re-check costs nothing and is instant. Turn off with KLARSCHIFF_LLM_CACHE=false.
    """
    key = _cache_key(model or config.MODEL, system, user)
    if config.LLM_CACHE and config.TEMPERATURE == 0:
        hit = _cache_load().get(key)
        if hit is not None:
            USAGE["cache_hits"] += 1
            _stats_add("hits")
            return hit
    resp = client().chat.completions.create(
        model=model or config.MODEL,
        temperature=config.TEMPERATURE,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
    )
    u = getattr(resp, "usage", None)
    if u is not None:
        USAGE["prompt_tokens"] += int(getattr(u, "prompt_tokens", 0) or 0)
        USAGE["completion_tokens"] += int(getattr(u, "completion_tokens", 0) or 0)
    USAGE["calls"] += 1
    text = resp.choices[0].message.content or "{}"
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    data = json.loads(text)
    if config.LLM_CACHE and config.TEMPERATURE == 0:
        cache = _cache_load()
        cache[key] = data
        _cache_file().write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
        _stats_add("misses")
    return data


# ---------------------------------------------------------------- answer cache (v2.6)
def _cache_file():
    return config.DATA_DIR / "llm_cache.json"


def _stats_file():
    return config.DATA_DIR / "llm_cache_stats.json"


def _cache_key(model: str, system: str, user) -> str:
    raw = json.dumps([model, system, user], ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _cache_load() -> dict:
    try:
        return json.loads(_cache_file().read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _stats_add(field: str) -> None:
    try:
        st = json.loads(_stats_file().read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        st = {"hits": 0, "misses": 0}
    st[field] = st.get(field, 0) + 1
    _stats_file().write_text(json.dumps(st), encoding="utf-8")


def cache_stats() -> dict:
    """For the dashboard: answers served from the cache vs. new AI calls, and the share saved."""
    try:
        st = json.loads(_stats_file().read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        st = {"hits": 0, "misses": 0}
    total = st.get("hits", 0) + st.get("misses", 0)
    return {"hits": st.get("hits", 0), "misses": st.get("misses", 0), "entries": len(_cache_load()),
            "saved_share": round(st.get("hits", 0) / total, 2) if total else None}


def clear_cache() -> None:
    """Empty the cache, e.g. after changing the prompt rules or the model (then re-run the evaluation)."""
    for f in (_cache_file(), _stats_file()):
        if f.exists():
            f.unlink()


def image_part(image_bytes: bytes, mime: str = "image/png") -> dict:
    b64 = base64.b64encode(image_bytes).decode()
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}", "detail": "high"}}
