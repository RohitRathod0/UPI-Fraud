"""
Configuration management
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/upi_fraud_detection')
    
    # Redis
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
    
    # External APIs
    GOOGLE_SAFE_BROWSING_API_KEY = os.getenv('GOOGLE_SAFE_BROWSING_API_KEY', '')
    PHISHTANK_API_KEY = os.getenv('PHISHTANK_API_KEY', '')
    
    # Model paths
    MODEL_DIR = os.getenv('MODEL_DIR', './models')
    PHISHING_MODEL_PATH = f'{MODEL_DIR}/phishing_detector.pkl'
    QR_MODEL_PATH = f'{MODEL_DIR}/qr_detector.pkl'
    COLLECT_MODEL_PATH = f'{MODEL_DIR}/collect_detector.pkl'
    MALWARE_MODEL_PATH = f'{MODEL_DIR}/malware_detector.pkl'
    
    # HITL Configuration
    HITL_ENABLED = os.getenv('HITL_ENABLED', 'true').lower() == 'true'
    REVIEW_QUEUE_MAX_SIZE = int(os.getenv('REVIEW_QUEUE_MAX_SIZE', 1000))
    
    # SLA deadlines (minutes)
    SLA_CRITICAL = int(os.getenv('SLA_CRITICAL', 2))
    SLA_HIGH = int(os.getenv('SLA_HIGH', 10))
    SLA_MEDIUM = int(os.getenv('SLA_MEDIUM', 30))
    SLA_LOW = int(os.getenv('SLA_LOW', 1440))
    
    # Trust score thresholds
    TRUST_SCORE_ALLOW_THRESHOLD = int(os.getenv('TRUST_SCORE_ALLOW_THRESHOLD', 65))
    TRUST_SCORE_WARN_THRESHOLD = int(os.getenv('TRUST_SCORE_WARN_THRESHOLD', 45))
    
    # Feature flags
    ENABLE_CLAMAV = os.getenv('ENABLE_CLAMAV', 'false').lower() == 'true'
    ENABLE_EXTERNAL_API_CALLS = os.getenv('ENABLE_EXTERNAL_API_CALLS', 'true').lower() == 'true'
    
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    API_KEY_HEADER = 'X-API-Key'
    
    # Monitoring
    PROMETHEUS_ENABLED = os.getenv('PROMETHEUS_ENABLED', 'true').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

config = Config()
