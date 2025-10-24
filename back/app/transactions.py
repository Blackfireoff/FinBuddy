from fastapi import HTTPException
from typing import Literal
import httpx


async def get_last_transactions(network: Literal["mainnet", "sepolia"], evm_address: str):
    """
    Récupère les 3 dernières transactions d'une adresse Ethereum depuis Blockscout API.

    Args:
        network: Le réseau Ethereum ("mainnet" ou "sepolia")
        evm_address: L'adresse Ethereum (0x...)

    Returns:
        Liste des 3 dernières transactions avec leurs détails.

    Raises:
        HTTPException: En cas d'erreur HTTP ou de données invalides
    """
    base_urls = {
        "mainnet": "https://eth.blockscout.com",
        "sepolia": "https://eth-sepolia.blockscout.com"
    }

    base_url = base_urls[network]
    url = f"{base_url}/api/v2/addresses/{evm_address}/transactions"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

            if not data or "items" not in data:
                raise HTTPException(status_code=404, detail="Aucune transaction trouvée")

            items = data.get("items", [])
            if len(items) == 0:
                return []

            last_three = items[:3]
            result = []

            for item in last_three:
                try:
                    tx = {
                        "hash": item.get("hash"),
                        "from": item.get("from", {}).get("hash"),
                        "to": item.get("to", {}).get("hash") if item.get("to") else None,
                        "gasUsed": int(item.get("gas_used", 0)),
                        "gasLimit": int(item.get("gas_limit", 0)),
                        "gasPrice": int(item.get("gas_price", 0)),
                        "valueEth": float(item.get("value", 0)) / 1e18,
                        "feeWei": int(item.get("fee", {}).get("value", 0)),
                        "baseFeePerGas": int(item.get("base_fee_per_gas", 0)),
                        "maxFeePerGas": int(item.get("max_fee_per_gas", 0)),
                        "maxPriorityFeePerGas": int(item.get("max_priority_fee_per_gas", 0)),
                        "type": item.get("transaction_types", ["transfer"])[0],
                        "isVerifiedContract": bool(item.get("to", {}).get("is_verified", False)),
                        "isKnownProtocol": bool(item.get("to", {}).get("name"))
                                            or len(item.get("to", {}).get("public_tags", [])) > 0,
                        "profitEth": 0.0  # placeholder, à calculer si tu veux ajouter ton profit réel
                    }
                    result.append(tx)
                except Exception:
                    continue

            return result

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code,
                            detail=f"Erreur Blockscout API: {e.response.status_code}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=503,
                            detail=f"Erreur de connexion à Blockscout: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")
