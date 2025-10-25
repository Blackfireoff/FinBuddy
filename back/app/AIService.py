import os, json, httpx
from typing import Any, Dict
from fastapi import FastAPI, HTTPException
from jinja2 import Template
from schemas import ExplainRequest, ExplainResponse, TxExplanation

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL = os.getenv("MODEL", "llama3.2:3b")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "600"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.2"))
TOP_P = float(os.getenv("TOP_P", "0.9"))


# Load prompt template
with open("prompt.jinja", "r", encoding="utf-8") as f:
    PROMPT_TPL = Template(f.read())

async def ollama_chat(system_prompt: str, user_prompt: str) -> str:
    """
    Call Ollama chat API. Returns raw model text.
    """
    url = f"{OLLAMA_BASE_URL}/api/chat"
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt}
        ],
        "options": {
            "temperature": TEMPERATURE,
            "top_p": TOP_P,
            "num_predict": MAX_TOKENS
        },
        "stream": False
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post('http://10.15.0.20:11434', json=payload)
        if r.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Ollama error: {r.text}")
        data = r.json()
        return data.get("message", {}).get("content", "")

def force_json(s: str) -> Dict[str, Any]:
    """
    Try to extract a JSON object from model output.
    """
    s = s.strip()
    # Best effort: pick first {...} block
    start = s.find("{")
    end = s.rfind("}")
    if start != -1 and end != -1 and end > start:
        s = s[start:end+1]
    try:
        return json.loads(s)
    except Exception:
        raise HTTPException(status_code=502, detail="Model did not return valid JSON.")

async def explain(req: ExplainRequest):
    explanations = []

    # On explique TX par TX pour garder des réponses courtes et robustes
    for tx in req.scored_transactions:
        # Construit le prompt
        payload = {
            "network": req.network,
            "address": req.address,
            "tx": tx.model_dump()
        }
        prompt = PROMPT_TPL.render(data=payload)

        # Appel LLM
        raw = await ollama_chat(
            system_prompt="You are a precise, non-fabricating FinBuddy explanation engine.",
            user_prompt=prompt
        )
        # Parse JSON
        parsed = force_json(raw)

        # Sanity: s'assure qu'on renvoie bien le hash de la tx demandée
        parsed["tx_hash"] = tx.tx_hash

        explanations.append(parsed)

    return ExplainResponse(
        network=req.network,
        address=req.address,
        model=MODEL,
        explanations=[TxExplanation(**e) for e in explanations],
    )