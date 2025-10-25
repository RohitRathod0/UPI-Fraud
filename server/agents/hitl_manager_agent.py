

from typing import Dict, Any

class HITLManagerAgent:
    def __init__(self):
        self.trust_thresholds = {
            "borderline_block": (35, 45),
            "borderline_warn": (55, 65),
            "high_value_threshold": 50000
        }
    
    async def evaluate(
        self,
        transaction_id: str,
        trust_score: float,
        action: str,
        detector_results: Dict[str, Any],
        transaction_amount: float
    ) -> Dict[str, Any]:
        subscores = [r["subscore"] for r in detector_results.values()]
        variance = max(subscores) - min(subscores)
        
        triggers = []
        priority = "LOW"
        
        if self.trust_thresholds["borderline_block"][0] <= trust_score <= self.trust_thresholds["borderline_block"][1]:
            triggers.append("Borderline BLOCK case")
            priority = "HIGH"
        
        if variance > 0.5:
            triggers.append("High variance in detector scores")
            priority = "MEDIUM"
        
        if transaction_amount > self.trust_thresholds["high_value_threshold"] and 40 <= trust_score <= 60:
            triggers.append(f"High-value with medium risk")
            priority = "CRITICAL"
        
        avg_confidence = sum(r["confidence"] for r in detector_results.values()) / len(detector_results)
        if avg_confidence < 0.6:
            triggers.append("Low overall confidence")
        
        human_review_required = len(triggers) > 0
        
        return {
            "human_review_required": human_review_required,
            "priority": priority if human_review_required else None,
            "triggers": triggers
        }
