import math
from typing import Dict


class TransactionScorer:
    def __init__(self, wallet: str):
        self.wallet = wallet.lower()

    def economic_efficiency_score(self, tx: Dict) -> float:
        gas_cost_eth = tx["gasUsed"] * tx["gasPrice"] * 1e-9
        profit_eth = tx.get("profitEth", 0.0)
        roi = profit_eth / (tx["valueEth"] + 1e-12)
        gas_efficiency = tx["valueEth"] / (gas_cost_eth + 1e-12)
        roi_score = max(0, min(10, 5 + roi * 50))
        gas_score = max(0, min(10, math.log1p(gas_efficiency)))
        return round(roi_score * 0.6 + gas_score * 0.4, 2)

    def technical_efficiency_score(self, tx: Dict) -> float:
        gas_ratio = tx["gasUsed"] / tx["gasLimit"] if tx["gasLimit"] > 0 else 1
        efficiency_score = (1 - abs(gas_ratio - 0.7)) * 10
        eip_1559_bonus = 1.0 if tx["gasPrice"] < 40 else 0.0
        return round(min(10, efficiency_score + eip_1559_bonus), 2)

    def risk_security_score(self, tx: Dict) -> float:
        score = 5.0
        if tx.get("isVerifiedContract", False):
            score += 3
        if tx.get("isKnownProtocol", False):
            score += 2
        if "0x000" in (tx.get("to") or ""):
            score -= 5
        return max(0, min(10, score))

    def strategic_alignment_score(self, tx: Dict) -> float:
        tx_type = tx.get("type", "transfer")
        if tx_type in ["stake", "lp_deposit"]:
            return 9.0
        elif tx_type in ["swap", "transfer"]:
            return 6.0
        elif tx_type in ["mint_nft", "speculative"]:
            return 4.0
        else:
            return 5.0

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
