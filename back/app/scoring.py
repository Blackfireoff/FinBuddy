import math
from typing import Dict, Optional, List


class TransactionScorer:
    def __init__(self, wallet: str):
        self.wallet = wallet.lower()

    def economic_efficiency_score(self, tx: Dict) -> float:
        # Convert gas cost to ETH (gas_used * gas_price in wei, then convert to ETH)
        gas_cost_eth = tx["gasUsed"] * tx["gasPrice"] / 1e18
        profit_eth = tx.get("profitEth", 0.0)
        
        # Calculate ROI based on transaction value
        tx_value_eth = tx["valueEth"]
        if tx_value_eth > 0:
            roi = profit_eth / tx_value_eth
        else:
            roi = 0.0
            
        # Gas efficiency: value transferred per unit of gas cost
        if gas_cost_eth > 0:
            gas_efficiency = tx_value_eth / gas_cost_eth
        else:
            gas_efficiency = 0.0
            
        # ROI score (0-10 scale)
        roi_score = max(0, min(10, 5 + roi * 2))  # Adjusted multiplier for more reasonable scoring
        
        # Gas efficiency score (0-10 scale)
        gas_score = max(0, min(10, math.log1p(gas_efficiency)))
        
        return round(roi_score * 0.6 + gas_score * 0.4, 2)

    def technical_efficiency_score(self, tx: Dict) -> float:
        # Gas usage efficiency: how well the gas limit was utilized
        gas_ratio = tx["gasUsed"] / tx["gasLimit"] if tx["gasLimit"] > 0 else 1
        # Optimal gas usage is around 70-90% of limit
        if 0.7 <= gas_ratio <= 0.9:
            efficiency_score = 10.0
        elif 0.5 <= gas_ratio < 0.7 or 0.9 < gas_ratio <= 1.0:
            efficiency_score = 7.0
        else:
            efficiency_score = 4.0
            
        # EIP-1559 bonus: lower gas prices indicate better fee management
        # Convert gas price from wei to gwei for comparison
        gas_price_gwei = tx["gasPrice"] / 1e9
        eip_1559_bonus = 2.0 if gas_price_gwei < 20 else 1.0 if gas_price_gwei < 50 else 0.0
        
        # Type 2 transaction bonus (EIP-1559)
        tx_type = tx.get("type", 0)
        type_bonus = 1.0 if tx_type == 2 else 0.0
        
        return round(min(10, efficiency_score + eip_1559_bonus + type_bonus), 2)

    def risk_security_score(self, tx: Dict) -> float:
        score = 5.0  # Base score
        
        # Contract verification bonus
        if tx.get("isVerifiedContract", False):
            score += 3.0
            
        # Known protocol bonus
        if tx.get("isKnownProtocol", False):
            score += 2.0
            
        # Scam detection - major penalty
        if tx.get("isScam", False):
            score -= 8.0  # Severe penalty for known scam addresses
            
        # Address reputation check
        to_address = tx.get("to", "")
        if to_address:
            # Check for suspicious patterns
            if "0x000" in to_address:
                score -= 5.0
            # Check for known scam patterns
            if to_address.startswith("0x00000000000"):
                score -= 3.0
                
        # Transaction status check
        if tx.get("status") == "ok":
            score += 1.0
        elif tx.get("status") == "failed":
            score -= 2.0
            
        # Check for contract creation (higher risk)
        if tx.get("created_contract"):
            score -= 1.0
            
        # Check for error in internal transactions
        if tx.get("has_error_in_internal_transactions", False):
            score -= 2.0
            
        return max(0, min(10, score))

    def strategic_alignment_score(self, tx: Dict) -> float:
        # Get transaction type from transaction_types array
        tx_types = tx.get("transaction_types", ["coin_transfer"])
        tx_type = tx_types[0] if tx_types else "coin_transfer"
        
        # Strategic scoring based on transaction type
        if tx_type in ["stake", "lp_deposit", "yield_farming"]:
            return 9.0  # High strategic value
        elif tx_type in ["swap", "coin_transfer", "defi_interaction"]:
            return 7.0  # Good strategic value
        elif tx_type in ["nft_mint", "nft_transfer"]:
            return 5.0  # Medium strategic value
        elif tx_type in ["contract_interaction", "token_transfer"]:
            return 6.0  # Moderate strategic value
        elif tx_type in ["speculative", "gambling"]:
            return 3.0  # Low strategic value
        else:
            return 5.0  # Default neutral score

    def score_transaction(self, tx: Dict) -> Dict:
        economic = self.economic_efficiency_score(tx)
        technical = self.technical_efficiency_score(tx)
        risk = self.risk_security_score(tx)
        strategic = self.strategic_alignment_score(tx)
        final_score = round(
            economic * 0.3 + technical * 0.2 + risk * 0.3 + strategic * 0.2, 2
        )
        final_score_no_risk = round(
            economic * 0.4 + technical * 0.3 + strategic * 0.3, 2
        )
        return {
            "tx_hash": tx.get("hash"),
            "scores": {
                "economic": economic,
                "technical": technical,
                "risk_security": risk,
                "strategic": strategic,
            },
            "final_score": final_score,
            "final_score_no_risk": final_score_no_risk,
        }


class EnhancedTransactionScorer:
    """
    Enhanced transaction scorer with comprehensive blockchain data analysis.
    Integrates with Blockscout API data for maximum accuracy.
    """
    
    def __init__(self, wallet: str):
        self.wallet = wallet.lower()
    
    def calculate_enhanced_economic_score(self, tx: Dict, address_info: Dict = None, 
                                        token_transfers: List[Dict] = None) -> float:
        """Calculate enhanced economic score using comprehensive data."""
        score = 5.0
        
        # Gas efficiency with real-time data
        gas_cost_eth = tx["gasUsed"] * tx["gasPrice"] / 1e18
        tx_value_eth = tx["valueEth"]
        
        if gas_cost_eth > 0:
            gas_efficiency = tx_value_eth / gas_cost_eth
            score = min(10, math.log1p(gas_efficiency) * 2)
        
        # Address balance analysis from API data
        if address_info:
            balance_wei = int(address_info.get("balance", "0"))
            balance_eth = balance_wei / 1e18
            
            # High balance addresses get bonus
            if balance_eth > 10:
                score += 1.0
            elif balance_eth > 1:
                score += 0.5
            elif balance_eth < 0.01:
                score -= 0.5
        
        # Token activity analysis
        if token_transfers:
            recent_transfers = len([t for t in token_transfers if t.get("timestamp")])
            if recent_transfers > 10:  # Active address
                score += 1.0
            elif recent_transfers < 2:  # Inactive address
                score -= 0.5
        
        # Fee optimization analysis
        gas_price_gwei = tx["gasPrice"] / 1e9
        if gas_price_gwei < 5:  # Excellent fee management
            score += 3.0
        elif gas_price_gwei < 15:  # Good fee management
            score += 2.0
        elif gas_price_gwei < 30:  # Average fee management
            score += 1.0
        elif gas_price_gwei > 100:  # Poor fee management
            score -= 2.0
        
        return round(min(10, max(0, score)), 2)
    
    def calculate_enhanced_technical_score(self, tx: Dict, tx_details: Dict = None, 
                                         tx_logs: List[Dict] = None) -> float:
        """Calculate enhanced technical score using comprehensive data."""
        score = 5.0
        
        # Gas usage optimization
        gas_ratio = tx["gasUsed"] / tx["gasLimit"] if tx["gasLimit"] > 0 else 1
        
        # Optimal gas usage (70-90% is ideal)
        if 0.7 <= gas_ratio <= 0.9:
            score += 3.0
        elif 0.5 <= gas_ratio < 0.7 or 0.9 < gas_ratio <= 1.0:
            score += 1.5
        elif gas_ratio < 0.5:  # Under-utilized gas
            score -= 1.0
        elif gas_ratio > 1.0:  # Over-limit (shouldn't happen)
            score -= 3.0
        
        # EIP-1559 optimization
        tx_type = tx.get("type", 0)
        if tx_type == 2:  # EIP-1559 transaction
            score += 2.0
            
            # Priority fee optimization
            max_priority_fee = tx.get("maxPriorityFeePerGas", 0)
            if max_priority_fee > 0:
                priority_fee_gwei = max_priority_fee / 1e9
                if priority_fee_gwei < 1:  # Excellent
                    score += 2.0
                elif priority_fee_gwei < 3:  # Good
                    score += 1.0
                elif priority_fee_gwei > 10:  # Poor
                    score -= 1.0
        
        # Transaction complexity analysis
        if tx_details:
            method = tx_details.get("method")
            if method and method != "0x":
                # Complex transaction
                if len(method) > 20:
                    score += 1.0
                elif len(method) > 10:
                    score += 0.5
        
        # Event analysis from logs
        if tx_logs:
            event_count = len(tx_logs)
            if event_count > 5:  # Complex transaction
                score += 1.0
            elif event_count == 0:  # Simple transfer
                score += 0.5
        
        # Transaction status
        if tx.get("status") == "ok":
            score += 1.0
        elif tx.get("status") == "failed":
            score -= 3.0
        
        return round(min(10, max(0, score)), 2)
    
    def calculate_enhanced_risk_score(self, tx: Dict, address_info: Dict = None, 
                                    tx_details: Dict = None) -> float:
        """Calculate enhanced risk score using comprehensive data."""
        score = 5.0
        
        # Contract verification analysis
        if tx.get("isVerifiedContract", False):
            score += 3.0
        elif address_info and address_info.get("is_verified", False):
            score += 3.0
        
        # Protocol reputation analysis
        if tx.get("isKnownProtocol", False):
            score += 2.0
        elif address_info:
            name = address_info.get("name")
            public_tags = address_info.get("public_tags", [])
            if name or public_tags:
                score += 2.0
        
        # Scam detection (highest priority)
        if tx.get("isScam", False):
            score -= 8.0
        elif address_info and address_info.get("is_scam", False):
            score -= 8.0
        
        # Address reputation analysis
        if address_info:
            reputation = address_info.get("reputation", "unknown")
            if reputation == "trusted":
                score += 3.0
            elif reputation == "suspicious":
                score -= 2.0
            elif reputation == "scam":
                score -= 8.0
        
        # Transaction status and error analysis
        if tx.get("status") == "ok":
            score += 1.0
        elif tx.get("status") == "failed":
            score -= 3.0
        
        # Contract creation risk
        if tx.get("created_contract"):
            score -= 2.0
        
        # Internal transaction errors
        if tx.get("has_error_in_internal_transactions", False):
            score -= 3.0
        
        # Address activity and experience
        if address_info:
            tx_count = address_info.get("transactions_count", 0)
            if tx_count > 1000:  # Very experienced
                score += 1.0
            elif tx_count < 5:  # Very new
                score -= 1.0
        
        # Suspicious address patterns
        to_address = tx.get("to", "")
        if to_address:
            if "0x000" in to_address:
                score -= 5.0
            if to_address.startswith("0x00000000000"):
                score -= 3.0
        
        return round(min(10, max(0, score)), 2)
    
    def calculate_enhanced_strategic_score(self, tx: Dict, token_transfers: List[Dict] = None,
                                        interpreter_data: Dict = None) -> float:
        """Calculate enhanced strategic score using interpreter API data."""
        score = 5.0
        
        # Use interpreter API data for enhanced analysis
        if interpreter_data:
            # Analyze interpreter classification
            classification = interpreter_data.get("classification", "").lower()
            if "defi" in classification or "swap" in classification:
                score += 2.0
            elif "staking" in classification or "yield" in classification:
                score += 3.0
            elif "nft" in classification:
                score += 1.0
            elif "gambling" in classification or "casino" in classification:
                score -= 2.0
            elif "scam" in classification or "suspicious" in classification:
                score -= 4.0
            
            # Analyze interpreter confidence
            confidence = interpreter_data.get("confidence", 0)
            if confidence > 0.8:  # High confidence
                score += 1.0
            elif confidence < 0.3:  # Low confidence
                score -= 0.5
        
        # Transaction type analysis
        tx_types = tx.get("transaction_types", ["coin_transfer"])
        tx_type = tx_types[0] if tx_types else "coin_transfer"
        
        type_scores = {
            "stake": 9.0,
            "lp_deposit": 9.0,
            "yield_farming": 9.0,
            "defi_interaction": 8.0,
            "swap": 7.0,
            "coin_transfer": 6.0,
            "token_transfer": 6.0,
            "contract_interaction": 6.0,
            "nft_mint": 5.0,
            "nft_transfer": 5.0,
            "speculative": 3.0,
            "gambling": 2.0
        }
        
        base_score = type_scores.get(tx_type, 5.0)
        score = max(score, base_score)  # Use higher of interpreter or type score
        
        # Token transfer analysis
        if token_transfers:
            defi_tokens = 0
            stable_tokens = 0
            speculative_tokens = 0
            
            for transfer in token_transfers[:10]:
                token_symbol = transfer.get("token", {}).get("symbol", "").upper()
                if token_symbol in ["USDC", "USDT", "DAI", "BUSD", "FRAX"]:
                    stable_tokens += 1
                elif token_symbol in ["UNI", "AAVE", "COMP", "MKR", "CRV", "SUSHI"]:
                    defi_tokens += 1
                else:
                    speculative_tokens += 1
            
            if defi_tokens > 0:
                score += min(2.0, defi_tokens * 0.5)
            if stable_tokens > 0:
                score += min(1.0, stable_tokens * 0.2)
            if speculative_tokens > 3:
                score -= min(2.0, (speculative_tokens - 3) * 0.5)
        
        return round(min(10, max(0, score)), 2)
    
    def score_transaction_enhanced(self, tx: Dict, api_data: Dict) -> Dict:
        """
        Enhanced transaction scoring using comprehensive API data.
        This is the main scoring method that integrates all data sources.
        """
        # Extract data from API results
        address_info = api_data.get("address_info", {})
        token_transfers = api_data.get("token_transfers", [])
        tx_details = api_data.get("transaction_details", {})
        interpreter_data = api_data.get("interpreter_data", {})
        tx_logs = api_data.get("transaction_logs", [])
        
        # Calculate enhanced scores
        economic = self.calculate_enhanced_economic_score(tx, address_info, token_transfers)
        technical = self.calculate_enhanced_technical_score(tx, tx_details, tx_logs)
        risk = self.calculate_enhanced_risk_score(tx, address_info, tx_details)
        strategic = self.calculate_enhanced_strategic_score(tx, token_transfers, interpreter_data)
        
        # Calculate final scores
        final_score = round(
            economic * 0.3 + technical * 0.2 + risk * 0.3 + strategic * 0.2, 2
        )
        final_score_no_risk = round(
            economic * 0.4 + technical * 0.3 + strategic * 0.3, 2
        )
        
        # Risk level assessment
        risk_level = "low"
        if risk < 3:
            risk_level = "high"
        elif risk < 6:
            risk_level = "medium"
        
        # Enhanced analysis with interpreter insights
        interpreter_insights = {}
        if interpreter_data:
            interpreter_insights = {
                "classification": interpreter_data.get("classification", "unknown"),
                "confidence": interpreter_data.get("confidence", 0),
                "description": interpreter_data.get("description", ""),
                "risk_assessment": interpreter_data.get("risk_level", "unknown")
            }
        
        return {
            "tx_hash": tx.get("hash"),
            "scores": {
                "economic": economic,
                "technical": technical,
                "risk_security": risk,
                "strategic": strategic,
            },
            "final_score": final_score,
            "final_score_no_risk": final_score_no_risk,
            "risk_level": risk_level,
            "interpreter_analysis": interpreter_insights,
            "enhanced_data": {
                "address_info": address_info,
                "token_transfers_count": len(token_transfers),
                "transaction_details": tx_details,
                "scoring_method": "enhanced_blockscout_with_interpreter"
            }
        }
