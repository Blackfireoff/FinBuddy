import json
from typing import Any, Dict, Tuple

from fastapi import FastAPI, HTTPException
from jinja2 import Template
from json_repair import repair_json

from schemas import ExplainRequest, ExplainResponse, TxExplanation

# Frontend must provide AI config. Default provider is 'ollama'. No environment fallback is used.

# Native Ollama path removed; we use the OpenAI-compatible API for Ollama


# Load prompt template
with open("prompt.jinja", "r", encoding="utf-8") as f:
    PROMPT_TPL = Template(f.read())


async def openai_compat_chat(user_prompt: str, ai: Dict) -> Tuple[str, str]:
    """
    Call an OpenAI-compatible chat completion endpoint using frontend-provided config.
    Expected ai keys: { provider, api_key }. Model is restricted to provider defaults.
    """
    api_key = (ai or {}).get("api_key")
    provider = ((ai or {}).get("provider") or "ollama").lower()
    # For OpenAI-compatible providers, api_key is required. For 'ollama' it can be omitted.
    if provider != "ollama" and not api_key:
        raise HTTPException(
            status_code=400, detail="ai.api_key is required for non-ollama providers"
        )

    # Provider → base_url + allowed models mapping
    provider_defaults = {
        "openai": {
            "base_url": "https://api.openai.com/v1",
            "models": ["o4-mini"],
        },
        "gemini": {
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "models": ["gemini-2.5-flash"],
        },
        "groq": {
            "base_url": "https://api.groq.com/openai/v1",
            "models": ["llama-3.3-70b-versatile"],
        },
        "deepseek": {
            "base_url": "https://api.deepseek.com",
            "models": ["deepseek-chat"],
        },
        # Ollama via OpenAI-compatible API
        "ollama": {
            "base_url": "http://localhost:11434/v1",
            "models": ["llama3.2:3b"],
        },
    }

    defaults = provider_defaults.get(provider)
    if not defaults:
        raise HTTPException(status_code=400, detail="Unsupported ai.provider")

    base_url = defaults["base_url"]
    allowed_models = defaults.get("models") or []
    if not allowed_models:
        raise HTTPException(status_code=500, detail="No models configured for provider")
    # Use default (first) model; ignore custom model input to restrict surface
    model = allowed_models[0]

    try:
        from openai import OpenAI
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"openai client not installed: {str(e)}"
        )

    if provider == "ollama" and not api_key:
        api_key = "ollama"  # placeholder; Ollama ignores the token
    client = OpenAI(api_key=api_key, base_url=base_url)
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": user_prompt}],
        )
        msg = None
        try:
            msg = resp.choices[0].message.content if resp and resp.choices else None
        except Exception:
            pass
        if not msg:
            try:
                msg = resp.choices[0].message  # type: ignore
            except Exception:
                msg = None
        text = (
            msg
            if isinstance(msg, str)
            else json.dumps(resp.model_dump() if hasattr(resp, "model_dump") else resp)
        )
        return text, model
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"OpenAI-compatible chat error: {str(e)}"
        )


async def explain(req: ExplainRequest):
    explanations = []

    # On explique TX par TX pour garder des réponses courtes et robustes
    for tx in req.scored_transactions:
        # Construit le prompt
        payload = {
            "network": req.network,
            "address": req.address,
            "tx": tx.model_dump(),
        }
        prompt = PROMPT_TPL.render(data=payload)
        if not isinstance(req.ai, dict):
            # Default to ollama if not provided
            req.ai = {"provider": "ollama"}
        print(
            f"Prompt sent to {req.ai.get('provider', 'ollama')} (auto):\n{prompt}",
            flush=True,
        )
        data, used_model = await openai_compat_chat(user_prompt=prompt, ai=req.ai or {})
        data = repair_json(data)
        data = json.loads(data)
        data["tx_hash"] = tx.tx_hash
        data["scores"] = tx.subscores
        explanations.append(data)

    # Model label from enforced provider defaults
    response_model = used_model
    return ExplainResponse(
        network=req.network,
        address=req.address,
        model=response_model,
        explanations=[TxExplanation(**e) for e in explanations],
    )

