"""
Trust Score Aggregation Agent
Combines 4 detector subscores into final Trust Score (0-100)
"""

from typing import Dict, Any

class TrustScoreAgent:
    def __init__(self):
        # Weights for each detector (must sum to 1.0)
        self.weights = {
            'phishing': 0.30,
            'quishing': 0.25,
            'collect': 0.25,
            'malware': 0.20
        }
        
        # Confidence weighting factor
        self.confidence_weight = 0.3
    
    def compute_trust_score(
        self,
        phishing_score: float,
        phishing_confidence: float,
        quishing_score: float,
        quishing_confidence: float,
        collect_score: float,
        collect_confidence: float,
        malware_score: float,
        malware_confidence: float
    ) -> Dict[str, Any]:
        """
        Aggregate subscores into Trust Score (0-100)
        
        Formula:
        1. Calculate weighted average of risk scores
        2. Adjust by confidence (low confidence = move toward 50)
        3. Convert to trust score: Trust = 100 * (1 - risk)
        4. Determine action: ALLOW (>65), WARN (45-65), BLOCK (<45)
        """
        
        # Step 1: Weighted average of risk scores
        subscores = {
            'phishing': phishing_score,
            'quishing': quishing_score,
            'collect': collect_score,
            'malware': malware_score
        }
        
        confidences = {
            'phishing': phishing_confidence,
            'quishing': quishing_confidence,
            'collect': collect_confidence,
            'malware': malware_confidence
        }
        
        # Confidence-weighted aggregation
        weighted_risk = 0.0
        total_weight = 0.0
        
        for detector, risk_score in subscores.items():
            confidence = confidences[detector]
            base_weight = self.weights[detector]
            
            # Adjust weight by confidence
            adjusted_weight = base_weight * (1 + self.confidence_weight * (confidence - 0.5))
            
            weighted_risk += adjusted_weight * risk_score
            total_weight += adjusted_weight
        
        # Normalize
        if total_weight > 0:
            final_risk = weighted_risk / total_weight
        else:
            final_risk = 0.5  # Default to uncertain
        
        # Step 2: Calculate aggregate confidence
        aggregate_confidence = sum(confidences.values()) / len(confidences)
        
        # Step 3: Adjust for low confidence (regression to mean)
        if aggregate_confidence < 0.7:
            uncertainty_factor = (0.7 - aggregate_confidence) / 0.7
            final_risk = final_risk * (1 - uncertainty_factor * 0.5) + 0.5 * uncertainty_factor
        
        # Step 4: Convert to Trust Score (0-100, higher = more trustworthy)
        trust_score = 100 * (1 - final_risk)
        trust_score = max(0, min(100, trust_score))  # Clamp to [0, 100]
        
        # Step 5: Determine action
        action = self._determine_action(trust_score, aggregate_confidence)
        
        return {
            'trust_score': round(trust_score, 2),
            'final_risk': round(final_risk, 3),
            'aggregate_confidence': round(aggregate_confidence, 3),
            'action': action,
            'subscore_weights_used': self.weights
        }
    
    def _determine_action(self, trust_score: float, confidence: float) -> str:
        """
        Determine action based on trust score
        
        ALLOW: Trust > 65 (low risk)
        WARN: Trust 45-65 (medium risk)
        BLOCK: Trust < 45 (high risk)
        """
        
        if trust_score >= 65:
            return "ALLOW"
        elif trust_score >= 45:
            return "WARN"
        else:
            return "BLOCK"
