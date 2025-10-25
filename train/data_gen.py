"""
Synthetic UPI Transaction Data Generator
Generates 200k realistic UPI transactions with fraud labels
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import hashlib
import json

np.random.seed(42)
random.seed(42)

class UPIDataGenerator:
    def __init__(self, n_samples=200000):
        self.n_samples = n_samples
        self.fraud_rate = 0.08  # 8% fraud rate (realistic for UPI)
        
        # UPI-specific data
        self.upi_apps = ['PhonePe', 'GooglePay', 'Paytm', 'BHIM', 'AmazonPay', 'WhatsAppPay']
        self.merchant_categories = ['Grocery', 'Electronics', 'Food', 'Transport', 'Bills', 'Shopping', 'Entertainment']
        self.banks = ['SBI', 'HDFC', 'ICICI', 'Axis', 'Kotak', 'PNB', 'BOB']
        
        # Fraud pattern indicators
        self.phishing_domains = ['upi-verify.com', 'secure-payment.net', 'bank-alert.in', 'upi-refund.co']
        self.suspicious_keywords = ['verify', 'urgent', 'refund', 'reward', 'prize', 'confirm', 'update KYC']
        
    def generate_transaction_id(self, idx):
        """Generate realistic UPI transaction ID"""
        timestamp = int(datetime.now().timestamp() * 1000)
        return f"UPI{timestamp}{idx:06d}"
    
    def generate_vpa(self, is_fraud=False):
        """Generate Virtual Payment Address (UPI ID)"""
        if is_fraud and random.random() < 0.4:
            # Suspicious patterns
            prefixes = ['admin', 'support', 'verify', 'official', 'payment']
            return f"{random.choice(prefixes)}{random.randint(1000,9999)}@{random.choice(self.upi_apps).lower()}"
        else:
            names = ['john', 'priya', 'amit', 'neha', 'raj', 'anjali', 'vikram', 'pooja']
            return f"{random.choice(names)}{random.randint(100,999)}@{random.choice(self.upi_apps).lower()}"
    
    def generate_qr_features(self, is_fraud=False):
        """Generate QR code features based on research (AUC 0.91+)"""
        if is_fraud and random.random() < 0.5:
            return {
                'qr_complexity': np.random.uniform(0.7, 1.0),  # High complexity
                'qr_error_correction': np.random.choice(['L', 'M']),  # Low correction
                'qr_version': np.random.randint(15, 40),  # Large version
                'qr_pixel_density': np.random.uniform(0.8, 1.0),
                'qr_has_logo': 0,  # No logo (suspicious)
                'qr_url_length': np.random.randint(150, 300)
            }
        else:
            return {
                'qr_complexity': np.random.uniform(0.2, 0.6),
                'qr_error_correction': np.random.choice(['H', 'Q']),
                'qr_version': np.random.randint(1, 10),
                'qr_pixel_density': np.random.uniform(0.3, 0.6),
                'qr_has_logo': 1,
                'qr_url_length': np.random.randint(20, 80)
            }
    
    def generate_phishing_features(self, is_fraud=False):
        """Generate phishing/vishing indicators"""
        if is_fraud and random.random() < 0.6:
            return {
                'contains_url': 1,
                'url_domain': random.choice(self.phishing_domains),
                'suspicious_keywords': np.random.randint(2, 5),
                'urgent_language': 1,
                'requests_pin': 1 if random.random() < 0.3 else 0,
                'mimics_bank': 1,
                'has_typosquatting': 1 if random.random() < 0.4 else 0
            }
        else:
            return {
                'contains_url': 0,
                'url_domain': None,
                'suspicious_keywords': 0,
                'urgent_language': 0,
                'requests_pin': 0,
                'mimics_bank': 0,
                'has_typosquatting': 0
            }
    
    def generate_collect_request_features(self, is_fraud=False):
        """Generate collect request exploit features (NPCI discontinued Oct 2025)"""
        # Note: P2P collect requests disabled from Oct 1, 2025
        is_collect_request = random.random() < 0.15  # Historical data
        
        if is_collect_request and is_fraud:
            return {
                'is_collect_request': 1,
                'collect_unsolicited': 1,
                'collect_from_unknown': 1,
                'collect_amount': np.random.uniform(1000, 2000),  # Below ₹2000 limit
                'collect_frequency_1h': np.random.randint(3, 10),  # Multiple requests
                'collect_timing': 'odd_hours' if random.random() < 0.6 else 'normal'
            }
        elif is_collect_request:
            return {
                'is_collect_request': 1,
                'collect_unsolicited': 0,
                'collect_from_unknown': 0,
                'collect_amount': np.random.uniform(100, 500),
                'collect_frequency_1h': 1,
                'collect_timing': 'normal'
            }
        else:
            return {
                'is_collect_request': 0,
                'collect_unsolicited': 0,
                'collect_from_unknown': 0,
                'collect_amount': 0,
                'collect_frequency_1h': 0,
                'collect_timing': 'normal'
            }
    
    def generate_malware_features(self, is_fraud=False):
        """Generate malware/device compromise indicators"""
        if is_fraud and random.random() < 0.3:
            return {
                'app_modified': 1,
                'root_jailbreak': 1 if random.random() < 0.5 else 0,
                'suspicious_permissions': np.random.randint(3, 8),
                'app_from_unknown_source': 1,
                'has_overlay_attack': 1 if random.random() < 0.4 else 0,
                'clipboard_hijack': 1 if random.random() < 0.3 else 0
            }
        else:
            return {
                'app_modified': 0,
                'root_jailbreak': 0,
                'suspicious_permissions': np.random.randint(0, 2),
                'app_from_unknown_source': 0,
                'has_overlay_attack': 0,
                'clipboard_hijack': 0
            }
    
    def generate_transaction_features(self, is_fraud=False):
        """Generate general transaction features"""
        base_amount = np.random.lognormal(6, 2) if not is_fraud else np.random.lognormal(7, 1.5)
        
        return {
            'amount': round(max(10, base_amount), 2),
            'hour': np.random.randint(0, 24),
            'day_of_week': np.random.randint(0, 7),
            'is_weekend': np.random.randint(0, 2),
            'payee_new': 1 if (is_fraud and random.random() < 0.7) or (not is_fraud and random.random() < 0.2) else 0,
            'transaction_count_24h': np.random.poisson(5 if not is_fraud else 12),
            'avg_transaction_amount_30d': np.random.lognormal(6, 1.5),
            'payee_category': random.choice(self.merchant_categories),
            'payer_bank': random.choice(self.banks),
            'payee_bank': random.choice(self.banks),
            'payer_upi_app': random.choice(self.upi_apps),
            'cross_bank': 1 if random.random() < 0.4 else 0
        }
    
    def generate_dataset(self):
        """Generate complete dataset"""
        print(f"Generating {self.n_samples} UPI transactions...")
        
        n_fraud = int(self.n_samples * self.fraud_rate)
        n_legit = self.n_samples - n_fraud
        
        labels = [1] * n_fraud + [0] * n_legit
        random.shuffle(labels)
        
        data = []
        
        for idx, is_fraud in enumerate(labels):
            if idx % 10000 == 0:
                print(f"Generated {idx}/{self.n_samples} transactions...")
            
            # Generate all feature groups
            txn_features = self.generate_transaction_features(is_fraud)
            phish_features = self.generate_phishing_features(is_fraud)
            qr_features = self.generate_qr_features(is_fraud)
            collect_features = self.generate_collect_request_features(is_fraud)
            malware_features = self.generate_malware_features(is_fraud)
            
            # Combine all features
            record = {
                'transaction_id': self.generate_transaction_id(idx),
                'timestamp': (datetime.now() - timedelta(days=random.randint(0, 90))).isoformat(),
                'payer_vpa': self.generate_vpa(is_fraud=False),
                'payee_vpa': self.generate_vpa(is_fraud=is_fraud),
                'is_fraud': is_fraud,
                **txn_features,
                **phish_features,
                **qr_features,
                **collect_features,
                **malware_features
            }
            
            data.append(record)
        
        df = pd.DataFrame(data)
        print(f"\nDataset generated: {len(df)} transactions, {df['is_fraud'].sum()} fraud cases ({df['is_fraud'].mean()*100:.2f}%)")
        return df

if __name__ == "__main__":
    generator = UPIDataGenerator(n_samples=200000)
    df = generator.generate_dataset()
    
    # Save dataset
    df.to_csv('upi_transactions_synthetic.csv', index=False)
    print("\nDataset saved to upi_transactions_synthetic.csv")
    
    # Print statistics
    print("\n=== Dataset Statistics ===")
    print(f"Total transactions: {len(df)}")
    print(f"Fraud cases: {df['is_fraud'].sum()} ({df['is_fraud'].mean()*100:.2f}%)")
    print(f"Average amount: ₹{df['amount'].mean():.2f}")
    print(f"Collect requests: {df['is_collect_request'].sum()}")
    print(f"Transactions with URLs: {df['contains_url'].sum()}")
    print(f"QR code transactions: {(df['qr_complexity'] > 0).sum()}")
