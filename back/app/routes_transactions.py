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