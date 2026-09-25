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
import json

from . import config


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
    """
    resp = client().chat.completions.create(
        model=model or config.MODEL,
        temperature=config.TEMPERATURE,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
    )
    text = resp.choices[0].message.content or "{}"
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(text)


def image_part(image_bytes: bytes, mime: str = "image/png") -> dict:
    b64 = base64.b64encode(image_bytes).decode()
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}", "detail": "high"}}
