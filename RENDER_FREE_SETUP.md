# 🆓 Render Free Tier - Manual Setup (No Payment Required)

If you want to avoid adding payment information, follow these steps to manually create services on the free tier.

## Step 1: Create Web Service (Free)

1. In Render dashboard, click **"New +"** → **"Web Service"**
2. Connect your GitHub repository: `UPI-Fraud`
3. Configure:
   - **Name**: `upi-fraud-detection-api`
   - **Region**: Choose closest (e.g., `Oregon`)
   - **Branch**: `main`
   - **Root Directory**: Leave empty
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `cd server && uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Select **"Free"** (important!)
4. Click **"Create Web Service"**

## Step 2: Add Environment Variables

In your web service settings → **"Environment"** tab, add:

- `MODEL_DIR` = `./server/models`
- `HITL_ENABLED` = `true`
- `LOG_LEVEL` = `INFO`

## Step 3: Create PostgreSQL Database (Free)

1. Click **"New +"** → **"Postgres"**
2. Configure:
   - **Name**: `upi-fraud-db`
   - **Database**: `upi_fraud_detection`
   - **User**: `upi_fraud_user`
   - **Region**: Same as web service
   - **PostgreSQL Version**: `15` (or latest)
   - **Plan**: Select **"Free"** (important!)
3. Click **"Create Database"**

## Step 4: Link Database to Web Service

1. Go back to your web service
2. **"Environment"** tab
3. Click **"Link Database"**
4. Select `upi-fraud-db`
5. This automatically adds `DATABASE_URL` environment variable

## Step 5: Deploy

1. Render will automatically start building
2. Watch the build logs
3. Wait 5-10 minutes for deployment

## Free Tier Limits

✅ **What's Free:**
- 750 hours/month (enough for 24/7 operation)
- 512MB RAM
- Shared CPU
- PostgreSQL database (90 days retention)

⚠️ **Limitations:**
- Service spins down after 15 min inactivity (cold start ~30 sec)
- Limited CPU (may be slower)
- Database auto-pauses after 90 days of inactivity

---

**Note**: If Render still asks for payment info, you can:
- Add a card (won't be charged for free tier)
- Or try alternative platforms: Railway, Fly.io, or PythonAnywhere

