"""
Phishing/Vishing Detection Agent
Message-aware detection + optional ML fallback
"""

import pickle
import pandas as pd
from typing import Dict, Any
import asyncio


class PhishingAgent:
    def __init__(self, model_path: str = '../models/phishing_detector.pkl'):
        self.model_path = model_path
        self.model = None
        self.loaded = False
        self.load_model()

    def load_model(self):
        try:
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            self.loaded = True
            print("PhishingAgent: Model loaded successfully")
        except Exception as e:
            print(f"PhishingAgent: Could not load model - {e}")
            self.loaded = False

    def is_loaded(self) -> bool:
        return self.loaded

    async def analyze(self, transaction: Any) -> Dict[str, Any]:
        await asyncio.sleep(0.01)

        message = str(getattr(transaction, 'message', '')).lower()
        payee_vpa = str(getattr(transaction, 'payee_vpa', '')).lower()
        amount = float(getattr(transaction, 'amount', 0))

        feats = self._extract_features(message, payee_vpa, amount)
        proba = self._predict(feats)
        indicators = self._indicators(feats, proba)

        return {
            'agent': 'PhishingAgent',
            'subscore': float(proba),
            'confidence': float(abs(proba - 0.5) * 2),
            'indicators': indicators
        }

    def _predict(self, feats: Dict[str, float]) -> float:
        # Strong rule boost on credentials
        base = feats['phishing_risk_composite']
        if feats['has_cred'] > 0.5:
            base = min(1.0, base + 0.45)

        if self.loaded and self.model is not None:
            try:
                X = pd.DataFrame([feats])
                ml = float(self.model.predict_proba(X)[0, 1])
                # Blend conservatively so rules dominate critical patterns
                return max(base, ml * 0.7 + base * 0.3)
            except Exception:
                return base
        return base

    def _extract_features(self, message: str, payee_vpa: str, amount: float) -> Dict[str, float]:
        url_patterns = ['http://', 'https://', 'www.', '.com', '.in', 'bit.ly', 'tinyurl']
        contains_url = 1.0 if any(p in message for p in url_patterns) else 0.0

        urgent_terms = ['urgent', 'immediately', 'emergency', 'locked', 'suspended', 'expire', 'action required', 'final notice']
        urgent_flag = 1.0 if any(t in message for t in urgent_terms) else 0.0

        cred_terms = ['otp', 'one time password', 'one-time password', 'pin', 'cvv', 'password', 'pwd']
        has_cred = 1.0 if any(t in message for t in cred_terms) else 0.0

        bank_words = ['account', 'bank', 'security', 'verification', 'blocked', 'deactivated', 'unauthorized']
        mimics_bank = 1.0 if sum(w in message for w in bank_words) >= 2 else 0.0

        sus_payee_words = ['verify', 'security', 'account', 'official', 'support', 'service']
        has_typosquat = 1.0 if any(w in payee_vpa for w in sus_payee_words) else 0.0

        composite = (
            has_cred     * 0.45 +
            urgent_flag  * 0.25 +
            contains_url * 0.20 +
            mimics_bank  * 0.07 +
            has_typosquat* 0.03
        )

        return {
            'contains_url': contains_url,
            'urgent_flag': urgent_flag,
            'has_cred': has_cred,
            'mimics_bank': mimics_bank,
            'has_typosquat': has_typosquat,
            'phishing_risk_composite': min(1.0, composite),
            'amount': amount
        }

    def _indicators(self, f: Dict[str, float], proba: float):
        ind = []
        if f['has_cred'] > 0: ind.append("Requests credentials (OTP/PIN/password)")
        if f['urgent_flag'] > 0: ind.append("Urgent/threatening language")
        if f['contains_url'] > 0: ind.append("Message contains URL/link")
        if f['mimics_bank'] > 0: ind.append("Mimics bank/official communication")
        if f['has_typosquat'] > 0: ind.append("Suspicious payee naming (security/verify)")
        if not ind: ind.append("No significant phishing indicators")
        return ind
