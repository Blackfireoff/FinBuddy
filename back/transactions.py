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
        Liste des 3 dernières transactions avec hash, from, to, et gasFeeWei

    Raises:
        HTTPException: En cas d'erreur HTTP ou de données invalides
    """
    # Choisir la base URL selon le réseau
    base_urls = {
        "mainnet": "https://eth.blockscout.com",
        "sepolia": "https://eth-sepolia.blockscout.com"
    }

    base_url = base_urls[network]
    url = f"{base_url}/api/v2/addresses/{evm_address}/transactions"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()  # Lève une exception pour les codes d'erreur HTTP

            data = response.json()

            # Vérifier si la réponse contient des items
            if not data or "items" not in data:
                raise HTTPException(status_code=404, detail="Aucune transaction trouvée")

            items = data.get("items", [])

            if len(items) == 0:
                return []

            # Prendre les 3 dernières transactions
            last_three = items[:3]

            # Transformer chaque transaction au format minimal
            result = []
            for item in last_three:
                try:
                    tx = {
                        "hash": item.get("hash"),
                        "from": item.get("from", {}).get("hash"),
                        "to": item.get("to", {}).get("hash") if item.get("to") else None,
                        "gasFeeWei": item.get("fee", {}).get("value")
                    }
                    result.append(tx)
                except (KeyError, AttributeError) as e:
                    # Continuer même si une transaction est mal formée
                    continue

            return result

    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Erreur Blockscout API: {e.response.status_code}"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Erreur de connexion à Blockscout: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur interne: {str(e)}"
        )

