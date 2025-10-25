"""
Database configuration for SQLite
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Use SQLite (no PostgreSQL needed)
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./upi_fraud_detection.db')

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class ReviewQueue(Base):
    __tablename__ = "review_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, unique=True, index=True)
    trust_score = Column(Float)
    priority = Column(String)
    request_data = Column(String)  # JSON as string
    subscores = Column(String)  # JSON as string
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed = Column(Boolean, default=False)
    analyst_id = Column(String, nullable=True)
    decision = Column(String, nullable=True)

class FeedbackLog(Base):
    __tablename__ = "feedback_log"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, index=True)
    original_trust_score = Column(Float)
    original_subscores = Column(String)  # JSON as string
    analyst_decision = Column(String)
    correct_label = Column(Integer)
    feedback_text = Column(String, nullable=True)
    model_was_correct = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    used_for_retraining = Column(Integer, default=0)

class AnalystMetrics(Base):
    __tablename__ = "analyst_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    analyst_id = Column(String, unique=True, index=True)
    total_reviews = Column(Integer, default=0)
    correct_decisions = Column(Integer, default=0)
    avg_review_time_seconds = Column(Float, default=0.0)
    last_active = Column(DateTime, default=datetime.utcnow)
