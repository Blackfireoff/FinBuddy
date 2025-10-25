from typing import Literal
import requests, os, json
from dotenv import load_dotenv
from fastapi import APIRouter
from scoring import EnhancedTransactionScorer
from transactions import get_last_transactions, BlockscoutAPIClient
from schemas import ExplainResponse, ExplainRequest
from AIService import explain

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
    Endpoint pour récupérer les scores des 3 dernières transactions avec analyse blockchain en temps réel et interpreter API.

    Exemple: GET /transactions/mainnet/0x94E2623A8637F85aC367940D5594eD4498fEDB51/scores
    """
    # Get transactions
    transactions = await get_last_transactions(network, evm_address)
    
    # Initialize API client and enhanced scorer
    api_client = BlockscoutAPIClient(network)
    enhanced_scorer = EnhancedTransactionScorer(wallet=evm_address)
    
    # Score transactions avec données enrichies + interpreter (V2)
    cohort_stats = await api_client.get_cohort_stats()

    scored_transactions = []
    for tx in transactions:
        enhanced_data = await api_client.get_comprehensive_transaction_data(tx)
        scored_tx = enhanced_scorer.score_transaction_enhanced_v2(
            tx, enhanced_data, cohort_stats=cohort_stats
        )
        scored_transactions.append(scored_tx)

    return {
        "network": network, 
        "address": evm_address, 
        "scored_transactions": scored_transactions,

    }

# add a route using the ai.py to get a chat completion from asi1.ai
@router.get("/ai/chat")
def ai_chat(message: str):

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
    
@router.post("/aiservice/explain", response_model=ExplainResponse)
async def ai_explain(req: ExplainRequest):
    return await explain(req=req)