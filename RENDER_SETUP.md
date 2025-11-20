# 🚀 Quick Render Deployment Steps

## Pre-Deployment Checklist

✅ **Models are committed to Git**
```bash
# Make sure your models are in server/models/ and committed
git add server/models/*.pkl
git commit -m "Add ML models for deployment"
git push
```

✅ **Code is pushed to GitHub**
- Your repository should be on GitHub
- All files are committed and pushed

## Step-by-Step Deployment

### Step 1: Sign Up / Log In to Render
1. Go to https://render.com
2. Click **"Get Started for Free"** or **"Sign In"**
3. Sign up with GitHub (recommended for easy repo connection)

### Step 2: Create New Web Service
1. In Render dashboard, click **"New +"** button (top right)
2. Select **"Web Service"**
3. Connect your GitHub account if not already connected
4. Select your repository: `finanace` (or your repo name)
5. Click **"Connect"**

### Step 3: Configure Service
Fill in these settings:

**Basic Settings:**
- **Name**: `upi-fraud-detection-api` (or your preferred name)
- **Region**: Choose closest to you (e.g., `Oregon (US West)`)
- **Branch**: `main` (or `master`)
- **Root Directory**: Leave empty
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `cd server && uvicorn app:app --host 0.0.0.0 --port $PORT`

**Plan:**
- Select **Free** (or upgrade later if needed)

### Step 4: Add Environment Variables
Click **"Advanced"** → **"Add Environment Variable"** and add:

| Key | Value |
|-----|-------|
| `MODEL_DIR` | `./server/models` |
| `HITL_ENABLED` | `true` |
| `LOG_LEVEL` | `INFO` |

**Note**: `DATABASE_URL` will be added automatically when you create the database.

### Step 5: Create PostgreSQL Database
1. In Render dashboard, click **"New +"** → **"PostgreSQL"**
2. Configure:
   - **Name**: `upi-fraud-db`
   - **Database**: `upi_fraud_detection`
   - **User**: `upi_fraud_user`
   - **Region**: Same as your web service
   - **PostgreSQL Version**: `15` (or latest)
   - **Plan**: **Free** (or Starter for production)
3. Click **"Create Database"**
4. Wait for database to be created (takes ~1 minute)

### Step 6: Link Database to Web Service
1. Go back to your web service settings
2. Go to **"Environment"** tab
3. You should see `DATABASE_URL` automatically added
4. If not, click **"Link Database"** and select `upi-fraud-db`

### Step 7: Deploy!
1. Scroll to bottom of settings page
2. Click **"Create Web Service"**
3. Watch the build logs - deployment takes 5-10 minutes
4. You'll see build progress in real-time

### Step 8: Verify Deployment
Once deployed, you'll get a URL like: `https://upi-fraud-detection-api.onrender.com`

**Test the API:**
```bash
# Health check
curl https://your-app-name.onrender.com/health

# Root endpoint
curl https://your-app-name.onrender.com/
```

## Important Notes

⚠️ **Free Tier Limitations:**
- Service spins down after 15 minutes of inactivity
- First request after spin-down takes ~30 seconds (cold start)
- 750 hours/month free (enough for most projects)

💡 **Tips:**
- Use the health endpoint to keep service warm: Set up a cron job to ping `/health` every 10 minutes
- Upgrade to Starter plan ($7/month) for always-on service
- Check logs in Render dashboard if something goes wrong

## Troubleshooting

**Models not found?**
- Ensure models are committed: `git add server/models/*.pkl`
- Check `MODEL_DIR` environment variable is set correctly

**Database connection error?**
- Verify PostgreSQL service is running
- Check `DATABASE_URL` is set in environment variables

**Build fails?**
- Check build logs in Render dashboard
- Verify all dependencies in `requirements.txt`
- Ensure Python version is compatible

## Next Steps After Deployment

1. **Test your API endpoints**
2. **Set up monitoring** (Render provides basic logs)
3. **Configure custom domain** (optional)
4. **Set up automatic deployments** (already enabled on git push)

---

**Need help?** Check the full deployment guide in `DEPLOYMENT.md`

