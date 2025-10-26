import os, json, httpx
from typing import Any, Dict
from fastapi import FastAPI, HTTPException
from jinja2 import Template
from schemas import ExplainRequest, ExplainResponse, TxExplanation



OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL = os.getenv("MODEL", "llama3.2:3b")


# Load prompt template
with open("prompt.jinja", "r", encoding="utf-8") as f:
    PROMPT_TPL = Template(f.read())

async def ollama_chat(user_prompt: str) -> str:
    """
    Call Ollama chat API. Returns raw model text.
    """
    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": MODEL,
        "prompt": user_prompt,
        "stream": False
    }
    print(url, flush=True)
    async with httpx.AsyncClient(timeout=1200.0) as client:
        r = await client.post(url, json=payload)
        if r.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Ollama error: {r.text}")
        data = r.json()
        print(data, flush=True)
        return data.get("response", {})


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
        print(f"Prompt sent to Ollama:\n{prompt}", flush=True)
        # Appel LLM
        data = await ollama_chat(user_prompt=prompt)
        data = json.loads(data)

        # Parse JSON

        # Sanity: s'assure qu'on renvoie bien le hash de la tx demandée
        data["tx_hash"] = tx.tx_hash

        explanations.append(data)

    return ExplainResponse(
        network=req.network,
        address=req.address,
        model=MODEL,
        explanations=[TxExplanation(**e) for e in explanations],
    )