"""
Feature Engineering for UPI Fraud Detection
Extracts 50+ features for ML models
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
import hashlib

class UPIFeatureEngineer:
    def __init__(self):
        self.label_encoders = {}
        self.scaler = StandardScaler()
        
    def hash_pii(self, value):
        if pd.isna(value) or value is None:
            return None
        return hashlib.sha256(str(value).encode()).hexdigest()[:16]
    
    def encode_categorical(self, df, columns):
        df = df.copy()
        for col in columns:
            if col not in df.columns:
                continue
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
                df[col] = self.label_encoders[col].fit_transform(df[col].astype(str))
            else:
                df[col] = self.label_encoders[col].transform(df[col].astype(str))
        return df
    
    def create_phishing_features(self, df):
        df = df.copy()
        df['domain_reputation'] = df['url_domain'].apply(
            lambda x: 0.2 if pd.notna(x) and str(x) in ['upi-verify.com', 'secure-payment.net', 'bank-alert.in'] else 0.8
        )
        df['keyword_risk_score'] = df['suspicious_keywords'] / 5.0
        df['phishing_risk_composite'] = (
            df['contains_url'] * 0.3 +
            df['urgent_language'] * 0.2 +
            df['requests_pin'] * 0.3 +
            df['mimics_bank'] * 0.15 +
            df['has_typosquatting'] * 0.05
        )
        return df
    
    def create_qr_features(self, df):
        df = df.copy()
        df['qr_complexity_ratio'] = df['qr_complexity'] / (df['qr_version'] + 1)
        error_correction_map = {'L': 0.25, 'M': 0.5, 'Q': 0.75, 'H': 1.0}
        df['qr_error_correction_score'] = df['qr_error_correction'].map(error_correction_map)
        df['qr_suspicious'] = (
            (df['qr_complexity'] > 0.7) & 
            (df['qr_has_logo'] == 0) & 
            (df['qr_url_length'] > 100)
        ).astype(int)
        df['qr_risk_score'] = (
            df['qr_complexity'] * 0.3 +
            (1 - df['qr_error_correction_score']) * 0.2 +
            (df['qr_version'] / 40) * 0.2 +
            (1 - df['qr_has_logo']) * 0.15 +
            (df['qr_url_length'] / 300) * 0.15
        )
        return df
    
    def create_collect_request_features(self, df):
        df = df.copy()
        df['collect_risk_score'] = 0.0
        collect_mask = df['is_collect_request'] == 1
        if collect_mask.sum() > 0:
            df.loc[collect_mask, 'collect_risk_score'] = (
                df.loc[collect_mask, 'collect_unsolicited'] * 0.4 +
                df.loc[collect_mask, 'collect_from_unknown'] * 0.3 +
                (df.loc[collect_mask, 'collect_frequency_1h'] > 2).astype(int) * 0.2 +
                (df.loc[collect_mask, 'collect_timing'] == 'odd_hours').astype(int) * 0.1
            )
        df['collect_amount_ratio'] = df['collect_amount'] / (df['avg_transaction_amount_30d'] + 1)
        return df
    
    def create_malware_features(self, df):
        df = df.copy()
        df['device_security_score'] = 1.0 - (
            df['app_modified'] * 0.3 +
            df['root_jailbreak'] * 0.25 +
            df['app_from_unknown_source'] * 0.2 +
            df['has_overlay_attack'] * 0.15 +
            df['clipboard_hijack'] * 0.1
        )
        df['permission_risk'] = df['suspicious_permissions'] / 10.0
        df['malware_risk_composite'] = (
            df['app_modified'] * 0.3 +
            df['root_jailbreak'] * 0.25 +
            (df['suspicious_permissions'] > 3).astype(int) * 0.2 +
            df['app_from_unknown_source'] * 0.15 +
            df['has_overlay_attack'] * 0.1
        )
        return df
    
    def create_behavioral_features(self, df):
        df = df.copy()
        df['amount_deviation'] = np.abs(df['amount'] - df['avg_transaction_amount_30d']) / (df['avg_transaction_amount_30d'] + 1)
        df['velocity_risk'] = (df['transaction_count_24h'] > 10).astype(int)
        df['time_risk'] = ((df['hour'] < 6) | (df['hour'] > 22)).astype(int)
        df['new_payee_risk'] = df['payee_new'] * (df['amount'] > 5000).astype(int)
        return df
    
    def engineer_all_features(self, df, fit=True):
        print("Engineering features...")
        df['payer_vpa_hash'] = df['payer_vpa'].apply(self.hash_pii)
        df['payee_vpa_hash'] = df['payee_vpa'].apply(self.hash_pii)
        df = self.create_phishing_features(df)
        df = self.create_qr_features(df)
        df = self.create_collect_request_features(df)
        df = self.create_malware_features(df)
        df = self.create_behavioral_features(df)
        categorical_cols = ['payee_category', 'payer_bank', 'payee_bank', 'payer_upi_app', 'qr_error_correction', 'collect_timing']
        df = self.encode_categorical(df, categorical_cols)
        print(f"Total features: {df.shape[1]}")
        return df

if __name__ == "__main__":
    print("Loading synthetic data...")
    df = pd.read_csv('upi_transactions_synthetic.csv')
    print(f"Loaded {len(df)} transactions")
    
    engineer = UPIFeatureEngineer()
    df_engineered = engineer.engineer_all_features(df)
    
    print("\n=== Feature Engineering Complete ===")
    print(f"Engineered features: {df_engineered.shape[1]}")
    
    df_engineered.to_csv('upi_transactions_engineered.csv', index=False)
    print("Saved to upi_transactions_engineered.csv")
