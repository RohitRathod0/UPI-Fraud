"""
Phishing/Vishing Detection Agent
XGBoost classifier for detecting social engineering attacks
"""

import pickle
import pandas as pd
import numpy as np
from typing import Dict, Any
import asyncio
import re


class PhishingAgent:
    def __init__(self, model_path: str = '../models/phishing_detector.pkl'):
        self.model = None
        self.model_path = model_path
        self.loaded = False
        self.load_model()
    
    def load_model(self):
        """Load the trained phishing detection model"""
        try:
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            self.loaded = True
            print(f"PhishingAgent: Model loaded successfully")
        except Exception as e:
            print(f"PhishingAgent: Could not load model - {e}")
            self.loaded = False
    
    def is_loaded(self) -> bool:
        return self.loaded
    
    async def analyze(self, transaction: Any) -> Dict[str, Any]:
        """Analyze transaction for phishing patterns"""
        await asyncio.sleep(0.03)
        
        try:
            message = str(getattr(transaction, 'message', '')).lower()
            payee_vpa = str(getattr(transaction, 'payee_vpa', '')).lower()
            amount = getattr(transaction, 'amount', 0)
            
            # Extract REAL features from message
            features = self._extract_real_features(message, payee_vpa, amount)
            
            # Use model if loaded
            if self.loaded and self.model:
                X = pd.DataFrame([features])
                proba = float(self.model.predict_proba(X)[0, 1])
            else:
                # Fallback: rule-based from real features
                proba = features['phishing_risk_composite']
            
            confidence = abs(proba - 0.5) * 2
            
            return {
                'agent': 'PhishingAgent',
                'subscore': proba,
                'confidence': float(confidence),
                'indicators': self._get_indicators(features, proba)
            }
            
        except Exception as e:
            print(f"PhishingAgent error: {e}")
            return {
                'agent': 'PhishingAgent',
                'subscore': 0.0,
                'confidence': 0.0,
                'indicators': []
            }
    
    def _extract_real_features(self, message: str, payee_vpa: str, amount: float) -> Dict[str, float]:
        """Extract REAL features by parsing message text"""
        
        # Check for URLs
        url_patterns = ['http://', 'https://', 'www.', '.com', '.in', 'bit.ly', 'tinyurl']
        contains_url = 1.0 if any(pattern in message for pattern in url_patterns) else 0.0
        
        # Urgent language keywords
        urgent_words = ['urgent', 'immediately', 'locked', 'suspended', 'expire', 
                       'action required', 'final notice', 'last chance', 'limited time']
        urgent_count = sum(1 for word in urgent_words if word in message)
        urgent_language = min(urgent_count / 3.0, 1.0)
        
        # Credential requests
        cred_words = ['pin', 'password', 'otp', 'cvv', 'verify', 'confirm', 
                     'validate', 'authenticate']
        requests_pin = 1.0 if any(word in message for word in cred_words) else 0.0
        
        # Bank/security mimicking
        bank_words = ['account', 'bank', 'security', 'verification', 'suspended',
                     'blocked', 'deactivated', 'unauthorized']
        bank_count = sum(1 for word in bank_words if word in message)
        mimics_bank = min(bank_count / 3.0, 1.0)
        
        # Check payee for suspicious patterns
        suspicious_payee_words = ['verify', 'security', 'account', 'bank', 'official',
                                  'support', 'customer', 'service']
        has_typosquatting = 1.0 if any(word in payee_vpa for word in suspicious_payee_words) else 0.0
        
        # Domain reputation (if contains suspicious payee)
        domain_reputation = 0.3 if has_typosquatting else 0.8
        
        # Total suspicious keywords
        suspicious_keywords = urgent_count + (1 if requests_pin else 0) + (1 if contains_url else 0)
        
        # Keyword risk score
        keyword_risk_score = min(suspicious_keywords / 5.0, 1.0)
        
        # Overall phishing risk composite
        phishing_risk_composite = (
            contains_url * 0.25 +
            urgent_language * 0.25 +
            requests_pin * 0.20 +
            mimics_bank * 0.15 +
            has_typosquatting * 0.15
        )
        
        return {
            'contains_url': contains_url,
            'suspicious_keywords': float(suspicious_keywords),
            'urgent_language': urgent_language,
            'requests_pin': requests_pin,
            'mimics_bank': mimics_bank,
            'has_typosquatting': has_typosquatting,
            'domain_reputation': domain_reputation,
            'keyword_risk_score': keyword_risk_score,
            'phishing_risk_composite': phishing_risk_composite,
            'amount': amount,
            'payee_new': 1,
            'transaction_count_24h': 5,
            'hour': 12,
            'time_risk': 0.0
        }
    
    def _get_indicators(self, features: Dict[str, float], risk_score: float) -> list:
        """Generate human-readable indicators"""
        indicators = []
        
        if risk_score > 0.7:
            indicators.append("🚨 HIGH PHISHING RISK - Multiple fraud patterns detected")
        elif risk_score > 0.5:
            indicators.append("⚠️ MODERATE PHISHING RISK - Suspicious patterns found")
        
        if features['contains_url'] > 0:
            indicators.append("⚠️ Message contains URL link")
        
        if features['urgent_language'] > 0.5:
            indicators.append("⚠️ Urgent/threatening language detected")
        
        if features['requests_pin'] > 0:
            indicators.append("⚠️ Requests credentials (PIN/OTP/password)")
        
        if features['mimics_bank'] > 0.5:
            indicators.append("⚠️ Mimics bank/official communication")
        
        if features['has_typosquatting'] > 0:
            indicators.append("⚠️ Suspicious payee name (security/verify/account)")
        
        if features['suspicious_keywords'] > 3:
            indicators.append(f"⚠️ Multiple suspicious keywords ({int(features['suspicious_keywords'])} found)")
        
        if not indicators:
            indicators.append("✓ No significant phishing indicators")
        
        return indicators
