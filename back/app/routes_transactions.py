from typing import Literal

from fastapi import APIRouter
from scoring import TransactionScorer

from transactions import get_last_transactions

router = APIRouter()


@router.get("/transactions/{network}/{evm_address}")
async def get_transactions(network: Literal["mainnet", "sepolia"], evm_address: str):
    """
    Endpoint pour récupérer les 3 dernières transactions d'une adresse Ethereum.

    Exemple: GET /transactions/mainnet/0x94E2623A8637F85aC367940D5594eD4498fEDB51
    """
    transactions = await get_last_transactions(network, evm_address)
    return {"network": network, "address": evm_address, "transactions": transactions}

@router.get("/transactions/{network}/{evm_address}/scores")
async def get_transaction_scores(network: Literal["mainnet", "sepolia"], evm_address: str):
    """
    Endpoint pour récupérer les scores des 3 dernières transactions d'une adresse Ethereum.

    Exemple: GET /transactions/mainnet/0x94E2623A8637F85aC367940D5594eD4498fEDB51/scores
    """
    transactions = await get_last_transactions(network, evm_address)
    scorer = TransactionScorer(wallet=evm_address)
    scored_transactions = [scorer.score_transaction(tx) for tx in transactions]
    print(scored_transactions)
    return {"network": network, "address": evm_address, "scored_transactions": scored_transactions}#         "final": final_score,
#         }

# add a route using the ai.py to get a chat completion from asi1.ai
@router.get("/ai/chat")
def ai_chat(message: str):
    import requests, os, json
    from dotenv import load_dotenv

    url = "https://api.asi1.ai/v1/chat/completions"
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
    headers = {
        "Authorization": f"Bearer {os.getenv('ASI_ONE_API_KEY')}",
        "Content-Type": "application/json"
    }
    body = {
        "model": "asi1-mini",
        "messages": [{"role": "user", "content": message}]
    }
    response = requests.post(url, headers=headers, json=body)
    if response.status_code == 200:
        content = response.json()["choices"][0]["message"]["content"]
        return {"response": content}
    else:
        return {"error": "Failed to get response from AI service", "status_code": response.status_code}