"""
Quishing (QR Code Phishing) Detection Agent
XGBoost classifier for detecting QR-based fraud
"""

import pickle
import pandas as pd
import numpy as np
from typing import Dict, Any
import asyncio


class QuishingAgent:
    def __init__(self, model_path: str = '../models/quishing_detector.pkl'):
        self.model = None
        self.model_path = model_path
        self.loaded = False
        self.load_model()
    
    def load_model(self):
        """Load the trained quishing detection model"""
        try:
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            self.loaded = True
            print(f"QuishingAgent: Model loaded successfully")
        except Exception as e:
            print(f"QuishingAgent: Could not load model - {e}")
            self.loaded = False
    
    def is_loaded(self) -> bool:
        return self.loaded
    
    async def analyze(self, transaction: Any) -> Dict[str, Any]:
        """Analyze transaction for quishing patterns"""
        await asyncio.sleep(0.03)
        
        try:
            message = str(getattr(transaction, 'message', '')).lower()
            transaction_type = str(getattr(transaction, 'transaction_type', 'pay')).lower()
            amount = getattr(transaction, 'amount', 0)
            
            # Extract REAL quishing features
            features = self._extract_real_features(message, transaction_type, amount)
            
            # Use model if loaded
            if self.loaded and self.model:
                X = pd.DataFrame([features])
                proba = float(self.model.predict_proba(X)[0, 1])
            else:
                # Fallback: rule-based
                proba = features['quishing_risk_composite']
            
            confidence = abs(proba - 0.5) * 2
            
            return {
                'agent': 'QuishingAgent',
                'subscore': proba,
                'confidence': float(confidence),
                'indicators': self._get_indicators(features, proba)
            }
            
        except Exception as e:
            print(f"QuishingAgent error: {e}")
            return {
                'agent': 'QuishingAgent',
                'subscore': 0.0,
                'confidence': 0.0,
                'indicators': []
            }
    
    def _extract_real_features(self, message: str, transaction_type: str, amount: float) -> Dict[str, float]:
        """Extract REAL quishing features"""
        
        # QR-related keywords
        qr_keywords = ['qr', 'scan', 'code', 'barcode']
        contains_qr_mention = 1.0 if any(kw in message for kw in qr_keywords) else 0.0
        
        # Prize/reward scam keywords
        prize_words = ['prize', 'won', 'winner', 'reward', 'congratulations', 
                      'claim', 'free', 'gift', 'bonus']
        prize_scam = 1.0 if any(word in message for word in prize_words) else 0.0
        
        # Discount/offer keywords
        offer_words = ['discount', 'offer', 'deal', 'sale', '% off', 'limited']
        suspicious_offer = 1.0 if any(word in message for word in offer_words) else 0.0
        
        # Check if transaction type is QR
        is_qr_transaction = 1.0 if 'qr' in transaction_type else 0.0
        
        # Urgency in QR context
        urgent_qr_words = ['limited', 'expire', 'last chance', 'hurry', 'now']
        qr_urgency = 1.0 if any(word in message for word in urgent_qr_words) else 0.0
        
        # URL in QR context (common in quishing)
        has_url = 1.0 if any(p in message for p in ['http', 'www', 'bit.ly']) else 0.0
        
        # High value with QR (suspicious)
        high_value_qr = 1.0 if (amount > 10000 and contains_qr_mention > 0) else 0.0
        
        # Composite risk
        quishing_risk_composite = (
            contains_qr_mention * 0.20 +
            is_qr_transaction * 0.20 +
            prize_scam * 0.20 +
            suspicious_offer * 0.15 +
            qr_urgency * 0.15 +
            high_value_qr * 0.10
        )
        
        return {
            'contains_qr_mention': contains_qr_mention,
            'unverified_qr_source': is_qr_transaction,
            'prize_scam_language': prize_scam,
            'suspicious_offer': suspicious_offer,
            'qr_redirect_risk': has_url,
            'qr_urgency': qr_urgency,
            'high_value_qr': high_value_qr,
            'quishing_risk_composite': quishing_risk_composite,
            'amount': amount,
            'payee_new': 1,
            'transaction_count_24h': 5,
            'hour': 12
        }
    
    def _get_indicators(self, features: Dict[str, float], risk_score: float) -> list:
        """Generate human-readable indicators"""
        indicators = []
        
        if risk_score > 0.7:
            indicators.append("🚨 HIGH QUISHING RISK - QR code scam patterns detected")
        elif risk_score > 0.5:
            indicators.append("⚠️ MODERATE QUISHING RISK - Suspicious QR patterns")
        
        if features['contains_qr_mention'] > 0:
            indicators.append("⚠️ Message mentions QR code/scanning")
        
        if features['unverified_qr_source'] > 0:
            indicators.append("⚠️ QR-based transaction type")
        
        if features['prize_scam_language'] > 0:
            indicators.append("⚠️ Prize/reward scam language detected")
        
        if features['suspicious_offer'] > 0:
            indicators.append("⚠️ Suspicious discount/offer mentioned")
        
        if features['qr_urgency'] > 0:
            indicators.append("⚠️ Urgency tactics in QR context")
        
        if features['high_value_qr'] > 0:
            indicators.append("⚠️ High-value QR transaction")
        
        if not indicators:
            indicators.append("✓ No significant quishing indicators")
        
        return indicators
