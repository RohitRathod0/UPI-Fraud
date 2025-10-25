# You're in server directory already
# Create schemas.py with content


from pydantic import BaseModel, Field
from typing import Optional, Dict, List

class TransactionRequest(BaseModel):
    transaction_id: str
    payer_vpa: str
    payee_vpa: str
    amount: float = Field(..., gt=0)
    message: Optional[str] = None
    transaction_type: Optional[str] = "pay"
    payee_new: Optional[int] = Field(0, ge=0, le=1)

class FraudCheckResponse(BaseModel):
    transaction_id: str
    trust_score: int = Field(..., ge=0, le=100)
    action: str
    confidence: float
    human_review_required: bool
    priority_level: Optional[str] = None
    reasons: List[str]
    subscores: Dict[str, float]
    processing_time_ms: int

class ReviewDecision(BaseModel):
    transaction_id: str
    analyst_id: str
    decision: str
    feedback: Optional[str] = None
