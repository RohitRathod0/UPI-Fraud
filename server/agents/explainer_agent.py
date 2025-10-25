"""
Explainer Agent
Generates human-readable explanations for fraud decisions
"""

from typing import Dict, Any, List

class ExplainerAgent:
    def generate_explanation(
        self,
        trust_score: float,
        detector_results: Dict[str, Dict[str, Any]],
        action: str
    ) -> List[str]:
        """
        Generate human-readable explanations
        
        Returns list of reason strings for UI display
        """
        
        reasons = []
        
        # Overall risk assessment
        if trust_score >= 80:
            reasons.append("✓ Transaction appears safe (low risk)")
        elif trust_score >= 65:
            reasons.append("⚠ Transaction has low risk (proceed with caution)")
        elif trust_score >= 45:
            reasons.append("⚠ Transaction has medium risk (review details carefully)")
        else:
            reasons.append("⛔ Transaction has high fraud risk (BLOCKED)")
        
        # Add specific detector findings
        for detector_name, result in detector_results.items():
            subscore = result.get('subscore', 0)
            indicators = result.get('indicators', [])
            
            if subscore > 0.7:
                # High risk from this detector
                detector_label = self._get_detector_label(detector_name)
                reasons.append(f"⛔ {detector_label} detected:")
                reasons.extend([f"  • {ind}" for ind in indicators[:3]])  # Top 3 indicators
            
            elif subscore > 0.4 and indicators:
                # Medium risk
                detector_label = self._get_detector_label(detector_name)
                reasons.append(f"⚠ {detector_label} flagged:")
                reasons.extend([f"  • {ind}" for ind in indicators[:2]])  # Top 2 indicators
        
        # Add action-specific guidance
        if action == "BLOCK":
            reasons.append("🔒 Transaction BLOCKED for your protection")
            reasons.append("→ If legitimate, contact customer support with transaction ID")
        elif action == "WARN":
            reasons.append("⚠️ Proceed with CAUTION")
            reasons.append("→ Verify payee details before confirming")
        elif action == "ALLOW":
            reasons.append("✓ Safe to proceed with payment")
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
        action: str
    ) -> Dict[str, Any]:
        """Generate detailed JSON report for analyst dashboard"""
        
        report = {
            'summary': f"Trust Score: {trust_score:.0f}/100 - Action: {action}",
            'risk_level': self._get_risk_level(trust_score),
            'detector_breakdown': [],
            'top_risk_factors': [],
            'recommendations': []
        }
        
        # Detector breakdown
        for detector_name, result in detector_results.items():
            report['detector_breakdown'].append({
                'detector': self._get_detector_label(detector_name),
                'risk_score': round(result.get('subscore', 0) * 100, 1),
                'confidence': round(result.get('confidence', 0) * 100, 1),
                'indicators': result.get('indicators', [])
            })
        
        # Extract top risk factors
        all_indicators = []
        for result in detector_results.values():
            for indicator in result.get('indicators', []):
                all_indicators.append(indicator)
        
        report['top_risk_factors'] = all_indicators[:5]  # Top 5
        
        # Recommendations
        if action == "BLOCK":
            report['recommendations'] = [
                "Do not proceed with this transaction",
                "Report suspicious activity to your bank",
                "Change UPI PIN if credentials may be compromised"
            ]
        elif action == "WARN":
            report['recommendations'] = [
                "Verify payee identity through alternative channel",
                "Confirm transaction details are correct",
                "Check for suspicious indicators before proceeding"
            ]
        elif action == "ALLOW":
            report['recommendations'] = [
                "Transaction appears safe to proceed",
                "Always verify payee details",
                "Keep transaction confirmation for records"
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
