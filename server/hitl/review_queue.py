"""
Review Queue Manager
Manages priority queue for human review
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json

from database import SessionLocal, ReviewQueue

class ReviewQueue:
    def __init__(self):
        self.priority_order = {'CRITICAL': 1, 'HIGH': 2, 'MEDIUM': 3, 'LOW': 4}
    
    async def add_to_queue(
        self,
        transaction_id: str,
        request_data: dict,
        trust_score: float,
        confidence: float,
        priority: str,
        detector_results: dict,
        reasons: list
    ) -> ReviewQueue:
        """Add transaction to review queue"""
        
        db = SessionLocal()
        
        try:
            queue_item = ReviewQueue(
                transaction_id=transaction_id,
                request_data=json.dumps(request_data),
                trust_score=trust_score,
                confidence=confidence,
                priority=priority,
                detector_results=json.dumps(detector_results),
                reasons=json.dumps(reasons),
                status='pending',
                created_at=datetime.utcnow(),
                sla_deadline=self._calculate_sla_deadline(priority)
            )
            
            db.add(queue_item)
            db.commit()
            db.refresh(queue_item)
            
            print(f"Added transaction {transaction_id} to review queue (Priority: {priority})")
            
            return queue_item
        
        finally:
            db.close()
    
    async def get_queue(
        self,
        priority: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get pending items from review queue"""
        
        db = SessionLocal()
        
        try:
            query = db.query(ReviewQueue).filter(ReviewQueue.status == 'pending')
            
            if priority:
                query = query.filter(ReviewQueue.priority == priority)
            
            # Order by priority, then by creation time
            items = query.order_by(
                ReviewQueue.priority_order,
                ReviewQueue.created_at
            ).limit(limit).all()
            
            return [self._format_queue_item(item) for item in items]
        
        finally:
            db.close()
    
    async def get_queue_depth(self) -> int:
        """Get total number of pending reviews"""
        db = SessionLocal()
        try:
            return db.query(ReviewQueue).filter(ReviewQueue.status == 'pending').count()
        finally:
            db.close()
    
    async def get_overdue_items(self) -> List[Dict[str, Any]]:
        """Get items past SLA deadline"""
        db = SessionLocal()
        
        try:
            items = db.query(ReviewQueue).filter(
                ReviewQueue.status == 'pending',
                ReviewQueue.sla_deadline < datetime.utcnow()
            ).all()
            
            return [self._format_queue_item(item) for item in items]
        
        finally:
            db.close()
    
    async def assign_to_analyst(self, transaction_id: str, analyst_id: str):
        """Assign review to specific analyst"""
        db = SessionLocal()
        
        try:
            item = db.query(ReviewQueue).filter(
                ReviewQueue.transaction_id == transaction_id
            ).first()
            
            if item:
                item.assigned_to = analyst_id
                item.assigned_at = datetime.utcnow()
                db.commit()
        
        finally:
            db.close()
    
    def _calculate_sla_deadline(self, priority: str) -> datetime:
        """Calculate SLA deadline based on priority"""
        sla_minutes = {
            'CRITICAL': 2,
            'HIGH': 10,
            'MEDIUM': 30,
            'LOW': 1440  # 24 hours
        }
        
        minutes = sla_minutes.get(priority, 30)
        return datetime.utcnow() + timedelta(minutes=minutes)
    
    def _format_queue_item(self, item: ReviewQueue) -> Dict[str, Any]:
        """Format queue item for API response"""
        return {
            'id': item.id,
            'transaction_id': item.transaction_id,
            'trust_score': item.trust_score,
            'confidence': item.confidence,
            'priority': item.priority,
            'status': item.status,
            'created_at': item.created_at.isoformat(),
            'sla_deadline': item.sla_deadline.isoformat(),
            'time_in_queue_minutes': (datetime.utcnow() - item.created_at).total_seconds() / 60,
            'overdue': datetime.utcnow() > item.sla_deadline,
            'assigned_to': item.assigned_to,
            'request_data': json.loads(item.request_data),
            'detector_results': json.loads(item.detector_results),
            'reasons': json.loads(item.reasons)
        }
