"""
Main Training Pipeline
Orchestrates training of all 4 fraud detection models
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import argparse
from datetime import datetime

# Import model trainers
from models.phishing_model import PhishingDetector
from models.qr_model import QuishingDetector
from models.collect_model import CollectRequestDetector
from models.malware_model import MalwareDetector
from feature_engineer import UPIFeatureEngineer

class TrainingPipeline:
    def __init__(self, data_path='upi_transactions_synthetic.csv', model_dir='models'):
        self.data_path = data_path
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        
        self.engineer = UPIFeatureEngineer()
        
    def load_and_prepare_data(self):
        """Load synthetic data and engineer features"""
        print("\n" + "="*60)
        print("STEP 1: Loading and preparing data")
        print("="*60)
        
        # Load raw data
        print(f"Loading data from {self.data_path}...")
        df = pd.read_csv(self.data_path)
        print(f"Loaded {len(df)} transactions, {df['is_fraud'].sum()} fraud cases")
        
        # Engineer features
        print("\nEngineering features...")
        df_engineered = self.engineer.engineer_all_features(df, fit=True)
        
        # Save engineered data
        engineered_path = 'upi_transactions_engineered.csv'
        df_engineered.to_csv(engineered_path, index=False)
        print(f"Engineered data saved to {engineered_path}")
        
        return df_engineered
    
    def train_all_models(self, df):
        """Train all 4 fraud detection models"""
        
        results = {}
        
        # 1. Train Phishing Detector
        print("\n" + "="*60)
        print("STEP 2: Training Phishing Detector (XGBoost)")
        print("="*60)
        try:
            phishing_detector = PhishingDetector()
            phishing_detector.train(df)
            phishing_detector.save(str(self.model_dir / 'phishing_detector.pkl'))
            results['phishing'] = 'SUCCESS'
        except Exception as e:
            print(f"ERROR training phishing detector: {str(e)}")
            results['phishing'] = f'FAILED: {str(e)}'
        
        # 2. Train Quishing Detector
        print("\n" + "="*60)
        print("STEP 3: Training Quishing Detector (Random Forest)")
        print("="*60)
        try:
            quishing_detector = QuishingDetector()
            quishing_detector.train(df)
            quishing_detector.save(str(self.model_dir / 'qr_detector.pkl'))
            results['quishing'] = 'SUCCESS'
        except Exception as e:
            print(f"ERROR training quishing detector: {str(e)}")
            results['quishing'] = f'FAILED: {str(e)}'
        
        # 3. Train Collect Request Detector
        print("\n" + "="*60)
        print("STEP 4: Training Collect Request Detector (Logistic Regression)")
        print("="*60)
        try:
            collect_detector = CollectRequestDetector()
            collect_detector.train(df)
            collect_detector.save(str(self.model_dir / 'collect_detector.pkl'))
            results['collect_request'] = 'SUCCESS'
        except Exception as e:
            print(f"ERROR training collect detector: {str(e)}")
            results['collect_request'] = f'FAILED: {str(e)}'
        
        # 4. Train Malware Detector
        print("\n" + "="*60)
        print("STEP 5: Training Malware Detector (XGBoost)")
        print("="*60)
        try:
            malware_detector = MalwareDetector()
            malware_detector.train(df)
            malware_detector.save(str(self.model_dir / 'malware_detector.pkl'))
            results['malware'] = 'SUCCESS'
        except Exception as e:
            print(f"ERROR training malware detector: {str(e)}")
            results['malware'] = f'FAILED: {str(e)}'
        
        return results
    
    def run(self):
        """Execute full training pipeline"""
        start_time = datetime.now()
        
        print("\n" + "="*60)
        print("UPI FRAUD DETECTION - TRAINING PIPELINE")
        print("="*60)
        print(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Load and prepare data
        df = self.load_and_prepare_data()
        
        # Train all models
        results = self.train_all_models(df)
        
        # Print summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "="*60)
        print("TRAINING PIPELINE COMPLETE")
        print("="*60)
        print(f"End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")
        
        print("\n=== MODEL TRAINING RESULTS ===")
        for model_name, status in results.items():
            status_icon = "✓" if status == "SUCCESS" else "✗"
            print(f"{status_icon} {model_name.upper()}: {status}")
        
        success_count = sum(1 for s in results.values() if s == "SUCCESS")
        print(f"\nTotal: {success_count}/{len(results)} models trained successfully")
        
        if success_count == len(results):
            print("\n🎉 All models trained successfully!")
            print(f"Models saved to: {self.model_dir.absolute()}")
        else:
            print("\n⚠️  Some models failed to train. Check errors above.")
            return False
        
        return True


def main():
    parser = argparse.ArgumentParser(description='Train UPI fraud detection models')
    parser.add_argument('--data', type=str, default='upi_transactions_synthetic.csv',
                        help='Path to synthetic data CSV')
    parser.add_argument('--model-dir', type=str, default='models',
                        help='Directory to save trained models')
    
    args = parser.parse_args()
    
    # Check if data file exists
    if not Path(args.data).exists():
        print(f"ERROR: Data file not found: {args.data}")
        print("Please run data_gen.py first to generate synthetic data")
        sys.exit(1)
    
    # Run training pipeline
    pipeline = TrainingPipeline(data_path=args.data, model_dir=args.model_dir)
    success = pipeline.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
