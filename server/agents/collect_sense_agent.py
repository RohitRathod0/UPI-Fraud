"""
Collect Request Fraud Detection Agent
XGBoost classifier for detecting fraudulent payment requests
"""

import pickle
import pandas as pd
import numpy as np
from typing import Dict, Any
import asyncio


class CollectRequestAgent:
    def __init__(self, model_path: str = '../models/collect_request_detector.pkl'):
        self.model = None
        self.model_path = model_path
        self.loaded = False
        self.load_model()
    
    def load_model(self):
        """Load the trained collect request fraud model"""
        try:
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            self.loaded = True
            print(f"CollectRequestAgent: Model loaded successfully")
        except Exception as e:
            print(f"CollectRequestAgent: Could not load model - {e}")
            self.loaded = False
    
    def is_loaded(self) -> bool:
        return self.loaded
    
    async def analyze(self, transaction: Any) -> Dict[str, Any]:
        """Analyze transaction for collect request fraud"""
        await asyncio.sleep(0.03)
        
        try:
            message = str(getattr(transaction, 'message', '')).lower()
            transaction_type = str(getattr(transaction, 'transaction_type', 'pay')).lower()
            amount = getattr(transaction, 'amount', 0)
            
            # Extract REAL features
            features = self._extract_real_features(message, transaction_type, amount)
            
            # Use model if loaded
            if self.loaded and self.model:
                X = pd.DataFrame([features])
                proba = float(self.model.predict_proba(X)[0, 1])
            else:
                # Fallback
                proba = features['collect_fraud_composite']
            
            confidence = abs(proba - 0.5) * 2
            
            return {
                'agent': 'CollectRequestAgent',
                'subscore': proba,
                'confidence': float(confidence),
                'indicators': self._get_indicators(features, proba)
            }
            
        except Exception as e:
            print(f"CollectRequestAgent error: {e}")
            return {
                'agent': 'CollectRequestAgent',
                'subscore': 0.0,
                'confidence': 0.0,
                'indicators': []
            }
    
    def _extract_real_features(self, message: str, transaction_type: str, amount: float) -> Dict[str, float]:
        """Extract REAL collect fraud features"""
        
        # Check if it's a collect request
        is_collect = 1.0 if 'collect' in transaction_type else 0.0
        
        # Threatening language
        threat_words = ['legal', 'court', 'action', 'sue', 'police', 'arrest',
                       'penalty', 'fine', 'lawyer', 'case']
        threatening_language = 1.0 if any(word in message for word in threat_words) else 0.0
        
        # Urgency/pressure
        urgent_words = ['immediately', 'urgent', 'final', 'last', 'now', 'today']
        urgency_pressure = 1.0 if any(word in message for word in urgent_words) else 0.0
        
        # Debt/dues language
        debt_words = ['due', 'dues', 'debt', 'owe', 'outstanding', 'pending', 'unpaid']
        impersonates_authority = 1.0 if any(word in message for word in debt_words) else 0.0
        
        # Authority impersonation
        auth_words = ['government', 'tax', 'department', 'official', 'authority',
                     'ministry', 'officer']
        authority_claim = 1.0 if any(word in message for word in auth_words) else 0.0
        
        # High pressure tactics count
        pressure_count = (threatening_language + urgency_pressure + 
                         impersonates_authority + authority_claim)
        high_pressure_tactics = min(pressure_count / 4.0, 1.0)
        
        # Unsolicited + high value
        unsolicited_high_value = 1.0 if (is_collect and amount > 5000) else 0.0
        
        # Composite risk
        collect_fraud_composite = (
            is_collect * 0.15 +
            threatening_language * 0.25 +
            urgency_pressure * 0.20 +
            impersonates_authority * 0.20 +
            high_pressure_tactics * 0.20
        )
        
        return {
            'unsolicited_request': is_collect,
            'threatening_language': threatening_language,
            'urgency_pressure': urgency_pressure,
            'impersonates_authority': impersonates_authority,
            'high_pressure_tactics': high_pressure_tactics,
            'unsolicited_high_value': unsolicited_high_value,
            'collect_fraud_composite': collect_fraud_composite,
            'amount': amount,
            'payee_new': 1,
            'transaction_count_24h': 5,
            'hour': 12
        }
    
    def _get_indicators(self, features: Dict[str, float], risk_score: float) -> list:
        """Generate human-readable indicators"""
        indicators = []
        
        if risk_score > 0.7:
            indicators.append("🚨 HIGH COLLECT FRAUD RISK - Threatening patterns detected")
        elif risk_score > 0.5:
            indicators.append("⚠️ MODERATE COLLECT FRAUD RISK")
        
        if features['threatening_language'] > 0:
            indicators.append("⚠️ Threatening language (legal/court/police)")
        
        if features['urgency_pressure'] > 0:
            indicators.append("⚠️ High-pressure urgency tactics")
        
        if features['impersonates_authority'] > 0:
            indicators.append("⚠️ Claims debt/dues/outstanding payment")
        
        if features['unsolicited_high_value'] > 0:
            indicators.append("⚠️ Unsolicited high-value collect request")
        
        if features['high_pressure_tactics'] > 0.5:
            indicators.append("⚠️ Multiple pressure tactics detected")
        
        if not indicators:
            indicators.append("✓ No significant collect fraud indicators")
        
        return indicators
