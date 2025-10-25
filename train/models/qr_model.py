"""
QR Code (Quishing) Detection Model
Random Forest classifier for malicious QR codes
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, roc_auc_score
import joblib
import json

class QuishingDetector:
    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators=150,
            max_depth=12,
            min_samples_split=10,
            min_samples_leaf=5,
            max_features='sqrt',
            random_state=42,
            n_jobs=-1
        )
        
        self.feature_cols = [
            'qr_complexity', 'qr_version', 'qr_pixel_density',
            'qr_has_logo', 'qr_url_length', 'qr_risk_score',
            'qr_complexity_ratio', 'qr_error_correction_score',
            'qr_suspicious', 'amount', 'payee_new'
        ]
    
    def train(self, df):
        print("\n=== Training Quishing Detector ===")
        
        # Filter to QR-related transactions
        qr_mask = df['qr_complexity'] > 0
        df_qr = df[qr_mask].copy()
        
        X = df_qr[self.feature_cols]
        y = df_qr['is_fraud']
        
        print(f"Training samples: {len(X)}, Fraud rate: {y.mean()*100:.2f}%")
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        self.model.fit(X_train, y_train)
        
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        
        print("\n=== Quishing Detector Performance ===")
        print(classification_report(y_test, y_pred))
        print(f"ROC-AUC Score: {roc_auc_score(y_test, y_pred_proba):.4f}")
        
        # Cross-validation
        cv_scores = cross_val_score(self.model, X_train, y_train, cv=5, scoring='roc_auc')
        print(f"Cross-validation AUC: {cv_scores.mean():.4f} (+/- {cv_scores.std()*2:.4f})")
    
    def save(self, path='qr_detector.pkl'):
        joblib.dump(self.model, path)
        print(f"Model saved to {path}")
    
    def load(self, path='qr_detector.pkl'):
        self.model = joblib.load(path)
        print(f"Model loaded from {path}")

if __name__ == "__main__":
    df = pd.read_csv('upi_transactions_engineered.csv')
    detector = QuishingDetector()
    detector.train(df)
    detector.save('qr_detector.pkl')
