"""
UPI Fraud Detection API with Human-in-the-Loop
FastAPI server with 7 AI agents
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import time
from datetime import datetime
import json
import os

from schemas import TransactionRequest, FraudCheckResponse, ReviewDecision
from database import SessionLocal, Base, engine, ReviewQueue
from config import Config

# Agents
from agents.phish_agent import PhishingAgent
from agents.qr_guard_agent import QuishingAgent
from agents.collect_sense_agent import CollectRequestAgent
from agents.mal_scan_agent import MalwareAgent
from agents.trust_score_agent import TrustScoreAgent
from agents.explainer_agent import ExplainerAgent
from agents.hitl_manager_agent import HITLManagerAgent

# ------------------------------------------------------------------------------
# DB setup
# ------------------------------------------------------------------------------
Base.metadata.create_all(bind=engine)

# ------------------------------------------------------------------------------
# App setup
# ------------------------------------------------------------------------------
app = FastAPI(
    title="UPI Fraud Detection API",
    description="Pre-transaction fraud detection with Human-in-the-Loop AI agents",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if not os.path.exists('static'):
    os.makedirs('static')

app.mount("/static", StaticFiles(directory="static"), name="static")

# ------------------------------------------------------------------------------
# Agents initialization (use config for model paths)
# ------------------------------------------------------------------------------
print("Loading ML models...")
# Use config paths, fallback to relative paths for local development
model_dir = Config.MODEL_DIR if os.path.exists(Config.MODEL_DIR) else './models'
if not os.path.exists(model_dir):
    model_dir = '../models'  # Fallback for local dev

phishing_agent = PhishingAgent(model_path=os.path.join(model_dir, 'phishing_detector.pkl'))
quishing_agent = QuishingAgent(model_path=os.path.join(model_dir, 'qr_detector.pkl'))
collect_agent  = CollectRequestAgent(model_path=os.path.join(model_dir, 'collect_detector.pkl'))
malware_agent  = MalwareAgent(model_path=os.path.join(model_dir, 'malware_detector.pkl'))
trust_agent    = TrustScoreAgent()
explainer_agent = ExplainerAgent()
hitl_manager    = HITLManagerAgent()

# Try load (agents already handle load in __init__, but safe to call)
phishing_agent.load_model()
quishing_agent.load_model()
collect_agent.load_model()
malware_agent.load_model()

print("All models loaded successfully!")

# ------------------------------------------------------------------------------
# DB dependency
# ------------------------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------------------
@app.get("/")
async def root():
    """Landing page for the UPI Fraud Detection System"""
    return FileResponse('static/index.html')

@app.get("/api")
async def api_info():
    """API information endpoint"""
    return {
        "message": "UPI Fraud Detection API",
        "version": "1.0.0",
        "status": "online",
        "endpoints": {
            "health": "/health",
            "score_request": "/api/v1/score_request",
            "review_queue": "/api/v1/analyst/review_queue",
            "demo": "/pay"
        }
    }

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        queue_depth = db.query(ReviewQueue).filter(ReviewQueue.reviewed == False).count()
    except Exception as e:
        print(f"Health DB error: {e}")
        queue_depth = 0

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "agents": {
            "phishing": phishing_agent.is_loaded(),
            "quishing": quishing_agent.is_loaded(),
            "collect_request": collect_agent.is_loaded(),
            "malware": malware_agent.is_loaded()
        },
        "review_queue_depth": queue_depth
    }

@app.post("/api/v1/score_request", response_model=FraudCheckResponse)
async def score_transaction(request: TransactionRequest, db: Session = Depends(get_db)):
    """
    Score a UPI transaction for fraud risk
    Returns trust score (0-100) and action (ALLOW/WARN/BLOCK/HUMAN_REVIEW)
    """
    t0 = time.time()

    try:
        # Construct a simple object the agents can read attributes from
        transaction = type('Transaction', (), {
            'transaction_id': request.transaction_id,
            'amount': request.amount,
            'payer_vpa': request.payer_vpa,
            'payee_vpa': request.payee_vpa,
            'message': request.message or '',
            'payee_new': request.payee_new,
            'transaction_type': request.transaction_type,
            'hour': datetime.now().hour,
            'transaction_count_24h': 5,
            'avg_transaction_amount_30d': 1000
        })()

        print(f"\n=== Analyzing transaction {request.transaction_id} ===")

        # Run agents
        ph = await phishing_agent.analyze(transaction)
        print(f"Phishing score: {ph['subscore']:.2f}")

        qr = await quishing_agent.analyze(transaction)
        print(f"Quishing score: {qr['subscore']:.2f}")

        cr = await collect_agent.analyze(transaction)
        print(f"Collect score: {cr['subscore']:.2f}")

        mw = await malware_agent.analyze(transaction)
        print(f"Malware score: {mw['subscore']:.2f}")

        subs = {
            'phishing': float(ph['subscore']),
            'quishing': float(qr['subscore']),
            'collect':  float(cr['subscore']),
            'malware':  float(mw['subscore'])
        }

        indicators = {
            'phishing': ph.get('indicators', []),
            'quishing': qr.get('indicators', []),
            'collect':  cr.get('indicators', []),
            'malware':  mw.get('indicators', [])
        }

        # Aggregate with strict policy gates (TrustScoreAgent handles the gates)
        agg = trust_agent.aggregate(
            subs=subs,
            message=request.message,
            amount=float(request.amount),
            indicators_by_agent=indicators
        )

        trust_score = int(agg['trust_score'])
        action = agg['action']
        print(f"Trust Score: {trust_score}, Action: {action}")

        # HITL check (uses final trust and action)
        detector_results = {
            'phishing': ph,
            'quishing': qr,
            'collect':  cr,
            'malware':  mw
        }

        hitl_result = await hitl_manager.evaluate(
            transaction_id=request.transaction_id,
            trust_score=trust_score,
            action=action,
            detector_results=detector_results,
            transaction_amount=request.amount
        )

        if hitl_result['human_review_required']:
            entry = ReviewQueue(
                transaction_id=request.transaction_id,
                trust_score=float(trust_score),
                priority=hitl_result['priority'],
                request_data=json.dumps(request.dict()),
                subscores=json.dumps(subs),
                reviewed=False
            )
            db.add(entry)
            db.commit()
            action = "HUMAN_REVIEW"
            print(f"⚠️  Flagged for human review (Priority: {hitl_result['priority']})")

        # Explanations
        reasons = agg.get('reasons', [])
        # If you prefer ExplainerAgent, merge:
        # reasons = explainer_agent.generate_explanation(trust_score, detector_results, action)

        processing_time = int((time.time() - t0) * 1000)

        return FraudCheckResponse(
            transaction_id=request.transaction_id,
            trust_score=trust_score,
            action=action,
            confidence=None,
            human_review_required=hitl_result['human_review_required'],
            priority_level=hitl_result.get('priority'),
            reasons=reasons,
            subscores={
                'phishing': round(subs['phishing'], 3),
                'quishing': round(subs['quishing'], 3),
                'collect':  round(subs['collect'], 3),
                'malware':  round(subs['malware'], 3)
            },
            processing_time_ms=processing_time
        )

    except Exception as e:
        print(f"Error processing transaction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/analyst/review_queue")
async def get_review_queue(db: Session = Depends(get_db)):
    queue = db.query(ReviewQueue).filter(ReviewQueue.reviewed == False).order_by(
        ReviewQueue.created_at.desc()
    ).all()

    return {
        "queue_depth": len(queue),
        "items": [
            {
                "transaction_id": item.transaction_id,
                "trust_score": item.trust_score,
                "priority": item.priority,
                "created_at": item.created_at.isoformat(),
                "time_in_queue_minutes": (datetime.utcnow() - item.created_at).total_seconds() / 60
            }
            for item in queue
        ]
    }

@app.post("/api/v1/analyst/review")
async def submit_review(decision: ReviewDecision, db: Session = Depends(get_db)):
    item = db.query(ReviewQueue).filter(ReviewQueue.transaction_id == decision.transaction_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Transaction not found in review queue")

    item.reviewed = True
    item.analyst_id = decision.analyst_id
    item.decision = decision.decision
    db.commit()

    return {
        "message": "Review submitted successfully",
        "transaction_id": decision.transaction_id,
        "decision": decision.decision
    }

@app.get("/pay")
async def payment_ui():
    return FileResponse('static/upi_payment.html')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
