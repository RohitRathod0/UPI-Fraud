# 🔧 Troubleshooting Railway Deployment

## Error: "This site can't be reached" / DNS_PROBE_FINISHED_NXDOMAIN

This means Railway can't find your service. Let's fix it!

## Step 1: Check Railway Dashboard

1. Go to [railway.app](https://railway.app)
2. Log in to your account
3. Check if your project exists:
   - Look for project: `upi-fraud-detection-api` or similar
   - Check if service is listed

## Step 2: Check Service Status

In Railway dashboard:
- **Is the service running?** (Should show "Active" or "Running")
- **Are there any errors?** (Check "Logs" tab)
- **What's the actual URL?** (Check "Settings" → "Networking")

## Step 3: Common Issues & Solutions

### Issue 1: Service Not Deployed
**Solution:** Deploy it now!

### Issue 2: Service Stopped/Crashed
**Solution:** Check logs and restart

### Issue 3: Wrong URL
**Solution:** Get the correct URL from Railway dashboard

### Issue 4: Build Failed
**Solution:** Check build logs and fix errors

## Step 4: Redeploy (If Needed)

If service doesn't exist or failed:

1. Go to Railway dashboard
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Wait for deployment (2-5 minutes)

## Quick Fix Checklist

- [ ] Logged into Railway
- [ ] Project exists in dashboard
- [ ] Service is "Active" or "Running"
- [ ] No errors in logs
- [ ] Correct URL from Railway dashboard
- [ ] Service has been deployed successfully


