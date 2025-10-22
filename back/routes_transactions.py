from typing import Literal

from fastapi import APIRouter

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
