"""
Collect Request Exploit Detection Model
Interpretable Logistic Regression for collect request fraud
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
from sklearn.preprocessing import StandardScaler
import joblib
import json

class CollectRequestDetector:
    def __init__(self):
        self.model = LogisticRegression(
            C=1.0,
            penalty='l2',
            solver='lbfgs',
            max_iter=500,
            random_state=42,
            class_weight='balanced'
        )
        
        self.scaler = StandardScaler()
        
        self.feature_cols = [
            'is_collect_request',
            'collect_unsolicited',
            'collect_from_unknown',
            'collect_amount',
            'collect_frequency_1h',
            'collect_risk_score',
            'collect_amount_ratio',
            'amount_deviation',
            'time_risk',
            'payee_new'
        ]
        
        self.feature_importance = None
    
    def prepare_data(self, df):
        """Prepare collect request-specific features"""
        # Filter to collect requests only (or add negative samples)
        collect_mask = df['is_collect_request'] == 1
        
        # Include all collect requests + sampled non-collect transactions
        fraud_mask = df['is_fraud'] == 1
        non_collect_sample = ~collect_mask & (np.random.rand(len(df)) < 0.2)
        
        final_mask = collect_mask | fraud_mask | non_collect_sample
        
        df_filtered = df[final_mask].copy()
        
        X = df_filtered[self.feature_cols]
        y = df_filtered['is_fraud']
        
        return X, y
    
    def train(self, df):
        """Train collect request detection model"""
        print("\n=== Training Collect Request Detector ===")
        
        X, y = self.prepare_data(df)
        print(f"Training samples: {len(X)}, Fraud rate: {y.mean()*100:.2f}%")
        print(f"Collect requests: {X['is_collect_request'].sum()}")
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        y_pred_proba = self.model.predict_proba(X_test_scaled)[:, 1]
        
        print("\n=== Collect Request Detector Performance ===")
        print(classification_report(y_test, y_pred, target_names=['Legitimate', 'Fraud']))
        print(f"ROC-AUC Score: {roc_auc_score(y_test, y_pred_proba):.4f}")
        
        # Feature importance (coefficients)
        self.feature_importance = dict(zip(self.feature_cols, self.model.coef_[0]))
        print("\n=== Feature Coefficients (Interpretability) ===")
        for feat, coef in sorted(self.feature_importance.items(), key=lambda x: abs(x[1]), reverse=True):
            direction = "increases" if coef > 0 else "decreases"
            print(f"{feat}: {coef:.4f} ({direction} fraud risk)")
        
        # Cross-validation
        cv_scores = cross_val_score(self.model, X_train_scaled, y_train, cv=5, scoring='roc_auc')
        print(f"\nCross-validation AUC: {cv_scores.mean():.4f} (+/- {cv_scores.std()*2:.4f})")
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        print("\n=== Confusion Matrix ===")
        print(f"True Negatives:  {cm[0, 0]}")
        print(f"False Positives: {cm[0, 1]}")
        print(f"False Negatives: {cm[1, 0]}")
        print(f"True Positives:  {cm[1, 1]}")
        
        return self.model
    
    def predict(self, features_dict):
        """Predict collect request fraud probability"""
        X = pd.DataFrame([features_dict])[self.feature_cols]
        X_scaled = self.scaler.transform(X)
        proba = self.model.predict_proba(X_scaled)[0, 1]
        confidence = abs(proba - 0.5) * 2
        
        # Get feature contributions
        contributions = {}
        for i, (feat, value) in enumerate(zip(self.feature_cols, X.values[0])):
            if self.feature_importance:
                contrib = self.feature_importance[feat] * value
                if abs(contrib) > 0.01:
                    contributions[feat] = float(contrib)
        
        return {
            'collect_subscore': float(proba),
            'confidence': float(confidence),
            'feature_contributions': contributions
        }
    
    def save(self, path='models/collect_detector.pkl'):
        """Save trained model and scaler"""
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_importance': self.feature_importance
        }
        joblib.dump(model_data, path)
        
        # Save metadata
        metadata = {
            'feature_cols': self.feature_cols,
            'feature_importance': self.feature_importance
        }
        with open(path.replace('.pkl', '_metadata.json'), 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Model saved to {path}")
    
    def load(self, path='models/collect_detector.pkl'):
        """Load trained model and scaler"""
        model_data = joblib.load(path)
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.feature_importance = model_data['feature_importance']
        
        print(f"Model loaded from {path}")


if __name__ == "__main__":
    # Train collect request detector
    df = pd.read_csv('upi_transactions_engineered.csv')
    
    detector = CollectRequestDetector()
    detector.train(df)
    detector.save('collect_detector.pkl')
    
    # Test prediction
    sample = {
        'is_collect_request': 1,
        'collect_unsolicited': 1,
        'collect_from_unknown': 1,
        'collect_amount': 1500,
        'collect_frequency_1h': 5,
        'collect_risk_score': 0.8,
        'collect_amount_ratio': 3.0,
        'amount_deviation': 2.5,
        'time_risk': 1,
        'payee_new': 1
    }
    
    result = detector.predict(sample)
    print("\n=== Sample Prediction ===")
    print(f"Collect subscore: {result['collect_subscore']:.3f}")
    print(f"Confidence: {result['confidence']:.3f}")
    print(f"Feature contributions: {result['feature_contributions']}")
