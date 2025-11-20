from pydantic import BaseModel, Field
from typing import Optional, Dict, List


# -----------------------------
# Request/Response Schemas
# -----------------------------

class TransactionRequest(BaseModel):
    transaction_id: str = Field(..., min_length=1, description="Unique transaction identifier")
    payer_vpa: str = Field(..., min_length=3, description="Payer UPI ID")
    payee_vpa: str = Field(..., min_length=3, description="Payee UPI ID")
    amount: float = Field(..., gt=0, description="Transaction amount in INR")
    # Message MUST be required for fraud pattern analysis
    message: str = Field(..., min_length=4, description="Required; used for phishing/quishing/collect/malware analysis")
    transaction_type: str = Field(default="pay", description="pay | qr_pay | collect")
    payee_new: int = Field(default=1, ge=0, le=1, description="1 if payee is new/unknown to user")


class FraudCheckResponse(BaseModel):
    transaction_id: str
    trust_score: int
    action: str  # ALLOW | WARN | BLOCK | HUMAN_REVIEW
    confidence: Optional[float] = None
    human_review_required: Optional[bool] = None
    priority_level: Optional[str] = None
    reasons: List[str]
    subscores: Dict[str, float]
    processing_time_ms: Optional[int] = None
    risk_breakdown: Optional[Dict[str, Any]] = None  # Detailed risk analysis
    feature_importance: Optional[List[Dict[str, Any]]] = None  # Feature importance scores


# -----------------------------
# Analyst/HITL Schemas
# -----------------------------

# Pydantic v2: use 'pattern' instead of 'regex'
class ReviewDecision(BaseModel):
    transaction_id: str = Field(..., min_length=1, description="Transaction id in review queue")
    analyst_id: str = Field(..., min_length=1, description="Analyst identifier")
    decision: str = Field(
        ...,
        pattern="^(APPROVE|REJECT|ESCALATE)$",
        description="Decision for the queued transaction"
    )
