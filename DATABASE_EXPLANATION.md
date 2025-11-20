# 🗄️ Database System - Complete Explanation

This document explains how databases work in your UPI Fraud Detection system.

## 📋 Table of Contents
1. [Database Configuration](#database-configuration)
2. [Database Models (Tables)](#database-models)
3. [Where Databases Are Called](#where-databases-are-called)
4. [How Database Connections Work](#how-database-connections-work)
5. [Data Flow Examples](#data-flow-examples)

---

## 🔧 Database Configuration

### File: `server/database.py`

**Location**: `server/database.py`

**What it does:**
- Sets up database connection (SQLite for local, PostgreSQL for production)
- Defines database models (tables)
- Creates database engine and session factory

### Key Components:

```python
# 1. DATABASE_URL - Connection String
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./upi_fraud_detection.db')

# Local Development: SQLite
# sqlite:///./upi_fraud_detection.db → Creates file: upi_fraud_detection.db

# Production (Render): PostgreSQL
# postgresql://user:password@host:port/database → Connects to Render's PostgreSQL
```

**Connection Logic:**
```python
# SQLite (Local)
if "sqlite" in DATABASE_URL:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# PostgreSQL (Production)
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)
```

**Session Factory:**
```python
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# This creates a factory that produces database sessions
```

---

## 📊 Database Models (Tables)

Your system has **3 main database tables**:

### 1. **ReviewQueue** Table
**Purpose**: Stores transactions that need human review

**Location**: `server/database.py` (lines 31-43)

**Columns:**
- `id` - Primary key (auto-increment)
- `transaction_id` - Unique transaction identifier
- `trust_score` - AI's calculated trust score (0-100)
- `priority` - Review priority (CRITICAL, HIGH, MEDIUM, LOW)
- `request_data` - Full transaction data (stored as JSON string)
- `subscores` - Individual agent scores (stored as JSON string)
- `created_at` - When transaction was queued
- `reviewed` - Boolean: Has it been reviewed?
- `analyst_id` - Who reviewed it (if reviewed)
- `decision` - Analyst's decision (APPROVE/REJECT/ESCALATE)

**When it's used:**
- When AI flags a transaction for human review
- When analysts check the review queue
- When analysts submit their decisions

---

### 2. **FeedbackLog** Table
**Purpose**: Stores analyst feedback for model retraining

**Location**: `server/database.py` (lines 45-57)

**Columns:**
- `id` - Primary key
- `transaction_id` - Reference to transaction
- `original_trust_score` - What AI predicted
- `original_subscores` - AI's detailed scores (JSON)
- `analyst_decision` - What analyst decided
- `correct_label` - Ground truth (0=legitimate, 1=fraud)
- `feedback_text` - Analyst's comments
- `model_was_correct` - Was AI right? (0 or 1)
- `created_at` - When feedback was logged
- `used_for_retraining` - Has this been used to retrain models?

**When it's used:**
- When analyst submits feedback
- When collecting data for model retraining
- When tracking model accuracy

---

### 3. **AnalystMetrics** Table
**Purpose**: Tracks analyst performance

**Location**: `server/database.py` (lines 59-67)

**Columns:**
- `id` - Primary key
- `analyst_id` - Unique analyst identifier
- `total_reviews` - How many reviews completed
- `correct_decisions` - How many were correct
- `avg_review_time_seconds` - Average time per review
- `last_active` - Last review timestamp

**When it's used:**
- Tracking analyst performance
- Quality assurance
- (Currently not fully implemented)

---

## 🔄 Where Databases Are Called

### 1. **App Startup** (`server/app.py`)

**Line 32:**
```python
Base.metadata.create_all(bind=engine)
```
**What it does:**
- Creates all database tables if they don't exist
- Runs once when the app starts
- Safe to run multiple times (won't recreate existing tables)

---

### 2. **Database Dependency Function** (`server/app.py`)

**Lines 84-89:**
```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**What it does:**
- Creates a database session for each API request
- Automatically closes the session when request completes
- Used by FastAPI's dependency injection system

**How it's used:**
```python
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    # 'db' is automatically provided by FastAPI
    # It's a database session you can query with
```

---

### 3. **Health Check Endpoint** (`server/app.py`)

**Lines 102-120:**
```python
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    queue_depth = db.query(ReviewQueue).filter(
        ReviewQueue.reviewed == False
    ).count()
```

**What it does:**
- Checks how many transactions are waiting for review
- Tests database connection
- Returns system health status

**Database Query:**
```python
# SQL Equivalent:
# SELECT COUNT(*) FROM review_queue WHERE reviewed = False
```

---

### 4. **Transaction Scoring** (`server/app.py`)

**Lines 122-242:**
```python
@app.post("/api/v1/score_request")
async def score_transaction(request: TransactionRequest, db: Session = Depends(get_db)):
    # ... AI analysis happens ...
    
    if hitl_result['human_review_required']:
        entry = ReviewQueue(
            transaction_id=request.transaction_id,
            trust_score=float(trust_score),
            priority=hitl_result['priority'],
            request_data=json.dumps(request.dict()),
            subscores=json.dumps(subs),
            reviewed=False
        )
        db.add(entry)      # Add to session
        db.commit()        # Save to database
```

**What it does:**
1. Receives transaction request
2. Runs AI agents to analyze
3. If AI flags for review → **Creates database entry**
4. Saves transaction to `ReviewQueue` table

**Database Operations:**
- `db.add(entry)` - Adds new record to session
- `db.commit()` - Saves changes to database

---

### 5. **Get Review Queue** (`server/app.py`)

**Lines 244-262:**
```python
@app.get("/api/v1/analyst/review_queue")
async def get_review_queue(db: Session = Depends(get_db)):
    queue = db.query(ReviewQueue).filter(
        ReviewQueue.reviewed == False
    ).order_by(
        ReviewQueue.created_at.desc()
    ).all()
```

**What it does:**
- Fetches all unreviewed transactions
- Orders by creation time (newest first)
- Returns list for analyst dashboard

**Database Query:**
```python
# SQL Equivalent:
# SELECT * FROM review_queue 
# WHERE reviewed = False 
# ORDER BY created_at DESC
```

---

### 6. **Submit Review** (`server/app.py`)

**Lines 264-279:**
```python
@app.post("/api/v1/analyst/review")
async def submit_review(decision: ReviewDecision, db: Session = Depends(get_db)):
    item = db.query(ReviewQueue).filter(
        ReviewQueue.transaction_id == decision.transaction_id
    ).first()
    
    item.reviewed = True
    item.analyst_id = decision.analyst_id
    item.decision = decision.decision
    db.commit()
```

**What it does:**
1. Finds transaction in queue
2. Updates it with analyst's decision
3. Marks as reviewed
4. Saves changes

**Database Operations:**
- `db.query().filter().first()` - Find one record
- Modify object attributes
- `db.commit()` - Save changes

---

### 7. **Review Queue Manager** (`server/hitl/review_queue.py`)

**Purpose**: Advanced queue management (currently not used in main app)

**Key Methods:**
- `add_to_queue()` - Adds transaction to queue
- `get_queue()` - Gets pending items
- `get_queue_depth()` - Counts pending items
- `get_overdue_items()` - Finds items past SLA deadline

**Note**: This file creates its own database sessions:
```python
db = SessionLocal()
try:
    # Database operations
finally:
    db.close()
```

---

### 8. **Feedback Processor** (`server/hitl/feedback_processor.py`)

**Purpose**: Processes analyst feedback for retraining

**Key Methods:**

**`process_feedback()`** (Lines 13-73):
```python
feedback_log = FeedbackLog(
    transaction_id=transaction_id,
    original_trust_score=original_trust_score,
    analyst_decision=analyst_decision,
    correct_label=correct_label,
    # ...
)
db.add(feedback_log)
db.commit()
```
- Saves analyst feedback to `FeedbackLog` table
- Determines if AI was correct
- Updates analyst metrics

**`get_retraining_data()`** (Lines 81-108):
```python
feedback_items = db.query(FeedbackLog).filter(
    FeedbackLog.used_for_retraining == 0
).limit(min_samples * 2).all()
```
- Fetches feedback not yet used for training
- Returns data for model retraining

**`mark_used_for_retraining()`** (Lines 110-123):
```python
db.query(FeedbackLog).filter(
    FeedbackLog.transaction_id.in_(transaction_ids)
).update({'used_for_retraining': 1})
```
- Marks feedback as used after retraining

---

## 🔌 How Database Connections Work

### Connection Flow:

```
1. App Starts
   ↓
2. database.py loads
   ↓
3. Creates Engine (connection pool)
   ↓
4. Creates SessionLocal (session factory)
   ↓
5. Base.metadata.create_all() → Creates tables
   ↓
6. API Request Arrives
   ↓
7. get_db() called → Creates new Session
   ↓
8. Database query executed
   ↓
9. Session closed (finally block)
```

### Session Management:

**FastAPI Dependency Pattern:**
```python
def get_db():
    db = SessionLocal()      # Create session
    try:
        yield db             # Give to route handler
    finally:
        db.close()           # Always close, even on error
```

**Why this pattern?**
- Ensures sessions are always closed
- Prevents connection leaks
- One session per request

**Manual Session Pattern** (in review_queue.py):
```python
db = SessionLocal()
try:
    # Do database work
finally:
    db.close()
```

---

## 📈 Data Flow Examples

### Example 1: Transaction Flagged for Review

```
1. POST /api/v1/score_request
   ↓
2. AI analyzes transaction
   ↓
3. Trust score = 35 (low)
   ↓
4. HITL Manager: "human_review_required = True"
   ↓
5. Create ReviewQueue entry:
   - transaction_id = "txn_123"
   - trust_score = 35.0
   - priority = "HIGH"
   - reviewed = False
   ↓
6. db.add(entry) → db.commit()
   ↓
7. Entry saved to database ✅
```

### Example 2: Analyst Reviews Transaction

```
1. GET /api/v1/analyst/review_queue
   ↓
2. db.query(ReviewQueue).filter(reviewed=False).all()
   ↓
3. Returns list of pending transactions
   ↓
4. Analyst selects transaction "txn_123"
   ↓
5. POST /api/v1/analyst/review
   {
     "transaction_id": "txn_123",
     "analyst_id": "analyst_001",
     "decision": "BLOCK"
   }
   ↓
6. Find: db.query(ReviewQueue).filter(transaction_id="txn_123").first()
   ↓
7. Update:
   - item.reviewed = True
   - item.analyst_id = "analyst_001"
   - item.decision = "BLOCK"
   ↓
8. db.commit() → Saved ✅
```

### Example 3: Feedback Logged for Retraining

```
1. Analyst submits review (BLOCK)
   ↓
2. FeedbackProcessor.process_feedback() called
   ↓
3. Create FeedbackLog entry:
   - transaction_id = "txn_123"
   - original_trust_score = 35.0
   - analyst_decision = "BLOCK"
   - correct_label = 1 (fraud)
   - model_was_correct = 1 (AI was right)
   ↓
4. db.add(feedback_log) → db.commit()
   ↓
5. Later: get_retraining_data() fetches this for model training
```

---

## 🗺️ Database File Locations

### Local Development:
- **SQLite Database**: `upi_fraud_detection.db` (in project root)
- **Connection**: `sqlite:///./upi_fraud_detection.db`

### Production (Render):
- **PostgreSQL Database**: Managed by Render
- **Connection**: `postgresql://user:pass@host:port/db` (from environment variable)

---

## 🔍 Key Database Operations Summary

| Operation | Method | Location | Purpose |
|-----------|--------|----------|---------|
| **Create Tables** | `Base.metadata.create_all()` | `app.py:32` | Initialize database |
| **Get Session** | `get_db()` | `app.py:84` | FastAPI dependency |
| **Add to Queue** | `db.add()` + `db.commit()` | `app.py:211-212` | Save transaction |
| **Query Queue** | `db.query(ReviewQueue).filter()` | `app.py:246` | Get pending items |
| **Update Record** | Modify + `db.commit()` | `app.py:270-273` | Update review status |
| **Count Records** | `db.query().count()` | `app.py:105` | Count queue depth |
| **Log Feedback** | `db.add(FeedbackLog)` | `feedback_processor.py:61` | Save feedback |

---

## 🛠️ Database Technologies Used

1. **SQLAlchemy ORM** - Python database toolkit
   - Converts Python objects to SQL
   - Handles connections, transactions
   - Works with SQLite and PostgreSQL

2. **SQLite** (Local)
   - File-based database
   - No server needed
   - Good for development

3. **PostgreSQL** (Production)
   - Full-featured database server
   - Better for production
   - Managed by Render

---

## ⚠️ Important Notes

1. **Sessions must be closed** - Always use `try/finally` or FastAPI's dependency injection
2. **Transactions** - Changes aren't saved until `db.commit()`
3. **JSON Storage** - Complex data stored as JSON strings (request_data, subscores)
4. **Connection Pooling** - PostgreSQL uses connection pooling for performance
5. **Thread Safety** - SQLite needs `check_same_thread=False` for FastAPI

---

## 🚀 Next Steps

To see database in action:
1. Start your server: `cd server && uvicorn app:app`
2. Make a transaction request
3. Check database: `sqlite3 upi_fraud_detection.db "SELECT * FROM review_queue;"`
4. Or use a database viewer tool

---

**Questions?** Check the code comments or ask for clarification on any part!



