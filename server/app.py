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
from agents.phish_agent import PhishingAgent
from agents.qr_guard_agent import QuishingAgent
from agents.collect_sense_agent import CollectRequestAgent
from agents.mal_scan_agent import MalwareAgent
from agents.trust_score_agent import TrustScoreAgent
from agents.explainer_agent import ExplainerAgent
from agents.hitl_manager_agent import HITLManagerAgent

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="UPI Fraud Detection API",
    description="Pre-transaction fraud detection with Human-in-the-Loop AI agents",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
if not os.path.exists('static'):
    os.makedirs('static')

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
# Initialize all agents
print("Loading ML models...")
phishing_agent = PhishingAgent(model_path='../models/phishing_detector.pkl')
quishing_agent = QuishingAgent(model_path='../models/qr_detector.pkl')
collect_agent = CollectRequestAgent(model_path='../models/collect_detector.pkl')
malware_agent = MalwareAgent(model_path='../models/malware_detector.pkl')
trust_score_agent = TrustScoreAgent()
explainer_agent = ExplainerAgent()
hitl_manager = HITLManagerAgent()

# Load models
phishing_agent.load_model()
quishing_agent.load_model()
collect_agent.load_model()
malware_agent.load_model()

print("All models loaded successfully!")

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def root():
    return {
        "message": "UPI Fraud Detection API",
        "version": "1.0.0",
        "status": "online"
    }

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
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
async def score_transaction(
    request: TransactionRequest,
    db: Session = Depends(get_db)
):
    """
    Score a UPI transaction for fraud risk
    
    Returns trust score (0-100) and action (ALLOW/WARN/BLOCK/HUMAN_REVIEW)
    """
    start_time = time.time()
    
    try:
        # Mock transaction object
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
        
        # Run all 4 fraud detectors
        print(f"\n=== Analyzing transaction {request.transaction_id} ===")
        
        phishing_result = await phishing_agent.analyze(transaction)
        print(f"Phishing score: {phishing_result['subscore']:.2f}")
        
        quishing_result = await quishing_agent.analyze(transaction)
        print(f"Quishing score: {quishing_result['subscore']:.2f}")
        
        collect_result = await collect_agent.analyze(transaction)
        print(f"Collect score: {collect_result['subscore']:.2f}")
        
        malware_result = await malware_agent.analyze(transaction)
        print(f"Malware score: {malware_result['subscore']:.2f}")
        
        # Aggregate into trust score
        trust_result = trust_score_agent.compute_trust_score(
            phishing_score=phishing_result['subscore'],
            phishing_confidence=phishing_result['confidence'],
            quishing_score=quishing_result['subscore'],
            quishing_confidence=quishing_result['confidence'],
            collect_score=collect_result['subscore'],
            collect_confidence=collect_result['confidence'],
            malware_score=malware_result['subscore'],
            malware_confidence=malware_result['confidence']
        )
        
        trust_score = trust_result['trust_score']
        action = trust_result['action']
        aggregate_confidence = trust_result['aggregate_confidence']
        
        print(f"Trust Score: {trust_score}, Action: {action}")
        
        # Check if human review needed
        detector_results = {
            'phishing': phishing_result,
            'quishing': quishing_result,
            'collect': collect_result,
            'malware': malware_result
        }
        
        hitl_result = await hitl_manager.evaluate(
            transaction_id=request.transaction_id,
            trust_score=trust_score,
            action=action,
            detector_results=detector_results,
            transaction_amount=request.amount
        )
        
        if hitl_result['human_review_required']:
            # Add to review queue
            review_entry = ReviewQueue(
                transaction_id=request.transaction_id,
                trust_score=float(trust_score),
                priority=hitl_result['priority'],
                request_data=json.dumps(request.dict()),
                subscores=json.dumps({
                    'phishing': float(phishing_result['subscore']),
                    'quishing': float(quishing_result['subscore']),
                    'collect': float(collect_result['subscore']),
                    'malware': float(malware_result['subscore'])
                }),
                reviewed=False
            )
            db.add(review_entry)
            db.commit()
            
            action = "HUMAN_REVIEW"
            print(f"⚠️  Flagged for human review (Priority: {hitl_result['priority']})")
        
        # Generate explanations
        reasons = explainer_agent.generate_explanation(
            trust_score=trust_score,
            detector_results=detector_results,
            action=action
        )
        
        # Calculate processing time
        processing_time = int((time.time() - start_time) * 1000)
        
        return FraudCheckResponse(
            transaction_id=request.transaction_id,
            trust_score=int(trust_score),
            action=action,
            confidence=aggregate_confidence,
            human_review_required=hitl_result['human_review_required'],
            priority_level=hitl_result.get('priority'),
            reasons=reasons,
            subscores={
                'phishing': round(phishing_result['subscore'], 3),
                'quishing': round(quishing_result['subscore'], 3),
                'collect': round(collect_result['subscore'], 3),
                'malware': round(malware_result['subscore'], 3)
            },
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        print(f"Error processing transaction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/analyst/review_queue")
async def get_review_queue(db: Session = Depends(get_db)):
    """Get all transactions pending human review"""
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
async def submit_review(
    decision: ReviewDecision,
    db: Session = Depends(get_db)
):
    """Analyst submits review decision"""
    queue_item = db.query(ReviewQueue).filter(
        ReviewQueue.transaction_id == decision.transaction_id
    ).first()
    
    if not queue_item:
        raise HTTPException(status_code=404, detail="Transaction not found in review queue")
    
    queue_item.reviewed = True
    queue_item.analyst_id = decision.analyst_id
    queue_item.decision = decision.decision
    
    db.commit()
    
    return {
        "message": "Review submitted successfully",
        "transaction_id": decision.transaction_id,
        "decision": decision.decision
    }

@app.get("/pay")
async def payment_ui():
    """Serve the payment UI"""
    return FileResponse('static/upi_payment.html')
   

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
