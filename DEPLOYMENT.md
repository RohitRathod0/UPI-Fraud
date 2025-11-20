# 🚀 Deployment Guide: Render.com

This guide will walk you through deploying your UPI Fraud Detection API on Render.

## Prerequisites

1. **GitHub Account** - Your code needs to be in a GitHub repository
2. **Render Account** - Sign up at [render.com](https://render.com) (free tier available)
3. **Trained Models** - Make sure your `.pkl` model files are committed to the repository

## Step 1: Prepare Your Repository

### 1.1 Ensure Models are in the Repository

Make sure your trained models are in the `server/models/` directory:
- `phishing_detector.pkl`
- `qr_detector.pkl` (or `quishing_detector.pkl`)
- `collect_detector.pkl`
- `malware_detector.pkl`

### 1.2 Verify File Structure

Your repository should have this structure:
```
finanace/
├── server/
│   ├── app.py
│   ├── models/
│   │   ├── phishing_detector.pkl
│   │   ├── qr_detector.pkl
│   │   ├── collect_detector.pkl
│   │   └── malware_detector.pkl
│   ├── agents/
│   ├── static/
│   └── ...
├── requirements.txt
├── render.yaml
└── README.md
```

### 1.3 Commit and Push to GitHub

```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

## Step 2: Create Render Account

1. Go to [render.com](https://render.com)
2. Click **"Get Started for Free"**
3. Sign up with your GitHub account (recommended) or email

## Step 3: Deploy Using render.yaml (Recommended)

### 3.1 Create New Web Service

1. In Render dashboard, click **"New +"** → **"Blueprint"**
2. Connect your GitHub repository
3. Render will automatically detect `render.yaml`
4. Click **"Apply"**

### 3.2 Manual Setup (Alternative)

If you prefer manual setup:

1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. Configure:
   - **Name**: `upi-fraud-detection-api`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `cd server && uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Root Directory**: Leave empty (or set to project root)

## Step 4: Create PostgreSQL Database

1. In Render dashboard, click **"New +"** → **"PostgreSQL"**
2. Configure:
   - **Name**: `upi-fraud-db`
   - **Database**: `upi_fraud_detection`
   - **User**: `upi_fraud_user`
   - **Plan**: Free (or Starter for production)
3. Click **"Create Database"**
4. Copy the **Internal Database URL** (you'll need this)

## Step 5: Configure Environment Variables

In your Render service settings, add these environment variables:

### Required Variables:
- `DATABASE_URL` - Automatically set if using render.yaml blueprint
- `MODEL_DIR` - Set to `./server/models`
- `PYTHON_VERSION` - Set to `3.11.0`

### Optional Variables:
- `HITL_ENABLED` - `true` (default)
- `LOG_LEVEL` - `INFO` (default)
- `TRUST_SCORE_ALLOW_THRESHOLD` - `65` (default)
- `TRUST_SCORE_WARN_THRESHOLD` - `45` (default)

### How to Add Environment Variables:

1. Go to your service in Render dashboard
2. Click **"Environment"** tab
3. Click **"Add Environment Variable"**
4. Add each variable and its value
5. Click **"Save Changes"**

## Step 6: Deploy

1. Render will automatically start building and deploying
2. Watch the build logs for any errors
3. Once deployed, you'll get a URL like: `https://upi-fraud-detection-api.onrender.com`

## Step 7: Verify Deployment

### 7.1 Check Health Endpoint

Visit: `https://your-app-name.onrender.com/health`

You should see:
```json
{
  "status": "healthy",
  "timestamp": "...",
  "agents": {
    "phishing": true,
    "quishing": true,
    "collect_request": true,
    "malware": true
  },
  "review_queue_depth": 0
}
```

### 7.2 Test API Endpoint

```bash
curl https://your-app-name.onrender.com/
```

Should return:
```json
{
  "message": "UPI Fraud Detection API",
  "version": "1.0.0",
  "status": "online"
}
```

### 7.3 Test Fraud Detection

```bash
curl -X POST https://your-app-name.onrender.com/api/v1/score_request \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "test-123",
    "amount": 1000,
    "payer_vpa": "user@paytm",
    "payee_vpa": "merchant@upi",
    "message": "Payment for services",
    "payee_new": false,
    "transaction_type": "PAY"
  }'
```

## Step 8: Access Your Dashboard

Visit: `https://your-app-name.onrender.com/pay`

This will show your payment UI.

## Troubleshooting

### Issue: Models Not Found

**Error**: `FileNotFoundError: [Errno 2] No such file or directory: '../models/...'`

**Solution**: 
- Ensure models are in `server/models/` directory
- Check that `MODEL_DIR` environment variable is set correctly
- Verify models are committed to Git (not in .gitignore)

### Issue: Database Connection Failed

**Error**: `OperationalError: could not connect to server`

**Solution**:
- Verify `DATABASE_URL` is set correctly
- Check PostgreSQL service is running
- Ensure database URL uses `postgresql://` (not `postgres://`)

### Issue: Build Fails

**Error**: `ERROR: Could not find a version that satisfies the requirement...`

**Solution**:
- Check `requirements.txt` for version conflicts
- Try updating package versions
- Check Python version compatibility

### Issue: App Crashes on Startup

**Error**: Application crashes immediately after deployment

**Solution**:
- Check build logs for errors
- Verify all dependencies are in `requirements.txt`
- Ensure start command is correct: `cd server && uvicorn app:app --host 0.0.0.0 --port $PORT`

### Issue: Slow Cold Starts

**Problem**: First request takes 30+ seconds

**Solution**:
- This is normal on free tier (spins down after inactivity)
- Upgrade to paid plan for always-on service
- Consider adding a health check ping service

## Free Tier Limitations

- **Spins down after 15 minutes of inactivity** - First request after spin-down takes ~30 seconds
- **750 hours/month** - Enough for most projects
- **512MB RAM** - Should be sufficient for your ML models
- **Limited CPU** - May be slower for heavy ML inference

## Upgrading to Paid Plan

If you need:
- Always-on service (no spin-down)
- More RAM/CPU
- Better performance

Upgrade to **Starter Plan** ($7/month) or higher.

## Next Steps

1. **Set up custom domain** (optional)
2. **Add monitoring** (Render provides basic logs)
3. **Set up CI/CD** (automatic deployments on git push)
4. **Configure backups** for PostgreSQL database

## Support

- Render Docs: https://render.com/docs
- Render Community: https://community.render.com
- Check your service logs in Render dashboard for detailed error messages

---

**Congratulations! 🎉 Your UPI Fraud Detection API is now live on Render!**

