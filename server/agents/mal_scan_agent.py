"""
Malware/Device Compromise Detection Agent
Message-aware indicators + optional ML fallback
"""

import pickle
import pandas as pd
from typing import Dict, Any
import asyncio


class MalwareAgent:
    def __init__(self, model_path: str = '../models/malware_detector.pkl'):
        self.model_path = model_path
        self.model = None
        self.loaded = False
        self.load_model()

    def load_model(self):
        try:
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            self.loaded = True
            print("MalwareAgent: Model loaded successfully")
        except Exception as e:
            print(f"MalwareAgent: Could not load model - {e}")
            self.loaded = False

    def is_loaded(self) -> bool:
        return self.loaded

    async def analyze(self, transaction: Any) -> Dict[str, Any]:
        await asyncio.sleep(0.01)

        message = str(getattr(transaction, 'message', '')).lower()
        amount = float(getattr(transaction, 'amount', 0))
        hour = int(getattr(transaction, 'hour', 12))

        feats = self._extract_features(message, amount, hour)
        proba = self._predict(feats)
        indicators = self._indicators(feats, proba)

        return {
            'agent': 'MalwareAgent',
            'subscore': float(proba),
            'confidence': float(abs(proba - 0.5) * 2),
            'indicators': indicators
        }

    def _predict(self, f: Dict[str, float]) -> float:
        base = f['malware_composite']
        if self.loaded and self.model is not None:
            try:
                X = pd.DataFrame([f])
                ml = float(self.model.predict_proba(X)[0, 1])
                return max(base, ml * 0.7 + base * 0.3)
            except Exception:
                return base
        return base

    def _extract_features(self, message: str, amount: float, hour: int) -> Dict[str, float]:
        cred_terms = ['otp','pin','password','pwd','cvv']
        has_cred = 1.0 if any(t in message for t in cred_terms) else 0.0

        unusual_time = 1.0 if (hour < 6 or hour > 23) else 0.0
        high_value = 1.0 if amount >= 50000 else 0.0
        sms_interception = 1.0 if 'otp' in message else 0.0

        malware_composite = min(
            has_cred * 0.6 +
            high_value * 0.25 +
            unusual_time * 0.10 +
            sms_interception * 0.05,
            1.0
        )

        # EXACTLY 12 features for legacy models
        return {
            'unusual_app_behavior': 0.2 if has_cred else 0.0,
            'device_rooted_jailbroken': 0.0,
            'suspicious_permissions': 0.3 if has_cred else 0.0,
            'unusual_network_activity': 0.1 if has_cred else 0.0,
            'keylogger_indicators': has_cred,
            'screen_overlay_detected': 0.0,
            'sms_interception_risk': sms_interception,
            'device_compromise_score': malware_composite,
            'amount': amount,
            'transaction_count_24h': 5,
            'hour': hour,
            'unusual_time': unusual_time,
            'malware_composite': malware_composite
        }

    def _indicators(self, f: Dict[str, float], proba: float):
        ind = []
        if f['keylogger_indicators'] > 0: ind.append("⚠️ Credential text present (OTP/PIN/password)")
        if f['sms_interception_risk'] > 0: ind.append("⚠️ Possible SMS/OTP interception risk")
        if f['unusual_time'] > 0: ind.append("⚠️ Transaction at unusual hour")
        if f['amount'] >= 50000: ind.append("⚠️ High-value transaction")
        if not ind: ind.append("✓ No significant malware indicators")
        return ind
