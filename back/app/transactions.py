from fastapi import HTTPException
from typing import Literal, Dict, List, Optional
import httpx
import asyncio


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
                        "type": item.get("type", 0),  # Transaction type (0=legacy, 1=EIP-2930, 2=EIP-1559)
                        "transaction_types": item.get("transaction_types", ["coin_transfer"]),
                        "status": item.get("status", "unknown"),
                        "isVerifiedContract": bool(item.get("to", {}).get("is_verified", False)),
                        "isKnownProtocol": bool(item.get("to", {}).get("name"))
                                            or len(item.get("to", {}).get("public_tags", [])) > 0,
                        "isScam": bool(item.get("to", {}).get("is_scam", False)),
                        "created_contract": item.get("created_contract"),
                        "has_error_in_internal_transactions": item.get("has_error_in_internal_transactions", False),
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


class BlockscoutAPIClient:
    """
    Comprehensive Blockscout API client for transaction analysis.
    Handles all API interactions for enhanced transaction scoring.
    """
    
    def __init__(self, network: Literal["mainnet", "sepolia"]):
        self.network = network
        self.base_urls = {
            "mainnet": "https://eth.blockscout.com",
            "sepolia": "https://eth-sepolia.blockscout.com"
        }
        self.base_url = self.base_urls[network]
    
    async def get_comprehensive_address_info(self, address: str) -> Dict:
        """
        Get comprehensive address information from Blockscout API.
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                url = f"{self.base_url}/api/v2/addresses/{address}"
                response = await client.get(url)
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            print(f"Error getting address info: {e}")
        return {}
    
    async def get_token_transfers(self, address: str, limit: int = 10) -> List[Dict]:
        """
        Get token transfer information for an address.
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                url = f"{self.base_url}/api/v2/addresses/{address}/token-transfers"
                params = {"limit": limit}
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("items", [])
        except Exception as e:
            print(f"Error getting token transfers: {e}")
        return []
    
    async def get_transaction_details(self, tx_hash: str) -> Dict:
        """
        Get detailed transaction information.
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                url = f"{self.base_url}/api/v2/transactions/{tx_hash}"
                response = await client.get(url)
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            print(f"Error getting transaction details: {e}")
        return {}
    
    async def get_interpreter_analysis(self, tx_hash: str) -> Dict:
        """
        Get transaction analysis from Blockscout interpreter API.
        This provides human-readable transaction descriptions and risk assessment.
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Use the interpreter API endpoint
                url = f"{self.base_url}/api/v2/transactions/{tx_hash}/interpret"
                response = await client.get(url)
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            print(f"Error getting interpreter analysis: {e}")
        return {}
    
    async def get_transaction_logs(self, tx_hash: str) -> List[Dict]:
        """
        Get transaction logs for detailed analysis.
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                url = f"{self.base_url}/api/v2/transactions/{tx_hash}/logs"
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("items", [])
        except Exception as e:
            print(f"Error getting transaction logs: {e}")
        return []
    
    async def get_comprehensive_transaction_data(self, tx: Dict) -> Dict:
        """
        Get all comprehensive data for a transaction in parallel.
        This method fetches all necessary data for enhanced scoring.
        """
        to_address = tx.get("to", "")
        tx_hash = tx.get("hash", "")
        
        # Prepare all API calls
        tasks = []
        
        if to_address:
            tasks.append(self.get_comprehensive_address_info(to_address))
            tasks.append(self.get_token_transfers(to_address, 10))
        else:
            tasks.append(asyncio.create_task(asyncio.sleep(0)))
            tasks.append(asyncio.create_task(asyncio.sleep(0)))
        
        if tx_hash:
            tasks.append(self.get_transaction_details(tx_hash))
            tasks.append(self.get_interpreter_analysis(tx_hash))
            tasks.append(self.get_transaction_logs(tx_hash))
        else:
            tasks.append(asyncio.create_task(asyncio.sleep(0)))
            tasks.append(asyncio.create_task(asyncio.sleep(0)))
            tasks.append(asyncio.create_task(asyncio.sleep(0)))
        
        # Execute all tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Extract results safely
        address_info = results[0] if not isinstance(results[0], Exception) else {}
        token_transfers = results[1] if not isinstance(results[1], Exception) else []
        tx_details = results[2] if not isinstance(results[2], Exception) else {}
        interpreter_data = results[3] if not isinstance(results[3], Exception) else {}
        tx_logs = results[4] if not isinstance(results[4], Exception) else []
        
        return {
            "address_info": address_info,
            "token_transfers": token_transfers,
            "transaction_details": tx_details,
            "interpreter_data": interpreter_data,
            "transaction_logs": tx_logs
        }
