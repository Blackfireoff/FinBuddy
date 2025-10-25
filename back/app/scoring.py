from typing import Dict, Optional, List

class EnhancedTransactionScorer:
    """
    Enhanced V2 transaction scorer:
      - Market context (cohort percentiles on gas/tip) with fallbacks
      - EIP-1559 overpay ratio
      - Subscores (Economic / Technical / Risk / Strategic)
      - Confidence score and human-readable explanations
    """

    def __init__(self, wallet: str):
        self.wallet = wallet.lower()

    # -------------------------
    # Internal helpers
    # -------------------------
    @staticmethod
    def _safe_div(a: float, b: float, default: float = 0.0) -> float:
        try:
            if b == 0:
                return default
            return a / b
        except Exception:
            return default

    @staticmethod
    def _percentile_rank(x: float,
                         p50: Optional[float],
                         p80: Optional[float],
                         p95: Optional[float]) -> float:
        """
        ~0..1 position vs p50/p80/p95 (plus petit = meilleur marché).
        """
        if p50 is None:
            return 0.5
        # x <= p50 → 0.3..0.5
        if x <= p50:
            return 0.3 + 0.2 * (x / max(p50, 1))
        # p50..p80 → 0.5..0.8
        if p80 is None:
            p80 = 1.2 * p50
        if x <= p80:
            return 0.5 + 0.3 * EnhancedTransactionScorer._safe_div((x - p50), (p80 - p50), 0.0)
        # p80..p95 → 0.8..0.95
        if p95 is None:
            p95 = 1.3 * p80
        if x <= p95:
            return 0.8 + 0.15 * EnhancedTransactionScorer._safe_div((x - p80), (p95 - p80), 0.0)
        # > p95 → ~1
        return 0.98

    # -------------------------
    # Main API
    # -------------------------
    def score_transaction_enhanced_v2(
        self,
        tx: Dict,
        enhanced_data: Dict,
        cohort_stats: Optional[Dict] = None
    ) -> Dict:
        """
        V2 scoring using cohort percentiles, overpay ratio, and explicit confidence & explanations.
        """
        import json

        explanations: List[Dict] = []

        # -------- Extract base fields
        gas_used  = float(tx.get("gasUsed") or 0)
        gas_limit = float(tx.get("gasLimit") or 0)
        effective_gp = tx.get("gasPrice") or tx.get("maxFeePerGas") or 0
        tip = tx.get("maxPriorityFeePerGas") or 0
        base_fee = tx.get("baseFeePerGas") or (cohort_stats or {}).get("base_fee_last")

        p = (cohort_stats or {}).get("pctl", {})
        eGP_p = p.get("eGP", {}) if p else {}
        tip_p = p.get("tip", {}) if p else {}

        # -------- Percentile ranks (0..1 where 1 is bad/expensive)
        rank_eGP = self._percentile_rank(float(effective_gp), eGP_p.get(50), eGP_p.get(80), eGP_p.get(95)) if effective_gp else 0.5
        rank_tip = self._percentile_rank(float(tip),         tip_p.get(50), tip_p.get(80), tip_p.get(95))         if tip         else 0.5

        # -------- Fallbacks if cohort stats are empty
        no_eGP_pctl = not bool((cohort_stats or {}).get("pctl", {}).get("eGP"))
        if no_eGP_pctl and effective_gp and (base_fee is not None):
            min_required = (float(base_fee) if base_fee else 0.0) + float(tip or 0.0)
            ratio_to_min = float(effective_gp) / max(min_required, 1.0)
            # Plus c'est proche de 1.0, mieux c'est
            if ratio_to_min <= 1.02:
                rank_eGP = 0.35
            elif ratio_to_min <= 1.10:
                rank_eGP = 0.55
            else:
                rank_eGP = 0.80

        no_tip_pctl = not bool((cohort_stats or {}).get("pctl", {}).get("tip"))
        if no_tip_pctl:
            # Tip quasi nul = plutôt bon marché
            if float(tip or 0) <= 1e6:        # <= ~0.001 gwei
                rank_tip = 0.35
            elif float(tip or 0) <= 5e9:      # <= 5 gwei
                rank_tip = 0.55
            else:
                rank_tip = 0.80



        # -------- EIP-1559 Overpay ratio
        min_required = (float(base_fee) if base_fee else 0.0) + float(tip or 0.0)
        overpay_ratio = 0.0
        if effective_gp:
            overpay_ratio = max(0.0, min(1.0, self._safe_div((float(effective_gp) - min_required), float(effective_gp), 0.0)))
        if effective_gp and base_fee is not None:
            explanations.append({
                "label": "EIP-1559 overpay ratio",
                "value": round(overpay_ratio, 4),
                "delta": -round(30.0 * overpay_ratio, 2)
            })

        # -------- Economic
        economic = 100.0 - (rank_eGP * 70.0) - (rank_tip * 20.0) - (overpay_ratio * 10.0)
        economic = max(0.0, min(100.0, economic))
        explanations.append({"label": "Economic (gas price percentile)", "value": round(rank_eGP, 3), "delta": round(-(rank_eGP*70.0), 2)})

        # -------- Technical (sweet spot 0.7..0.95)
        ratio = self._safe_div(gas_used, gas_limit, 0.0)
        technical = 100.0
        details = (enhanced_data or {}).get("transaction_details") or {}
        token_transfers = (enhanced_data or {}).get("token_transfers") or []
        tx_types = (tx.get("transaction_types") or details.get("transaction_types") or [])
        is_simple_transfer = (not token_transfers) and (str(details.get("method") or "").strip() == "") and ("coin_transfer" in tx_types)

        if ratio == 0:
            technical -= 40.0
            explanations.append({"label": "No gas used info", "delta": -40.0})
        elif ratio < 0.5:
            technical -= (0.5 - ratio) * 60.0
            explanations.append({"label": "Low gas utilization", "value": round(ratio,3), "delta": -round((0.5 - ratio) * 60.0, 2)})
        elif ratio > 0.98:
            # ne pénalise pas un simple coin_transfer (21k/21k)
            if is_simple_transfer:
                explanations.append({"label": "Exact 21k gas transfer", "value": round(ratio,3), "delta": +2.0})
                technical += 2.0
            else:
                technical -= (ratio - 0.98) * 100.0
                explanations.append({"label": "High gas utilization (risk of OOG)", "value": round(ratio,3), "delta": -round((ratio - 0.98) * 100.0, 2)})
        else:
            technical += min(5.0, (ratio - 0.7) * 20.0)
            explanations.append({"label": "Good gas utilization", "value": round(ratio,3), "delta": +min(5.0, (ratio - 0.7) * 20.0)})

        technical = max(0.0, min(100.0, technical))

        # -------- Risk (EOA vs Contract, interpreter, age)
        addr_info = (enhanced_data or {}).get("address_info") or {}
        interpreter = (enhanced_data or {}).get("interpreter_data") or {}
        risk = 100.0

        to_info = (details.get("to") if isinstance(details, dict) else {}) or {}
        to_is_contract = bool(to_info.get("is_contract"))

        # Ne pénaliser "not verified" QUE si destination est un contrat
        is_verified = False
        try:
            is_verified = bool(
                to_info.get("is_verified") or
                addr_info.get("is_verified") or
                (addr_info.get("contract") or {}).get("is_verified")
            )
        except Exception:
            pass

        if to_is_contract and not is_verified:
            risk -= 15.0
            explanations.append({"label": "Contract not verified", "delta": -15.0})

        if isinstance(interpreter, dict):
            lvl = str(interpreter.get("risk_level") or interpreter.get("level") or "").lower()
            if "high" in lvl:
                risk -= 35.0; explanations.append({"label": "Interpreter risk: HIGH", "delta": -35.0})
            elif "medium" in lvl:
                risk -= 20.0; explanations.append({"label": "Interpreter risk: MEDIUM", "delta": -20.0})
            elif "low" in lvl:
                risk -=  5.0; explanations.append({"label": "Interpreter risk: LOW", "delta":  -5.0})

        try:
            if to_is_contract and addr_info.get("creation_block_number"):
                risk -= 10.0
                explanations.append({"label": "Newly deployed contract", "delta": -10.0})
        except Exception:
            pass

        risk = max(0.0, min(100.0, risk))

        # -------- Strategic / Intent
        method = str((details.get("method") if isinstance(details, dict) else "")).lower()
        intent = "transfer"
        if token_transfers:
            if "swap" in method or ("uniswap" in json.dumps(details).lower()):
                intent = "swap"
            elif "approve" in method:
                intent = "approve"
            else:
                intent = "contract_call"

        strategic = 85.0 if intent == "transfer" else 75.0 if intent == "swap" else 60.0 if intent == "approve" else 70.0
        explanations.append({
            "label": "Gas vs required (fallback)",
            "value": {
                "effective_gwei": round(float(effective_gp) / 1e9, 6),
                "required_gwei": round(((float(base_fee) if base_fee else 0.0) + float(tip or 0.0)) / 1e9, 6)
            },
            "delta": 0
        })

        # -------- Final aggregation + confidence
        final_no_risk = 0.35 * economic + 0.25 * technical + 0.10 * strategic
        final = final_no_risk + 0.30 * risk
        final = max(0.0, min(100.0, final))
        final_no_risk = max(0.0, min(100.0, final_no_risk))

        # Confidence = proportion de signaux présents (pondérée simple)
        present = 0.0; total = 0.0
        for v in [effective_gp, tip, base_fee, gas_used, gas_limit]:
            total += 1; present += 1 if v else 0
        if interpreter:
            total += 1; present += 1
        confidence = 0.7 + 0.3 * (present / max(total, 1.0))

        if not (cohort_stats or {}).get("pctl", {}).get("eGP"):
            confidence = max(0.7, confidence - 0.05)

        if not (cohort_stats or {}).get("pctl", {}).get("tip"):
            confidence = max(0.7, confidence - 0.05)

        final *= confidence
        final = max(0.0, min(100.0, final))

        return {
            "tx_hash": tx.get("hash"),
            "subscores": {
                "economic": round(economic, 2),
                "technical": round(technical, 2),
                "risk_security": round(risk, 2),
                "strategic": round(strategic, 2),
            },
            "final_score": round(final, 2),
            "final_score_no_risk": round(final_no_risk, 2),
            "risk_level": ("high" if risk < 40 else "medium" if risk < 70 else "low"),
            "interpreter_analysis": interpreter,
            "enhanced_data": {
                **(enhanced_data or {}),
                "cohort_stats": cohort_stats or {},
                "scoring_method": "enhanced_v2"
            },
            "confidence": round(confidence, 3),
            "explanations": explanations
        }
