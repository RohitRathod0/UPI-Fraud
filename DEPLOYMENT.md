# 🚀 Deployment Guide: Railway.app

**Free Tier: $5 credit/month, No credit card required initially!**

Railway is perfect for deploying your FastAPI application with ML models. It's simple, fast, and has a generous free tier.

## 🎯 Why Railway?

✅ **$5 free credit/month** - Enough for small projects  
✅ **No credit card required** initially  
✅ **Automatic deployments** from GitHub  
✅ **PostgreSQL included** - Easy database setup  
✅ **Simple configuration** - Just connect and deploy  
✅ **Fast builds** - Usually 2-3 minutes  

## 📋 Prerequisites

1. **GitHub Account** - Your code must be in a GitHub repository
2. **Railway Account** - Sign up at [railway.app](https://railway.app) (free)
3. **Trained Models** - Models should be in `server/models/` directory

## 🚀 Quick Deployment Steps

### Step 1: Sign Up for Railway

1. Go to [railway.app](https://railway.app)
2. Click **"Start a New Project"**
3. Sign up with GitHub (recommended) or email
4. Authorize Railway to access your GitHub repositories

### Step 2: Create New Project

1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Choose your repository: `UPI-Fraud` (or your repo name)
4. Railway will automatically detect it's a Python project

### Step 3: Configure Service

Railway will auto-detect your project, but verify these settings:

**Settings to check:**
- **Root Directory**: Leave empty (or set to project root)
- **Build Command**: `pip install -r requirements.txt` (auto-detected)
- **Start Command**: `cd server && uvicorn app:app --host 0.0.0.0 --port $PORT` (auto-detected)

**If not auto-detected, add manually:**
- Go to your service → **Settings** → **Deploy**
- Set **Start Command**: `cd server && uvicorn app:app --host 0.0.0.0 --port $PORT`

### Step 4: Add Environment Variables

Go to your service → **Variables** tab, add:

| Variable | Value | Required |
|----------|-------|----------|
| `MODEL_DIR` | `./server/models` | ✅ Yes |
| `HITL_ENABLED` | `true` | Optional |
| `LOG_LEVEL` | `INFO` | Optional |
| `PYTHON_VERSION` | `3.11.0` | Optional |

**Note**: `DATABASE_URL` will be added automatically when you create a database.

### Step 5: Create PostgreSQL Database

1. In your Railway project, click **"+ New"**
2. Select **"Database"** → **"Add PostgreSQL"**
3. Railway automatically:
   - Creates the database
   - Adds `DATABASE_URL` environment variable
   - Links it to your service

**That's it!** Railway will start deploying automatically.

### Step 6: Wait for Deployment

1. Watch the build logs in Railway dashboard
2. Build takes 2-5 minutes
3. Once deployed, you'll get a URL like: `https://your-app-name.up.railway.app`

## ✅ Verify Deployment

### Test Health Endpoint

```bash
curl https://your-app-name.up.railway.app/health
```

Should return:
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

### Test API

```bash
curl -X POST https://your-app-name.up.railway.app/api/v1/score_request \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "test-123",
    "amount": 1000,
    "payer_vpa": "user@paytm",
    "payee_vpa": "merchant@upi",
    "message": "Payment for services",
    "payee_new": 0,
    "transaction_type": "pay"
  }'
```

## 💰 Free Tier Limits

**What you get:**
- **$5 credit/month** - Usually enough for 1-2 small services
- **512MB RAM** - Sufficient for your ML models
- **1GB storage** - For database and files
- **100GB bandwidth** - Plenty for API calls

**What happens when you exceed:**
- Railway will notify you
- Service continues running
- You can upgrade or optimize usage

## 🔧 Troubleshooting

### Issue: Models Not Found

**Error**: `FileNotFoundError: [Errno 2] No such file or directory`

**Solution:**
1. Ensure models are committed: `git add server/models/*.pkl`
2. Check `MODEL_DIR` environment variable is set to `./server/models`
3. Verify models are in the repository (check GitHub)

### Issue: Database Connection Failed

**Error**: `OperationalError: could not connect to server`

**Solution:**
1. Verify PostgreSQL service is running in Railway
2. Check `DATABASE_URL` is set (should be automatic)
3. Restart your service after creating database

### Issue: Build Fails

**Error**: `ERROR: Could not find a version that satisfies the requirement...`

**Solution:**
1. Check `requirements.txt` for version conflicts
2. Try updating package versions
3. Check build logs for specific error

### Issue: Service Crashes

**Error**: Application crashes on startup

**Solution:**
1. Check logs in Railway dashboard
2. Verify start command is correct
3. Ensure all dependencies are in `requirements.txt`
4. Check Python version compatibility

## 📊 Monitoring

Railway provides:
- **Real-time logs** - View in dashboard
- **Metrics** - CPU, memory, network usage
- **Deployment history** - See all deployments
- **Environment variables** - Manage in dashboard

## 🔄 Automatic Deployments

Railway automatically deploys when you:
- Push to main branch
- Merge pull requests
- Manually trigger deployment

**To disable auto-deploy:**
- Go to service → Settings → Source
- Toggle "Auto Deploy"

## 🎨 Custom Domain (Optional)

1. Go to service → Settings → Networking
2. Click "Generate Domain" or "Add Custom Domain"
3. Follow instructions to configure DNS

## 📝 Next Steps

1. **Set up monitoring** - Use Railway's built-in metrics
2. **Configure backups** - Railway handles PostgreSQL backups automatically
3. **Add custom domain** - For production use
4. **Set up alerts** - Get notified of issues

## 🆘 Need Help?

- **Railway Docs**: https://docs.railway.app
- **Railway Discord**: https://discord.gg/railway
- **Check logs** in Railway dashboard for detailed errors

---

**Congratulations! 🎉 Your UPI Fraud Detection API is now live on Railway!**

