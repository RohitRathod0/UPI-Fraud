"""
Feedback Processor
Processes analyst feedback for model retraining
"""

from typing import Dict, Any
from datetime import datetime
import json

from database import SessionLocal, FeedbackLog

class FeedbackProcessor:
    async def process_feedback(
        self,
        transaction_id: str,
        analyst_decision: str,
        original_trust_score: float,
        feedback_text: str,
        subscores: Dict[str, Any]
    ):
        """
        Process analyst feedback and store for retraining
        
        Args:
            transaction_id: Transaction ID
            analyst_decision: APPROVE | BLOCK | ESCALATE
            original_trust_score: AI's original trust score
            feedback_text: Analyst's comments
            subscores: Original detector subscores
        """
        
        db = SessionLocal()
        
        try:
            # Determine correct label based on analyst decision
            if analyst_decision == "APPROVE":
                correct_label = 0  # Legitimate transaction
            elif analyst_decision == "BLOCK":
                correct_label = 1  # Fraud
            else:
                # ESCALATE or REQUEST_INFO - don't use for training yet
                return
            
            # Determine if model was correct
            model_predicted_fraud = original_trust_score < 50
            model_was_correct = int(model_predicted_fraud == (correct_label == 1))
            
            # Create feedback log entry
            feedback_log = FeedbackLog(
                transaction_id=transaction_id,
                original_trust_score=original_trust_score,
                original_subscores=json.dumps(subscores),
                analyst_decision=analyst_decision,
                correct_label=correct_label,
                feedback_text=feedback_text,
                model_was_correct=model_was_correct,
                created_at=datetime.utcnow(),
                used_for_retraining=0
            )
            
            db.add(feedback_log)
            db.commit()
            
            print(f"Feedback logged for {transaction_id}: Model {'correct' if model_was_correct else 'incorrect'}")
            
            # Update analyst metrics
            await self._update_analyst_metrics(db, analyst_decision, model_was_correct)
            
        except Exception as e:
            print(f"Error processing feedback: {str(e)}")
            db.rollback()
        finally:
            db.close()
    
    async def _update_analyst_metrics(self, db, analyst_id: str, was_correct: bool):
        """Update analyst performance metrics"""
        # Implementation for analyst performance tracking
        # Would increment counters in AnalystMetrics table
        pass
    
    async def get_retraining_data(self, min_samples: int = 100) -> Dict[str, Any]:
        """
        Get feedback data for model retraining
        
        Returns transactions with analyst labels that haven't been used for retraining
        """
        db = SessionLocal()
        
        try:
            feedback_items = db.query(FeedbackLog).filter(
                FeedbackLog.used_for_retraining == 0
            ).limit(min_samples * 2).all()
            
            if len(feedback_items) < min_samples:
                print(f"Insufficient feedback data for retraining ({len(feedback_items)} < {min_samples})")
                return None
            
            retraining_data = {
                'transaction_ids': [item.transaction_id for item in feedback_items],
                'labels': [item.correct_label for item in feedback_items],
                'original_scores': [item.original_trust_score for item in feedback_items],
                'count': len(feedback_items)
            }
            
            return retraining_data
            
        finally:
            db.close()
    
    async def mark_used_for_retraining(self, transaction_ids: list):
        """Mark feedback entries as used for retraining"""
        db = SessionLocal()
        
        try:
            db.query(FeedbackLog).filter(
                FeedbackLog.transaction_id.in_(transaction_ids)
            ).update({'used_for_retraining': 1})
            
            db.commit()
            print(f"Marked {len(transaction_ids)} feedback entries as used for retraining")
            
        finally:
            db.close()
