"""
Phishing/Vishing Detection Model
XGBoost classifier for detecting social engineering attacks
"""

import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
import joblib
import json

class PhishingDetector:
    def __init__(self):
        self.model = XGBClassifier(
            n_estimators=200,
            max_depth=8,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=3,
            gamma=0.1,
            scale_pos_weight=3,
            random_state=42,
            eval_metric='auc'
        )
        
        self.feature_cols = [
            'contains_url', 'suspicious_keywords', 'urgent_language',
            'requests_pin', 'mimics_bank', 'has_typosquatting',
            'domain_reputation', 'keyword_risk_score', 'phishing_risk_composite',
            'amount', 'payee_new', 'transaction_count_24h', 'hour', 'time_risk'
        ]
        
        self.feature_importance = None
    
    def prepare_data(self, df):
        """Prepare phishing-specific features"""
        X = df[self.feature_cols].copy()
        y = df['is_fraud'].copy()
        
        # Get fraud and legitimate samples
        fraud_indices = np.where(y == 1)[0]
        legit_indices = np.where(y == 0)[0]
        
        # Sample legitimate cases (3x fraud cases)
        n_legit_sample = min(len(legit_indices), len(fraud_indices) * 3)
        legit_sample_indices = np.random.choice(legit_indices, n_legit_sample, replace=False)
        
        # Combine
        final_indices = np.concatenate([fraud_indices, legit_sample_indices])
        np.random.shuffle(final_indices)
        
        X = X.iloc[final_indices]
        y = y.iloc[final_indices]
        
        return X, y
    
    def train(self, df):
        """Train phishing detection model"""
        print("\n=== Training Phishing Detector ===")
        
        X, y = self.prepare_data(df)
        print(f"Training samples: {len(X)}, Fraud rate: {y.mean()*100:.2f}%")
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train model
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        
        print("\n=== Phishing Detector Performance ===")
        print(classification_report(y_test, y_pred, target_names=['Legitimate', 'Phishing']))
        print(f"ROC-AUC Score: {roc_auc_score(y_test, y_pred_proba):.4f}")
        
        # Feature importance
        self.feature_importance = dict(zip(self.feature_cols, self.model.feature_importances_))
        print("\n=== Top 5 Important Features ===")
        for feat, imp in sorted(self.feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"{feat}: {imp:.4f}")
        
        # Cross-validation
        cv_scores = cross_val_score(self.model, X_train, y_train, cv=5, scoring='roc_auc')
        print(f"\nCross-validation AUC: {cv_scores.mean():.4f} (+/- {cv_scores.std()*2:.4f})")
        
        return self.model
    
    def predict(self, features_dict):
        """Predict phishing probability for a single transaction"""
        X = pd.DataFrame([features_dict])[self.feature_cols]
        proba = self.model.predict_proba(X)[0, 1]
        confidence = abs(proba - 0.5) * 2
        
        return {
            'phishing_subscore': float(proba),
            'confidence': float(confidence),
            'indicators': self._get_indicators(features_dict, proba)
        }
    
    def _get_indicators(self, features, score):
        """Get human-readable indicators"""
        indicators = []
        if features.get('contains_url', 0) == 1:
            indicators.append('Contains suspicious URL')
        if features.get('requests_pin', 0) == 1:
            indicators.append('Requests PIN/password')
        if features.get('mimics_bank', 0) == 1:
            indicators.append('Mimics bank/official entity')
        if features.get('suspicious_keywords', 0) >= 2:
            indicators.append(f"Contains {features['suspicious_keywords']} suspicious keywords")
        if features.get('urgent_language', 0) == 1:
            indicators.append('Uses urgent/threatening language')
        
        return indicators
    
    def save(self, path='phishing_detector.pkl'):
        """Save trained model"""
        joblib.dump(self.model, path)
        
        # Convert numpy types to Python types for JSON serialization
        feature_importance_clean = {
            k: float(v) for k, v in self.feature_importance.items()
        }
        
        metadata = {
            'feature_cols': self.feature_cols,
            'feature_importance': feature_importance_clean
        }
        with open(path.replace('.pkl', '_metadata.json'), 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Model saved to {path}")
    
    def load(self, path='phishing_detector.pkl'):
        """Load trained model"""
        self.model = joblib.load(path)
        
        with open(path.replace('.pkl', '_metadata.json'), 'r') as f:
            metadata = json.load(f)
            self.feature_importance = metadata['feature_importance']
        
        print(f"Model loaded from {path}")

if __name__ == "__main__":
    df = pd.read_csv('../upi_transactions_engineered.csv')
    
    detector = PhishingDetector()
    detector.train(df)
    detector.save('phishing_detector.pkl')
    
    print("\n✓ Phishing detector trained and saved successfully!")
