"""
HITL Model Retrainer
Retrains models using human-labeled feedback data
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import argparse
import sys

from models.phishing_model import PhishingDetector
from models.qr_model import QuishingDetector
from models.collect_model import CollectRequestDetector
from models.malware_model import MalwareDetector
from feature_engineer import UPIFeatureEngineer

import sqlalchemy
from sqlalchemy import create_engine
import os

class HITLRetrainer:
    def __init__(self, weeks_lookback=4, min_samples=100):
        self.weeks_lookback = weeks_lookback
        self.min_samples = min_samples
        self.engineer = UPIFeatureEngineer()
        
        # Database connection
        db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/upi_fraud_detection')
        self.engine = create_engine(db_url)
    
    def fetch_feedback_data(self):
        """Fetch human-labeled transactions from feedback_log"""
        print("\n=== Fetching Human Feedback Data ===")
        
        cutoff_date = datetime.utcnow() - timedelta(weeks=self.weeks_lookback)
        
        query = f"""
        SELECT 
            fl.transaction_id,
            fl.correct_label,
            fl.original_trust_score,
            fl.original_subscores,
            fl.analyst_decision,
            fl.feedback_text,
            fl.created_at,
            rq.request_data
        FROM feedback_log fl
        JOIN review_queue rq ON fl.transaction_id = rq.transaction_id
        WHERE fl.used_for_retraining = 0
        AND fl.created_at >= '{cutoff_date.isoformat()}'
        AND fl.analyst_decision IN ('APPROVE', 'BLOCK')
        ORDER BY fl.created_at DESC
        """
        
        try:
            df_feedback = pd.read_sql(query, self.engine)
            print(f"Fetched {len(df_feedback)} feedback records from last {self.weeks_lookback} weeks")
            
            if len(df_feedback) < self.min_samples:
                print(f"⚠️  Insufficient feedback data ({len(df_feedback)} < {self.min_samples})")
                print("Need more human reviews before retraining")
                return None
            
            return df_feedback
            
        except Exception as e:
            print(f"Error fetching feedback data: {str(e)}")
            return None
    
    def prepare_retraining_dataset(self, df_feedback, original_data_path='upi_transactions_engineered.csv'):
        """Combine feedback data with original training data"""
        print("\n=== Preparing Retraining Dataset ===")
        
        # Load original training data
        df_original = pd.read_csv(original_data_path)
        print(f"Original training data: {len(df_original)} samples")
        
        # Parse feedback data and create new samples
        feedback_samples = []
        for _, row in df_feedback.iterrows():
            try:
                request_data = eval(row['request_data'])  # Parse JSON string
                
                # Create sample with corrected label
                sample = {
                    'transaction_id': row['transaction_id'],
                    'is_fraud': row['correct_label'],
                    'amount': request_data.get('amount', 0),
                    'payer_vpa': request_data.get('payer_vpa', ''),
                    'payee_vpa': request_data.get('payee_vpa', ''),
                    # Add other fields as needed
                }
                feedback_samples.append(sample)
                
            except Exception as e:
                print(f"Error parsing feedback row {row['transaction_id']}: {str(e)}")
        
        df_feedback_samples = pd.DataFrame(feedback_samples)
        print(f"Parsed {len(df_feedback_samples)} feedback samples")
        
        # Engineer features for feedback samples
        df_feedback_engineered = self.engineer.engineer_all_features(df_feedback_samples, fit=False)
        
        # Combine with original data (oversample feedback data for importance)
        oversample_factor = 3  # Give human feedback more weight
        df_feedback_oversampled = pd.concat([df_feedback_engineered] * oversample_factor, ignore_index=True)
        
        df_combined = pd.concat([df_original, df_feedback_oversampled], ignore_index=True)
        print(f"Combined dataset: {len(df_combined)} samples")
        print(f"  - Original: {len(df_original)}")
        print(f"  - Feedback (oversampled): {len(df_feedback_oversampled)}")
        
        return df_combined, df_feedback
    
    def retrain_models(self, df_combined):
        """Retrain all 4 models with human feedback"""
        print("\n=== Retraining Models with Human Feedback ===")
        
        results = {}
        
        # 1. Retrain Phishing Detector
        print("\n--- Retraining Phishing Detector ---")
        try:
            phishing_detector = PhishingDetector()
            phishing_detector.train(df_combined)
            phishing_detector.save('models/phishing_detector_v2.pkl')
            results['phishing'] = 'SUCCESS'
        except Exception as e:
            print(f"ERROR: {str(e)}")
            results['phishing'] = 'FAILED'
        
        # 2. Retrain Quishing Detector
        print("\n--- Retraining Quishing Detector ---")
        try:
            quishing_detector = QuishingDetector()
            quishing_detector.train(df_combined)
            quishing_detector.save('models/qr_detector_v2.pkl')
            results['quishing'] = 'SUCCESS'
        except Exception as e:
            print(f"ERROR: {str(e)}")
            results['quishing'] = 'FAILED'
        
        # 3. Retrain Collect Request Detector
        print("\n--- Retraining Collect Request Detector ---")
        try:
            collect_detector = CollectRequestDetector()
            collect_detector.train(df_combined)
            collect_detector.save('models/collect_detector_v2.pkl')
            results['collect'] = 'SUCCESS'
        except Exception as e:
            print(f"ERROR: {str(e)}")
            results['collect'] = 'FAILED'
        
        # 4. Retrain Malware Detector
        print("\n--- Retraining Malware Detector ---")
        try:
            malware_detector = MalwareDetector()
            malware_detector.train(df_combined)
            malware_detector.save('models/malware_detector_v2.pkl')
            results['malware'] = 'SUCCESS'
        except Exception as e:
            print(f"ERROR: {str(e)}")
            results['malware'] = 'FAILED'
        
        return results
    
    def mark_feedback_as_used(self, df_feedback):
        """Mark feedback records as used for retraining"""
        print("\n=== Marking Feedback as Used ===")
        
        transaction_ids = df_feedback['transaction_id'].tolist()
        
        query = f"""
        UPDATE feedback_log
        SET used_for_retraining = 1
        WHERE transaction_id IN ({','.join([f"'{tid}'" for tid in transaction_ids])})
        """
        
        try:
            with self.engine.connect() as conn:
                conn.execute(query)
            print(f"Marked {len(transaction_ids)} feedback records as used")
        except Exception as e:
            print(f"Error marking feedback: {str(e)}")
    
    def run(self):
        """Execute HITL retraining pipeline"""
        print("\n" + "="*60)
        print("HITL MODEL RETRAINING PIPELINE")
        print("="*60)
        print(f"Lookback period: {self.weeks_lookback} weeks")
        print(f"Minimum samples: {self.min_samples}")
        
        # Step 1: Fetch feedback data
        df_feedback = self.fetch_feedback_data()
        if df_feedback is None:
            print("\n⚠️  Skipping retraining - insufficient data")
            return False
        
        # Step 2: Prepare retraining dataset
        df_combined, df_feedback = self.prepare_retraining_dataset(df_feedback)
        
        # Step 3: Retrain models
        results = self.retrain_models(df_combined)
        
        # Step 4: Mark feedback as used
        success_count = sum(1 for s in results.values() if s == "SUCCESS")
        if success_count == len(results):
            self.mark_feedback_as_used(df_feedback)
        
        # Print summary
        print("\n" + "="*60)
        print("RETRAINING COMPLETE")
        print("="*60)
        for model, status in results.items():
            icon = "✓" if status == "SUCCESS" else "✗"
            print(f"{icon} {model}: {status}")
        
        print(f"\nModels trained: {success_count}/{len(results)}")
        
        if success_count == len(results):
            print("\n🎉 All models retrained successfully with human feedback!")
            print("New model versions saved with '_v2' suffix")
            print("To deploy: rename _v2 models to replace original models")
        else:
            print("\n⚠️  Some models failed to retrain")
        
        return success_count == len(results)


def main():
    parser = argparse.ArgumentParser(description='Retrain models with human feedback')
    parser.add_argument('--weeks', type=int, default=4,
                        help='Weeks of feedback to include (default: 4)')
    parser.add_argument('--min-samples', type=int, default=100,
                        help='Minimum feedback samples required (default: 100)')
    
    args = parser.parse_args()
    
    retrainer = HITLRetrainer(weeks_lookback=args.weeks, min_samples=args.min_samples)
    success = retrainer.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
