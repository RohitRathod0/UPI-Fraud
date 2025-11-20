"""
Quishing (QR code phishing) Detection Agent
Message-aware detection + optional ML fallback
"""

import pickle
import pandas as pd
from typing import Dict, Any
import asyncio


class QuishingAgent:
    def __init__(self, model_path: str = '../models/qr_detector.pkl'):
        self.model_path = model_path
        self.model = None
        self.loaded = False
        self.load_model()

    def load_model(self):
        import joblib
        try:
            # Try joblib first (common for sklearn models)
            try:
                self.model = joblib.load(self.model_path)
                self.loaded = True
                print("QuishingAgent: Model loaded successfully via joblib")
                return
            except:
                pass
            
            # Try pickle with different protocols
            with open(self.model_path, 'rb') as f:
                try:
                    # Try standard pickle
                    self.model = pickle.load(f)
                    self.loaded = True
                    print("QuishingAgent: Model loaded successfully via pickle")
                    return
                except Exception as e1:
                    # Try with latin1 encoding (Python 2/3 compatibility)
                    f.seek(0)
                    try:
                        self.model = pickle.load(f, encoding='latin1')
                        self.loaded = True
                        print("QuishingAgent: Model loaded successfully via pickle (latin1)")
                        return
                    except Exception as e2:
                        # Try with errors='ignore'
                        f.seek(0)
                        try:
                            self.model = pickle.load(f, encoding='latin1', errors='ignore')
                            self.loaded = True
                            print("QuishingAgent: Model loaded successfully via pickle (latin1, ignore errors)")
                            return
                        except Exception as e3:
                            raise e1
        except Exception as e:
            print(f"QuishingAgent: Could not load model - {e}")
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
            'agent': 'QuishingAgent',
            'subscore': float(proba),
            'confidence': float(abs(proba - 0.5) * 2),
            'indicators': indicators
        }

    def _predict(self, f: Dict[str, float]) -> float:
        base = f['quishing_risk_composite']
        if self.loaded and self.model is not None:
            try:
                X = pd.DataFrame([f])
                ml = float(self.model.predict_proba(X)[0, 1])
                return max(base, ml * 0.7 + base * 0.3)
            except Exception:
                return base
        return base

    def _extract_features(self, message: str, tx_type: str, amount: float) -> Dict[str, float]:
        is_qr_txn = 1.0 if 'qr' in tx_type else 0.0
        mentions_qr = 1.0 if any(w in message for w in ['qr','scan','code','barcode']) else 0.0
        prize_lang  = 1.0 if any(w in message for w in ['prize','won','winner','reward','claim','free','gift']) else 0.0
        offer_lang  = 1.0 if any(w in message for w in ['discount','offer','deal','% off','limited']) else 0.0
        url_present = 1.0 if any(p in message for p in ['http','www','bit.ly']) else 0.0
        urgent_qr   = 1.0 if any(w in message for w in ['limited','expire','hurry','now','today','immediately']) else 0.0

        composite = (
            is_qr_txn  * 0.25 +
            mentions_qr* 0.20 +
            prize_lang * 0.25 +
            offer_lang * 0.15 +
            url_present* 0.10 +
            urgent_qr  * 0.05
        )

        return {
            'is_qr_txn': is_qr_txn,
            'mentions_qr': mentions_qr,
            'prize_lang': prize_lang,
            'offer_lang': offer_lang,
            'url_present': url_present,
            'urgent_qr': urgent_qr,
            'quishing_risk_composite': min(1.0, composite),
            'amount': amount
        }

    def _indicators(self, f: Dict[str, float], proba: float):
        ind = []
        if f['is_qr_txn'] > 0: ind.append("QR-based transaction")
        if f['mentions_qr'] > 0: ind.append("Message mentions QR/scan/code")
        if f['prize_lang'] > 0: ind.append("Prize/reward scam language")
        if f['offer_lang'] > 0: ind.append("Suspicious offer/discount")
        if f['url_present'] > 0: ind.append("URL present (possible redirect)")
        if f['urgent_qr'] > 0: ind.append("Urgency in QR context")
        if not ind: ind.append("No significant quishing indicators")
        return ind
