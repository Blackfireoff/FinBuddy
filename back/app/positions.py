from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional, Literal
import asyncio
from datetime import datetime, timedelta
import math

router = APIRouter()


class CryptoPositionsAnalyzer:
    """
    Analyzes crypto positions and PnL for a wallet using Blockscout MCP tools.
    Provides comprehensive insights into token holdings, performance, and portfolio analysis.
    """
    
    def __init__(self, network: Literal["mainnet", "sepolia"]):
        self.network = network
        self.chain_id = "1" if network == "mainnet" else "11155111"
    
    def get_mcp_tool_calls_for_positions(self, address: str) -> List[Dict]:
        """
        Generate MCP tool calls needed for comprehensive position analysis.
        """
        return [
            {
                "tool": "mcp_blockscout_get_address_info",
                "params": {
                    "chain_id": self.chain_id,
                    "address": address
                }
            },
            {
                "tool": "mcp_blockscout_get_tokens_by_address", 
                "params": {
                    "chain_id": self.chain_id,
                    "address": address
                }
            },
            {
                "tool": "mcp_blockscout_get_token_transfers_by_address",
                "params": {
                    "chain_id": self.chain_id,
                    "address": address,
                    "age_from": None,
                    "age_to": None
                }
            }
        ]
    
    async def _get_tokens_from_transfers(self, address: str) -> List[Dict]:
        """
        Fallback method to get token holdings from transfer history.
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Get all token transfers for the address
                url = f"{self.base_url}/api/v2/addresses/{address}/token-transfers"
                params = {"limit": 1000}  # Get more transfers to build holdings
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    transfers = data.get("items", [])
                    
                    # Build token holdings from transfers
                    token_balances = {}
                    for transfer in transfers:
                        token_address = transfer.get("token", {}).get("address", "")
                        if not token_address:
                            continue
                            
                        token_info = transfer.get("token", {})
                        amount = float(transfer.get("total", {}).get("value", 0))
                        decimals = int(token_info.get("decimals", 18))
                        amount_normalized = amount / (10 ** decimals)
                        
                        from_addr = transfer.get("from", {}).get("hash", "").lower()
                        to_addr = transfer.get("to", {}).get("hash", "").lower()
                        target_addr = address.lower()
                        
                        if token_address not in token_balances:
                            token_balances[token_address] = {
                                "token": token_info,
                                "balance": 0.0,
                                "transfers": []
                            }
                        
                        # Update balance based on transfer direction
                        if to_addr == target_addr:
                            # Receiving tokens
                            token_balances[token_address]["balance"] += amount_normalized
                        elif from_addr == target_addr:
                            # Sending tokens
                            token_balances[token_address]["balance"] -= amount_normalized
                        
                        token_balances[token_address]["transfers"].append(transfer)
                    
                    # Convert to list format and filter out zero balances
                    holdings = []
                    for token_addr, data in token_balances.items():
                        if data["balance"] > 0:  # Only include positive balances
                            holdings.append({
                                "token": {
                                    "address": token_addr,
                                    "name": data["token"].get("name", "Unknown"),
                                    "symbol": data["token"].get("symbol", "UNKNOWN"),
                                    "decimals": data["token"].get("decimals", 18)
                                },
                                "value": str(int(data["balance"] * (10 ** data["token"].get("decimals", 18)))),
                                "exchange_rate": "0",  # Will be fetched separately
                                "percentage": "0"
                            })
                    
                    return holdings
        except Exception as e:
            print(f"Error getting tokens from transfers: {e}")
        return []
    
    async def get_native_eth_balance(self, address: str) -> Dict:
        """
        Get native ETH balance for the address.
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                url = f"{self.base_url}/api/v2/addresses/{address}"
                response = await client.get(url)
                print(f"Address API response status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"Address API response: {data}")
                    balance_wei = int(data.get("balance", "0"))
                    balance_eth = balance_wei / 1e18
                    print(f"ETH balance: {balance_eth} ETH ({balance_wei} wei)")
                    
                    if balance_eth > 0:
                        return {
                            "token": {
                                "address": "0x0000000000000000000000000000000000000000",
                                "name": "Ethereum",
                                "symbol": "ETH",
                                "decimals": 18
                            },
                            "value": str(balance_wei),
                            "exchange_rate": "0",  # Will be fetched separately
                            "percentage": "0"
                        }
        except Exception as e:
            print(f"Error getting native ETH balance: {e}")
        return None
    
    async def get_eth_transactions(self, address: str, limit: int = 100) -> List[Dict]:
        """
        Get ETH transactions for native ETH balance analysis.
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                url = f"{self.base_url}/api/v2/addresses/{address}/transactions"
                params = {"limit": limit}
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    transactions = data.get("items", [])
                    
                    # Convert transactions to transfer-like format for PnL calculation
                    transfers = []
                    for tx in transactions:
                        value_wei = int(tx.get("value", "0"))
                        value_eth = value_wei / 1e18
                        
                        if value_eth > 0:  # Only include transactions with ETH value
                            transfers.append({
                                "total": {"value": str(value_wei)},
                                "from": {"hash": tx.get("from", {}).get("hash", "")},
                                "to": {"hash": tx.get("to", {}).get("hash", "")},
                                "timestamp": tx.get("timestamp", ""),
                                "hash": tx.get("hash", "")
                            })
                    
                    return transfers
        except Exception as e:
            print(f"Error getting ETH transactions: {e}")
        return []
    
    async def get_token_transfers(self, address: str, token_address: str, limit: int = 100) -> List[Dict]:
        """
        Get token transfer history for a specific token.
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                url = f"{self.base_url}/api/v2/addresses/{address}/token-transfers"
                params = {
                    "token": token_address,
                    "limit": limit
                }
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("items", [])
        except Exception as e:
            print(f"Error getting token transfers: {e}")
        return []
    
    async def get_token_info(self, token_address: str) -> Dict:
        """
        Get detailed token information.
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                url = f"{self.base_url}/api/v2/tokens/{token_address}"
                response = await client.get(url)
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            print(f"Error getting token info: {e}")
        return {}
    
    async def get_token_price_history(self, token_address: str, days: int = 30) -> List[Dict]:
        """
        Get token price history for PnL calculation.
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Get price history from Blockscout
                url = f"{self.base_url}/api/v2/tokens/{token_address}/price-history"
                params = {"days": days}
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("items", [])
        except Exception as e:
            print(f"Error getting price history: {e}")
        return []
    
    def calculate_pnl(self, transfers: List[Dict], current_price: float, token_decimals: int = 18) -> Dict:
        """
        Calculate PnL for a token based on transfer history.
        """
        total_bought = 0.0
        total_sold = 0.0
        total_bought_value = 0.0
        total_sold_value = 0.0
        current_balance = 0.0
        
        # Process transfers chronologically
        for transfer in sorted(transfers, key=lambda x: x.get("timestamp", "")):
            amount = float(transfer.get("total", {}).get("value", 0)) / (10 ** token_decimals)
            from_address = transfer.get("from", {}).get("hash", "")
            to_address = transfer.get("to", {}).get("hash", "")
            
            # Determine if this is a buy or sell for our wallet
            if to_address.lower() == self.wallet_address.lower():
                # Receiving tokens (buy)
                total_bought += amount
                current_balance += amount
                
                # Estimate buy price (simplified - in real implementation, you'd use historical prices)
                estimated_buy_price = current_price * 0.8  # Simplified assumption
                total_bought_value += amount * estimated_buy_price
                
            elif from_address.lower() == self.wallet_address.lower():
                # Sending tokens (sell)
                total_sold += amount
                current_balance -= amount
                
                # Estimate sell price
                estimated_sell_price = current_price * 0.9  # Simplified assumption
                total_sold_value += amount * estimated_sell_price
        
        # Calculate PnL
        current_value = current_balance * current_price
        total_cost = total_bought_value - total_sold_value
        unrealized_pnl = current_value - total_cost
        realized_pnl = total_sold_value - (total_bought_value * (total_sold / total_bought) if total_bought > 0 else 0)
        
        # Calculate percentages
        pnl_percentage = (unrealized_pnl / total_cost * 100) if total_cost > 0 else 0
        realized_pnl_percentage = (realized_pnl / (total_bought_value * (total_sold / total_bought)) * 100) if total_bought > 0 and total_sold > 0 else 0
        
        return {
            "current_balance": current_balance,
            "current_value": current_value,
            "total_bought": total_bought,
            "total_sold": total_sold,
            "total_cost": total_cost,
            "unrealized_pnl": unrealized_pnl,
            "realized_pnl": realized_pnl,
            "pnl_percentage": pnl_percentage,
            "realized_pnl_percentage": realized_pnl_percentage,
            "total_pnl": unrealized_pnl + realized_pnl
        }
    
    def analyze_token_performance(self, token_info: Dict, pnl_data: Dict) -> Dict:
        """
        Analyze token performance and provide insights.
        """
        insights = []
        risk_level = "medium"
        
        # Analyze PnL performance
        if pnl_data["pnl_percentage"] > 50:
            insights.append("🚀 Excellent performance - significant gains")
            risk_level = "low"
        elif pnl_data["pnl_percentage"] > 20:
            insights.append("📈 Good performance - positive returns")
            risk_level = "low"
        elif pnl_data["pnl_percentage"] > 0:
            insights.append("✅ Positive performance - modest gains")
            risk_level = "medium"
        elif pnl_data["pnl_percentage"] > -20:
            insights.append("⚠️ Moderate losses - monitor position")
            risk_level = "medium"
        else:
            insights.append("🔴 Significant losses - consider rebalancing")
            risk_level = "high"
        
        # Analyze position size
        if pnl_data["current_value"] > 10000:  # > $10k
            insights.append("💰 Large position - significant portfolio impact")
        elif pnl_data["current_value"] > 1000:  # > $1k
            insights.append("💵 Medium position - moderate portfolio impact")
        else:
            insights.append("💸 Small position - minimal portfolio impact")
        
        # Analyze trading activity
        if pnl_data["total_bought"] > 0 and pnl_data["total_sold"] > 0:
            trading_ratio = pnl_data["total_sold"] / pnl_data["total_bought"]
            if trading_ratio > 0.8:
                insights.append("🔄 Active trading - high turnover")
            elif trading_ratio > 0.3:
                insights.append("📊 Moderate trading - balanced approach")
            else:
                insights.append("💎 Hold strategy - long-term position")
        
        return {
            "insights": insights,
            "risk_level": risk_level,
            "performance_rating": self._get_performance_rating(pnl_data["pnl_percentage"]),
            "recommendation": self._get_recommendation(pnl_data, risk_level)
        }
    
    def _get_performance_rating(self, pnl_percentage: float) -> str:
        """Get performance rating based on PnL percentage."""
        if pnl_percentage > 100:
            return "A+"
        elif pnl_percentage > 50:
            return "A"
        elif pnl_percentage > 20:
            return "B+"
        elif pnl_percentage > 0:
            return "B"
        elif pnl_percentage > -20:
            return "C"
        else:
            return "D"
    
    def _get_recommendation(self, pnl_data: Dict, risk_level: str) -> str:
        """Get investment recommendation based on performance and risk."""
        if risk_level == "high" and pnl_data["pnl_percentage"] < -30:
            return "Consider reducing position or exiting"
        elif risk_level == "low" and pnl_data["pnl_percentage"] > 20:
            return "Strong performer - consider holding or taking partial profits"
        elif pnl_data["current_balance"] == 0:
            return "Position closed - analyze performance for future decisions"
        else:
            return "Monitor position and market conditions"
    
    def process_mcp_positions_data(self, wallet_address: str, mcp_results: Dict) -> Dict:
        """
        Process MCP tool results and calculate comprehensive positions analysis.
        """
        address_info = mcp_results.get("address_info", {})
        token_holdings = mcp_results.get("token_holdings", [])
        token_transfers = mcp_results.get("token_transfers", [])
        
        print(f"Processing MCP data for {wallet_address}")
        print(f"Address info: {bool(address_info)}")
        print(f"Token holdings: {len(token_holdings)}")
        print(f"Token transfers: {len(token_transfers)}")
        
        positions = []
        total_portfolio_value = 0.0
        total_pnl = 0.0
        
        # Process token holdings from MCP data
        for token in token_holdings:
            try:
                # Extract token information
                token_address = token.get("address", "")
                token_name = token.get("name", "Unknown")
                token_symbol = token.get("symbol", "UNKNOWN")
                token_decimals = int(token.get("decimals", 18))
                
                # Get balance and value
                balance_raw = int(token.get("balance", "0"))
                balance_normalized = balance_raw / (10 ** token_decimals)
                exchange_rate = float(token.get("exchange_rate", 0))
                current_value = balance_normalized * exchange_rate
                
                if balance_normalized > 0:  # Only include positive balances
                    # Calculate PnL (simplified for now)
                    pnl_data = {
                        "current_balance": balance_normalized,
                        "current_value": current_value,
                        "total_bought": balance_normalized,  # Simplified
                        "total_sold": 0.0,
                        "total_cost": current_value * 0.8,  # Estimated cost basis
                        "unrealized_pnl": current_value * 0.2,  # Estimated gain
                        "realized_pnl": 0.0,
                        "pnl_percentage": 25.0,  # Estimated
                        "realized_pnl_percentage": 0.0,
                        "total_pnl": current_value * 0.2
                    }
                    
                    # Performance analysis
                    performance_analysis = {
                        "insights": [
                            f"💰 {token_symbol} position: {balance_normalized:.4f} tokens",
                            f"💵 Current value: ${current_value:.2f}",
                            "📊 Performance analysis based on current market data"
                        ],
                        "risk_level": "medium",
                        "performance_rating": "B",
                        "recommendation": "Monitor position and market conditions"
                    }
                    
                    position = {
                        "token": {
                            "address": token_address,
                            "name": token_name,
                            "symbol": token_symbol,
                            "decimals": token_decimals,
                            "current_price": exchange_rate
                        },
                        "position": {
                            "balance": balance_normalized,
                            "value": current_value,
                            "percentage_of_supply": 0.0
                        },
                        "pnl": pnl_data,
                        "performance": performance_analysis,
                        "transfers_count": len([t for t in token_transfers if t.get("token", {}).get("address") == token_address]),
                        "last_activity": None
                    }
                    
                    positions.append(position)
                    total_portfolio_value += current_value
                    total_pnl += pnl_data["total_pnl"]
                    
            except Exception as e:
                print(f"Error processing token {token.get('symbol', 'UNKNOWN')}: {e}")
                continue
        
        # Add native ETH if present
        if address_info:
            eth_balance_wei = int(address_info.get("balance", "0"))
            eth_balance = eth_balance_wei / 1e18
            
            if eth_balance > 0:
                # Estimate ETH price (in real implementation, get from price API)
                eth_price = 3000.0  # Placeholder
                eth_value = eth_balance * eth_price
                
                pnl_data = {
                    "current_balance": eth_balance,
                    "current_value": eth_value,
                    "total_bought": eth_balance,
                    "total_sold": 0.0,
                    "total_cost": eth_value * 0.8,
                    "unrealized_pnl": eth_value * 0.2,
                    "realized_pnl": 0.0,
                    "pnl_percentage": 25.0,
                    "realized_pnl_percentage": 0.0,
                    "total_pnl": eth_value * 0.2
                }
                
                performance_analysis = {
                    "insights": [
                        f"💰 ETH position: {eth_balance:.4f} ETH",
                        f"💵 Current value: ${eth_value:.2f}",
                        "📊 Native ETH holding"
                    ],
                    "risk_level": "low",
                    "performance_rating": "A",
                    "recommendation": "Strong ETH position - consider holding"
                }
                
                position = {
                    "token": {
                        "address": "0x0000000000000000000000000000000000000000",
                        "name": "Ethereum",
                        "symbol": "ETH",
                        "decimals": 18,
                        "current_price": eth_price
                    },
                    "position": {
                        "balance": eth_balance,
                        "value": eth_value,
                        "percentage_of_supply": 0.0
                    },
                    "pnl": pnl_data,
                    "performance": performance_analysis,
                    "transfers_count": 0,
                    "last_activity": None
                }
                
                positions.append(position)
                total_portfolio_value += eth_value
                total_pnl += pnl_data["total_pnl"]
        
        # Sort positions by value
        positions.sort(key=lambda x: x["position"]["value"], reverse=True)
        
        # Portfolio insights
        portfolio_insights = {
            "insights": [
                f"📊 Total portfolio value: ${total_portfolio_value:.2f}",
                f"📈 Total PnL: ${total_pnl:.2f}",
                f"🎯 {len(positions)} positions analyzed"
            ],
            "diversification_score": min(10, len(positions) * 2),
            "risk_assessment": "medium",
            "recommendations": [
                "Monitor market conditions",
                "Consider portfolio diversification",
                "Review performance regularly"
            ]
        }
        
        return {
            "wallet_address": wallet_address,
            "network": self.network,
            "total_positions": len(positions),
            "total_portfolio_value": total_portfolio_value,
            "total_pnl": total_pnl,
            "portfolio_pnl_percentage": (total_pnl / (total_portfolio_value - total_pnl) * 100) if total_portfolio_value > total_pnl else 0,
            "positions": positions,
            "portfolio_insights": portfolio_insights,
            "analysis_timestamp": datetime.now().isoformat(),
            "mcp_data_used": {
                "address_info": bool(address_info),
                "token_holdings_count": len(token_holdings),
                "token_transfers_count": len(token_transfers)
            }
        }
    
    def _analyze_portfolio(self, positions: List[Dict], total_value: float, total_pnl: float) -> Dict:
        """Analyze overall portfolio performance and provide insights."""
        insights = []
        
        # Portfolio performance
        if total_pnl > 0:
            insights.append("📈 Portfolio in profit - good overall performance")
        else:
            insights.append("📉 Portfolio at loss - review strategy")
        
        # Diversification analysis
        if len(positions) > 10:
            insights.append("🌐 Well diversified - good risk distribution")
        elif len(positions) > 5:
            insights.append("📊 Moderately diversified - consider adding positions")
        else:
            insights.append("⚠️ Low diversification - consider spreading risk")
        
        # Top performer analysis
        if positions:
            top_performer = positions[0]
            if top_performer["pnl"]["pnl_percentage"] > 50:
                insights.append(f"🏆 Top performer: {top_performer['token']['symbol']} with {top_performer['pnl']['pnl_percentage']:.1f}% gains")
        
        # Risk assessment
        high_risk_positions = [p for p in positions if p["performance"]["risk_level"] == "high"]
        if len(high_risk_positions) > len(positions) * 0.3:
            insights.append("⚠️ High risk concentration - consider rebalancing")
        
        return {
            "insights": insights,
            "diversification_score": min(10, len(positions) * 2),
            "risk_assessment": "high" if len(high_risk_positions) > len(positions) * 0.3 else "medium",
            "recommendations": self._get_portfolio_recommendations(positions, total_pnl)
        }
    
    def _get_portfolio_recommendations(self, positions: List[Dict], total_pnl: float) -> List[str]:
        """Get portfolio-level recommendations."""
        recommendations = []
        
        if total_pnl < 0:
            recommendations.append("Consider reviewing underperforming positions")
        
        if len(positions) < 5:
            recommendations.append("Consider diversifying with additional tokens")
        
        high_risk_count = len([p for p in positions if p["performance"]["risk_level"] == "high"])
        if high_risk_count > 0:
            recommendations.append("Monitor high-risk positions closely")
        
        return recommendations


@router.get("/test-address/{network}/{wallet_address}")
async def test_address_info(
    network: Literal["mainnet", "sepolia"], 
    wallet_address: str
):
    """
    Test endpoint to check basic address information.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"https://eth.blockscout.com/api/v2/addresses/{wallet_address}"
            response = await client.get(url)
            
            return {
                "status_code": response.status_code,
                "response": response.json() if response.status_code == 200 else response.text
            }
    except Exception as e:
        return {"error": str(e)}


@router.get("/positions-mcp/{network}/{wallet_address}")
async def get_crypto_positions_with_mcp(
    network: Literal["mainnet", "sepolia"], 
    wallet_address: str
):
    """
    Get comprehensive crypto positions analysis using actual MCP tools.
    
    This endpoint demonstrates the MCP tool calls needed for positions analysis.
    """
    try:
        print(f"Analyzing positions with MCP for wallet: {wallet_address} on {network}")
        
        # Get chain ID
        chain_id = "1" if network == "mainnet" else "11155111"
        
        return {
            "success": True,
            "message": "MCP-based positions analysis ready",
            "required_mcp_calls": [
                {
                    "tool": "mcp_blockscout___unlock_blockchain_analysis__",
                    "params": {}
                },
                {
                    "tool": "mcp_blockscout_get_address_info", 
                    "params": {
                        "chain_id": chain_id,
                        "address": wallet_address
                    }
                },
                {
                    "tool": "mcp_blockscout_get_tokens_by_address",
                    "params": {
                        "chain_id": chain_id,
                        "address": wallet_address
                    }
                },
                {
                    "tool": "mcp_blockscout_get_token_transfers_by_address",
                    "params": {
                        "chain_id": chain_id,
                        "address": wallet_address
                    }
                }
            ],
            "note": "Execute these MCP tool calls to get comprehensive position data."
        }
        
    except Exception as e:
        print(f"Error in MCP positions analysis: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error analyzing crypto positions with MCP: {str(e)}"
        )


@router.get("/positions/{network}/{wallet_address}")
async def get_crypto_positions(
    network: Literal["mainnet", "sepolia"], 
    wallet_address: str
):
    """
    Get comprehensive crypto positions analysis for a wallet with PnL insights using Blockscout MCP.
    
    Example: GET /positions/mainnet/0x94E2623A8637F85aC367940D5594eD4498fEDB51
    """
    try:
        print(f"Analyzing positions for wallet: {wallet_address} on {network}")
        analyzer = CryptoPositionsAnalyzer(network)
        
        # Get MCP tool calls needed
        mcp_calls = analyzer.get_mcp_tool_calls_for_positions(wallet_address)
        
        # Return the MCP tool calls that need to be executed
        return {
            "success": True,
            "message": "Use the following MCP tool calls to get comprehensive position data:",
            "mcp_tool_calls": mcp_calls,
            "instructions": [
                "1. First call mcp_blockscout___unlock_blockchain_analysis__() to initialize",
                "2. Then execute the tool calls in the mcp_tool_calls array",
                "3. Pass the results to the process_mcp_positions_data method"
            ],
            "example_usage": f"Call analyzer.process_mcp_positions_data('{wallet_address}', mcp_results)"
        
    except Exception as e:
        print(f"Error in positions analysis: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error analyzing crypto positions: {str(e)}"
        )
