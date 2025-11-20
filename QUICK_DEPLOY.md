# ⚡ Quick Deployment Guide - Railway

## 🚀 3-Step Deployment

### Step 1: Push to GitHub
```bash
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

### Step 2: Deploy on Railway
1. Go to [railway.app](https://railway.app)
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select your repository
4. Railway auto-detects and starts deploying!

### Step 3: Add Database
1. In Railway project, click **"+ New"**
2. Select **"Database"** → **"Add PostgreSQL"**
3. Done! Database is automatically linked

## ⚙️ Environment Variables

Go to your service → **Variables** tab, add:

```
MODEL_DIR=./server/models
HITL_ENABLED=true
LOG_LEVEL=INFO
```

## ✅ Test Your Deployment

Once deployed, test with:
```bash
curl https://your-app-name.up.railway.app/health
```

## 💡 Tips

- **Free tier**: $5 credit/month (no card needed initially)
- **Auto-deploy**: Pushes to main branch auto-deploy
- **Logs**: View in Railway dashboard
- **Database**: PostgreSQL is automatically linked

**That's it!** Your API is live! 🎉



