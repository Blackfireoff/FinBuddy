from fastapi import HTTPException
from typing import Literal, Dict, List
import httpx
import asyncio


class WalletPositions:
    """
    Retrieve all crypto holdings (ETH + ERC20 tokens) for a given EVM address
    using only Blockscout API (including USD valuations when available).
    """

    def __init__(self, network: Literal["mainnet", "sepolia"]):
        self.network = network
        self.base_urls = {
            "mainnet": "https://eth.blockscout.com",
            "sepolia": "https://eth-sepolia.blockscout.com"
        }
        self.base_url = self.base_urls.get(network)
        if not self.base_url:
            raise HTTPException(status_code=400, detail="Unsupported network")
        # CoinGecko base
        self.coingecko_api = "https://api.coingecko.com/api/v3"

    def _to_float(self, value, default: float = 0.0) -> float:
        """Safely convert various Blockscout value shapes to float.
        Handles None, strings, numbers, and dicts like {"usd": 1.23} or {"rate": 1.23}.
        """
        try:
            if value is None:
                return default
            if isinstance(value, dict):
                for key in ("usd", "price", "rate", "value"):
                    if key in value and value[key] is not None:
                        try:
                            return float(value[key])
                        except Exception:
                            continue
                return default
            return float(value)
        except Exception:
            return default

    async def _get_eth_balance(self, address: str, client: httpx.AsyncClient) -> Dict:
        """Fetch the native ETH balance and USD value."""
        url = f"{self.base_url}/api/v2/addresses/{address}"
        try:
            r = await client.get(url)
            r.raise_for_status()
            data = r.json()

            balance_wei = self._to_float(data.get("coin_balance"), 0.0)
            balance_eth = balance_wei / 1e18
            # Prefer CoinGecko price
            price_usd = await self._get_coingecko_eth_price(client)
            if not price_usd:
                # fallback to Blockscout
                price_usd = self._to_float(data.get("coin_price"), 0.0)
            value_usd = self._to_float(data.get("coin_balance_usd"), balance_eth * price_usd)

            return {
                "symbol": "ETH",
                "balance": round(balance_eth, 6),
                "price_usd": round(price_usd, 2),
                "value_usd": round(value_usd, 2)
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching ETH balance: {str(e)}")

    async def _get_erc20_tokens(self, address: str, client: httpx.AsyncClient) -> List[Dict]:
        """Fetch ERC20 tokens and their USD values."""
        url = f"{self.base_url}/api/v2/addresses/{address}/tokens"
        try:
            r = await client.get(url)
            r.raise_for_status()
            data = r.json()

            # First pass: collect tokens and balances
            raw_tokens = []
            addresses_for_pricing: List[str] = []
            items = data.get("items", []) if isinstance(data, dict) else data
            for token in items:
                token_info = token.get("token", {}) or {}
                symbol = (token_info.get("symbol") or "UNKNOWN").upper()
                token_address = (token_info.get("address") or "").lower()

                # Skip ETH duplicates from token list
                if symbol == "ETH":
                    continue

                decimals_raw = token_info.get("decimals")
                try:
                    decimals = int(decimals_raw) if decimals_raw is not None else 18
                except Exception:
                    decimals = 18

                # Blockscout may expose token quantity under different fields
                quantity_raw = token.get("value")
                if quantity_raw is None:
                    quantity_raw = token.get("balance")
                if quantity_raw is None:
                    quantity_raw = 0

                quantity = self._to_float(quantity_raw, 0.0)
                balance = quantity / (10 ** decimals)

                raw_tokens.append({
                    "symbol": symbol,
                    "address": token_address,
                    "balance": balance
                })
                if token_address:
                    addresses_for_pricing.append(token_address)

            # Fetch prices from CoinGecko by contract address (mainnet only)
            cg_prices: Dict[str, float] = {}
            if self.network == "mainnet" and addresses_for_pricing:
                cg_prices = await self._get_coingecko_token_prices_by_contract(addresses_for_pricing, client)

            # Build final tokens with price/value, fallback to Blockscout when needed
            tokens: List[Dict] = []
            for t in raw_tokens:
                addr = (t.get("address") or "").lower()
                price_usd = self._to_float(cg_prices.get(addr), 0.0)
                if not price_usd and addr:
                    # last resort fallback
                    try:
                        price_usd = await self._fetch_token_price_usd(addr, client)
                    except Exception:
                        price_usd = 0.0
                value_usd = (t["balance"] * price_usd) if price_usd else 0.0
                tokens.append({
                    "symbol": t["symbol"],
                    "balance": round(t["balance"], 6),
                    "price_usd": round(price_usd, 2),
                    "value_usd": round(value_usd, 2)
                })

            return tokens

        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code,
                                detail=f"Error fetching ERC20 tokens: {e.response.text}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching ERC20 tokens: {str(e)}")

    async def _fetch_token_price_usd(self, token_address: str, client: httpx.AsyncClient) -> float:
        """Fetch token USD price from Blockscout token endpoint with multiple fallbacks."""
        if not token_address:
            return 0.0
        url = f"{self.base_url}/api/v2/tokens/{token_address}"
        try:
            r = await client.get(url)
            if r.status_code != 200:
                return 0.0
            data = r.json()

            # Try common shapes
            candidates = [
                data.get("usd_value"),
                data.get("price"),           # could be dict
                data.get("exchange_rate"),
            ]
            for c in candidates:
                price = self._to_float(c, 0.0)
                if price:
                    return price

            # Derive from market_cap / total_supply if available
            market_cap = self._to_float(data.get("market_cap"), 0.0)
            total_supply = self._to_float(data.get("total_supply"), 0.0)
            if market_cap and total_supply:
                try:
                    return market_cap / total_supply if total_supply > 0 else 0.0
                except Exception:
                    return 0.0

            # Some responses may nest price info
            market_data = data.get("market_data") or {}
            nested_candidates = [
                market_data.get("price_usd"),
                market_data.get("price"),
                market_data.get("rate"),
            ]
            for c in nested_candidates:
                price = self._to_float(c, 0.0)
                if price:
                    return price

            return 0.0
        except Exception:
            return 0.0

    async def _get_coingecko_eth_price(self, client: httpx.AsyncClient) -> float:
        """Get ETH price in USD from CoinGecko."""
        try:
            url = f"{self.coingecko_api}/simple/price?ids=ethereum&vs_currencies=usd"
            r = await client.get(url, timeout=20.0)
            if r.status_code == 200:
                data = r.json() or {}
                return float(((data.get("ethereum") or {}).get("usd")) or 0.0)
        except Exception:
            pass
        return 0.0

    async def _get_coingecko_token_prices_by_contract(self, addresses: List[str], client: httpx.AsyncClient) -> Dict[str, float]:
        """Get token prices by contract address via CoinGecko (mainnet only). Returns mapping of address(lower)->price."""
        result: Dict[str, float] = {}
        if not addresses:
            return result
        # CoinGecko supports up to ~100 ids per request; batch if needed
        BATCH = 80
        try:
            for i in range(0, len(addresses), BATCH):
                batch = [a.lower() for a in addresses[i:i+BATCH] if a]
                if not batch:
                    continue
                contracts = ",".join(batch)
                url = f"{self.coingecko_api}/simple/token_price/ethereum?contract_addresses={contracts}&vs_currencies=usd"
                r = await client.get(url, timeout=25.0)
                if r.status_code == 200:
                    data = r.json() or {}
                    # data is mapping {contract: {usd: price}}
                    for k, v in data.items():
                        try:
                            price = float((v or {}).get("usd") or 0.0)
                            if price:
                                result[k.lower()] = price
                        except Exception:
                            continue
        except Exception:
            return result
        return result

    async def get_wallet_positions(self, address: str) -> Dict:
        """Aggregate ETH and ERC20 token balances into a formatted response."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                eth_task = self._get_eth_balance(address, client)
                tokens_task = self._get_erc20_tokens(address, client)
                eth_result, tokens_result = await asyncio.gather(eth_task, tokens_task)

            positions = [eth_result] + tokens_result
            global_value_usd = round(sum(self._to_float(p.get("value_usd"), 0.0) for p in positions), 2)

            return {
                "positions": positions,
                "global_value_usd": global_value_usd
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
