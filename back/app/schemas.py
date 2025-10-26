from typing import List, Dict, Optional
from pydantic import BaseModel

class Subscores(BaseModel):
    economic: float
    technical: float
    risk_security: float
    strategic: float

class ScoredTx(BaseModel):
    tx_hash: str
    subscores: Subscores
    final_score: float
    final_score_no_risk: Optional[float] = None
    risk_level: Optional[str] = None
    interpreter_analysis: Optional[Dict] = None
    enhanced_data: Optional[Dict] = None
    confidence: Optional[float] = None
    explanations: Optional[List[Dict]] = None

class ExplainRequest(BaseModel):
    network: str
    address: str
    scored_transactions: List[ScoredTx]

class PerDimExplanation(BaseModel):
    why: str
    how_to_improve: str

class TxExplanation(BaseModel):
    tx_hash: str
    per_dimension: Dict[str, PerDimExplanation]
    overall_comment: str
    scores: Dict

class ExplainResponse(BaseModel):
    network: str
    address: str
    model: str
    explanations: List[TxExplanation]