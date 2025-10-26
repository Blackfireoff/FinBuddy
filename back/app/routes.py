from typing import Literal

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from scoring import EnhancedTransactionScorer
from transactions import get_last_transactions, BlockscoutAPIClient
from positions import WalletPositions
from schemas import ExplainRequest, ExplainResponse
from AIService import explain
import json
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


@router.get("/positions/{network}/{evm_address}")
async def get_positions(network: Literal["mainnet", "sepolia"], evm_address: str):
    """
    Endpoint pour récupérer TOUTES les positions actuelles d'un wallet avec valeurs USD: 
    - ETH natif (avec prix USD)
    - Tous les tokens ERC-20 (USDC, USDT, etc.) avec prix USD
    - Tous les NFTs (ERC-721, ERC-1155)
    - Montants détenus, PnL et valeurs USD
    

    Exemple: GET /positions/mainnet/0x94E2623A8637F85aC367940D5594eD4498fEDB51
    
    Retourne:
    - native_balance: Balance ETH avec usd_price et usd_value
    - all_tokens.erc20_tokens: Liste des tokens ERC-20 avec PnL et valeurs USD
    - all_tokens.nft_tokens: Liste des NFTs détenus
    - portfolio_summary: Résumé du portefeuille avec total_value_usd
    """
    # Initialize wallet positions client
    wallet_positions = WalletPositions(network)
    
    # Get wallet positions
    positions = await wallet_positions.get_wallet_positions(evm_address)
    
    return {
        "network": network,
        "address": evm_address,
        "positions": positions
    }
@router.websocket("/aiservice/analyse")
async def ai_explain_ws(websocket: WebSocket):
    """
    WebSocket endpoint for AI analysis.
    - Client sends an ExplainRequest (JSON)
    - Server processes it with the AI service
    - Server sends back ExplainResponse when done
    """
    await websocket.accept()
    try:
        # Wait for client to send request
        data = await websocket.receive_text()

        # Parse into schema
        req_dict = json.loads(data)
        req = ExplainRequest(**req_dict)
        # Run AI job
        result: ExplainResponse = await explain(req=req)

        # Send result when done
        await websocket.send_text(result.model_dump_json(indent=2))

        # Optionally close connection after sending
        await websocket.close()

    except WebSocketDisconnect:
        print("🔌 Client disconnected from /aiservice/analyse")
    except Exception as e:
        error_msg = json.dumps({"error": str(e)})
        await websocket.send_text(error_msg)
        await websocket.close()