"""
Collect Request Fraud Detection Agent
Message-aware detection + optional ML fallback
"""

import pickle
import pandas as pd
from typing import Dict, Any
import asyncio


class CollectRequestAgent:
    def __init__(self, model_path: str = '../models/collect_request_detector.pkl'):
        self.model_path = model_path
        self.model = None
        self.loaded = False
        self.load_model()

    def load_model(self):
        try:
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            self.loaded = True
            print("CollectRequestAgent: Model loaded successfully")
        except Exception as e:
            print(f"CollectRequestAgent: Could not load model - {e}")
            self.loaded = False

    def is_loaded(self) -> bool:
        return self.loaded

    async def analyze(self, transaction: Any) -> Dict[str, Any]:
        await asyncio.sleep(0.01)

        message = str(getattr(transaction, 'message', '')).lower()
        tx_type = str(getattr(transaction, 'transaction_type', 'pay')).lower()
        amount = float(getattr(transaction, 'amount', 0))

        feats = self._extract_features(message, tx_type, amount)
        proba = self._predict(feats)
        indicators = self._indicators(feats, proba)

        return {
            'agent': 'CollectRequestAgent',
            'subscore': float(proba),
            'confidence': float(abs(proba - 0.5) * 2),
            'indicators': indicators
        }

    def _predict(self, f: Dict[str, float]) -> float:
        base = f['collect_fraud_composite']
        if self.loaded and self.model is not None:
            try:
                X = pd.DataFrame([f])
                ml = float(self.model.predict_proba(X)[0, 1])
                return max(base, ml * 0.7 + base * 0.3)
            except Exception:
                return base
        return base

    def _extract_features(self, message: str, tx_type: str, amount: float) -> Dict[str, float]:
        is_collect = 1.0 if 'collect' in tx_type else 0.0
        threats = 1.0 if any(w in message for w in ['legal','court','police','arrest','penalty','fine','lawyer','case']) else 0.0
        urgency = 1.0 if any(w in message for w in ['immediately','urgent','final','last','now','today']) else 0.0
        dues   = 1.0 if any(w in message for w in ['due','dues','debt','owe','outstanding','pending','unpaid']) else 0.0
        authority = 1.0 if any(w in message for w in ['government','tax','department','official','authority','ministry','officer']) else 0.0

        composite = (
            is_collect * 0.20 +
            threats    * 0.30 +
            urgency    * 0.25 +
            dues       * 0.15 +
            authority  * 0.10
        )

        return {
            'is_collect': is_collect,
            'threats': threats,
            'urgency': urgency,
            'dues': dues,
            'authority': authority,
            'collect_fraud_composite': min(1.0, composite),
            'amount': amount
        }

    def _indicators(self, f: Dict[str, float], proba: float):
        ind = []
        if f['is_collect'] > 0: ind.append("⚠️ Collect payment request")
        if f['threats'] > 0: ind.append("⚠️ Threatening/legal language")
        if f['urgency'] > 0: ind.append("⚠️ Urgency/pressure")
        if f['dues'] > 0: ind.append("⚠️ Claims dues/outstanding")
        if f['authority'] > 0: ind.append("⚠️ Authority/department impersonation")
        if not ind: ind.append("✓ No significant collect fraud indicators")
        return ind
