"""
Explainer Agent
Generates human-readable explanations for fraud decisions with feature importance
"""

from typing import Dict, Any, List
import math

class ExplainerAgent:
    def generate_explanation(
        self,
        trust_score: float,
        detector_results: Dict[str, Dict[str, Any]],
        action: str,
        subscores: Dict[str, float] = None,
        transaction_data: Dict[str, Any] = None
    ) -> List[str]:
        """
        Generate human-readable explanations with feature importance
        
        Returns list of reason strings for UI display
        """
        
        reasons = []
        
        # Overall risk assessment
        risk_level = self._get_risk_level(trust_score)
        if trust_score >= 80:
            reasons.append(f"Transaction appears safe (Risk Level: {risk_level})")
        elif trust_score >= 65:
            reasons.append(f"Transaction has low-medium risk (Risk Level: {risk_level})")
        elif trust_score >= 45:
            reasons.append(f"Transaction has medium risk (Risk Level: {risk_level})")
        elif trust_score >= 30:
            reasons.append(f"Transaction has high risk (Risk Level: {risk_level})")
        else:
            reasons.append(f"Transaction has critical risk (Risk Level: {risk_level})")
        
        # Add specific detector findings with importance
        detector_risks = []
        for detector_name, result in detector_results.items():
            subscore = result.get('subscore', 0)
            risk_percentage = subscore * 100
            indicators = result.get('indicators', [])
            
            if subscore > 0.5:
                detector_label = self._get_detector_label(detector_name)
                detector_risks.append({
                    'name': detector_label,
                    'score': risk_percentage,
                    'indicators': indicators
                })
        
        # Sort by risk score (highest first)
        detector_risks.sort(key=lambda x: x['score'], reverse=True)
        
        # Add top risk detectors
        for det in detector_risks[:3]:  # Top 3 riskiest
            if det['score'] > 70:
                reasons.append(f"{det['name']}: {det['score']:.0f}% risk")
                reasons.extend([f"  • {ind}" for ind in det['indicators'][:2]])
            elif det['score'] > 40:
                reasons.append(f"{det['name']}: {det['score']:.0f}% risk")
                if det['indicators']:
                    reasons.append(f"  • {det['indicators'][0]}")
        
        # Add transaction-specific insights
        if transaction_data:
            amount = transaction_data.get('amount', 0)
            if amount > 50000:
                reasons.append(f"High transaction amount: ₹{amount:,.0f}")
            if transaction_data.get('payee_new', 0) == 1:
                reasons.append("Payee is new/unknown to you")
        
        # Add action-specific guidance
        if action == "BLOCK":
            reasons.append("🔒 Transaction BLOCKED for your protection")
            reasons.append("→ If legitimate, contact customer support with transaction ID")
        elif action == "WARN":
            reasons.append("⚠️ Proceed with CAUTION")
            reasons.append("→ Verify payee details before confirming")
        elif action == "ALLOW":
            reasons.append("Safe to proceed with payment")
        elif action == "HUMAN_REVIEW":
            reasons.append("👤 Under review by security team")
            reasons.append("→ Decision typically within 5 minutes")
        
        return reasons
    
    def _get_detector_label(self, detector_name: str) -> str:
        """Get friendly name for detector"""
        labels = {
            'phishing': 'Phishing/Social Engineering',
            'quishing': 'Malicious QR Code (Quishing)',
            'collect': 'Collect Request Exploit',
            'malware': 'Malware/Device Compromise'
        }
        return labels.get(detector_name, detector_name.title())
    
    def generate_detailed_report(
        self,
        trust_score: float,
        detector_results: Dict[str, Dict[str, Any]],
        action: str,
        subscores: Dict[str, float] = None,
        transaction_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate detailed JSON report with feature importance for visualization"""
        
        risk_level = self._get_risk_level(trust_score)
        
        report = {
            'summary': f"Trust Score: {trust_score:.0f}/100 - Action: {action}",
            'risk_level': risk_level,
            'risk_percentage': round(100 - trust_score, 1),  # Risk = 100 - trust
            'trust_score': round(trust_score, 1),
            'detector_breakdown': [],
            'feature_importance': [],
            'top_risk_factors': [],
            'recommendations': [],
            'risk_breakdown': {}
        }
        
        # Detector breakdown with importance
        detector_list = []
        for detector_name, result in detector_results.items():
            risk_score = result.get('subscore', 0) * 100
            detector_list.append({
                'detector': self._get_detector_label(detector_name),
                'detector_key': detector_name,
                'risk_score': round(risk_score, 1),
                'confidence': round(result.get('confidence', 0) * 100, 1),
                'indicators': result.get('indicators', []),
                'importance': round(risk_score, 1)  # Importance = risk score
            })
        
        # Sort by risk score
        detector_list.sort(key=lambda x: x['risk_score'], reverse=True)
        report['detector_breakdown'] = detector_list
        
        # Feature importance (from subscores)
        if subscores:
            feature_importance = []
            for feature_name, score in subscores.items():
                risk_pct = score * 100
                feature_importance.append({
                    'feature': self._get_detector_label(feature_name),
                    'feature_key': feature_name,
                    'importance': round(risk_pct, 1),
                    'contribution': round(risk_pct / len(subscores), 1) if subscores else 0
                })
            
            # Sort by importance
            feature_importance.sort(key=lambda x: x['importance'], reverse=True)
            report['feature_importance'] = feature_importance
            
            # Risk breakdown for pie chart
            report['risk_breakdown'] = {
                feature['feature_key']: feature['importance'] 
                for feature in feature_importance
            }
        
        # Extract top risk factors
        all_indicators = []
        for result in detector_results.values():
            for indicator in result.get('indicators', []):
                all_indicators.append({
                    'indicator': indicator,
                    'severity': 'high' if len(indicator) > 50 else 'medium'
                })
        
        report['top_risk_factors'] = all_indicators[:5]  # Top 5
        
        # Transaction insights
        if transaction_data:
            report['transaction_insights'] = {
                'amount': transaction_data.get('amount', 0),
                'amount_risk': 'high' if transaction_data.get('amount', 0) > 50000 else 'normal',
                'payee_new': transaction_data.get('payee_new', 0) == 1,
                'transaction_type': transaction_data.get('transaction_type', 'pay')
            }
        
        # Recommendations
        if action == "BLOCK":
            report['recommendations'] = [
                "Do not proceed with this transaction",
                "Report suspicious activity to your bank",
                "Change UPI PIN if credentials may be compromised",
                "Review recent transactions for unauthorized activity"
            ]
        elif action == "WARN":
            report['recommendations'] = [
                "Verify payee identity through alternative channel",
                "Confirm transaction details are correct",
                "Check for suspicious indicators before proceeding",
                "Contact payee directly if possible"
            ]
        elif action == "ALLOW":
            report['recommendations'] = [
                "Transaction appears safe to proceed",
                "Always verify payee details",
                "Keep transaction confirmation for records",
                "Monitor account for any unusual activity"
            ]
        elif action == "HUMAN_REVIEW":
            report['recommendations'] = [
                "Transaction is under security review",
                "Decision will be made within 5 minutes",
                "You will be notified of the outcome",
                "Do not attempt the transaction again until approved"
            ]
        
        return report
    
    def _get_risk_level(self, trust_score: float) -> str:
        """Convert trust score to risk level label"""
        if trust_score >= 80:
            return "LOW"
        elif trust_score >= 65:
            return "LOW-MEDIUM"
        elif trust_score >= 45:
            return "MEDIUM"
        elif trust_score >= 30:
            return "HIGH"
        else:
            return "CRITICAL"
