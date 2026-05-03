# 🆓 FREE Deployment Action Plan - Start Now!

## 🎯 Goal: $0/month forever with GitHub auto-deploy

---

## ⚡ QUICK START (30 minutes)

### Step 1: Setup PlanetScale Database (10 min) ✅ FREE FOREVER

```bash
# 1. Sign up at https://planetscale.com/ (use GitHub)
# 2. Click "Create Database"
#    - Name: classora-lms
#    - Region: Pick closest to you
# 3. Click "Connect" → "Django"
# 4. Copy the DATABASE_URL (starts with mysql://)
# 5. Save it somewhere - you'll need it!
```

**Result:** Cloud MySQL database, $0 forever, 5GB storage

---

### Step 2: Prepare Code for Production (5 min)

Run these commands in your project:

```bash
# 1. Create runtime file
echo "python-3.11.0" > runtime.txt

# 2. Create Procfile for Render
cat > Procfile << 'EOF'
web: python manage.py migrate && python manage.py collectstatic --noinput && gunicorn classora.wsgi:application
EOF

# 3. Update requirements
pip install gunicorn dj-database-url whitenoise PyMySQL
pip freeze > requirements.txt

# 4. Create production settings
cat > classora/settings_production.py << 'EOF'
from .settings import *
import dj_database_url

DEBUG = False
ALLOWED_HOSTS = ['.onrender.com', '.vercel.app', 'localhost']

# PlanetScale Database
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL'),
        conn_max_age=600,
        ssl_require=True
    )
}

# Static files
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# CORS - will update with actual URLs after deploy
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
]

# Security
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Use production settings
DJANGO_SETTINGS_MODULE = 'classora.settings_production'
EOF

# 5. Add PyMySQL to handle PlanetScale
# Create/append to classora/__init__.py
cat >> classora/__init__.py << 'EOF'
import pymysql
pymysql.install_as_MySQLdb()
EOF

# 6. Commit changes
git add .
git commit -m "Ready for free cloud deployment"
git push origin main
```

---

### Step 3: Deploy Backend to Render (10 min) ✅ FREE FOREVER

1. **Go to https://render.com/**
2. Sign up with GitHub (FREE)
3. Click "New +" → "Web Service"
4. Connect your `classora-lms` GitHub repo
5. Fill the form:

| Field | Value |
|-------|-------|
| **Name** | classora-lms |
| **Region** | Oregon (US West) or closest |
| **Branch** | main |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate` |
| **Start Command** | `gunicorn classora.wsgi:application` |
| **Plan** | Free |

6. Click "Advanced" → Add Environment Variables:

```
DATABASE_URL=mysql://xxxxxxxxx@xxxx.psdb.cloud/classora?ssl_ca=/etc/ssl/cert.pem
SECRET_KEY=copy-from-your-env-file-or-generate-new
GEMINI_API_KEY=AIzaSyYourKeyHere
DEBUG=False
DJANGO_SETTINGS_MODULE=classora.settings_production
WEB_CONCURRENCY=2
```

7. Click "Create Web Service"
8. Wait 2-5 minutes for deployment
9. **Your API is live!** 🎉

**URL:** `https://classora-lms.onrender.com`

---

### Step 4: Deploy Frontend to Vercel (5 min) ✅ FREE FOREVER

```bash
# 1. Go to frontend folder
cd frontend

# 2. Create vercel config
cat > vercel.json << 'EOF'
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
EOF

# 3. Update API URL in your frontend
# Edit: frontend/src/api/client.js or wherever you set the API URL
# Change from 'http://127.0.0.1:8000' to 'https://classora-lms.onrender.com'

# 4. Deploy to Vercel
npm install -g vercel
vercel login
vercel --prod

# When prompted:
# - Set up and deploy? Yes
# - Which scope? (your username)
# - Link to existing project? No
# - Project name? classora-lms-frontend
```

5. **Set environment variable:**
```bash
vercel env add VITE_API_URL
# Enter: https://classora-lms.onrender.com
```

**Your frontend is live!** 🎉

**URL:** `https://classora-lms-frontend.vercel.app`

---

### Step 5: Keep Render Awake (FREE) - 2 min

**Problem:** Render sleeps after 15 min of inactivity (cold start = 30 sec delay)

**Solution:** UptimeRobot (FREE forever)

1. Go to https://uptimerobot.com/
2. Sign up (FREE)
3. Click "Add New Monitor"
4. Configure:
   - **Monitor Type:** HTTP(s)
   - **Friendly Name:** Classora LMS Keepalive
   - **URL:** `https://classora-lms.onrender.com/api/lms/ai/status/`
   - **Monitoring Interval:** Every 5 minutes (FREE tier)
5. Click "Create Monitor"

**Result:** Your app stays awake 24/7 for FREE! ✅

---

## ✅ DONE! What You Have Now

### 🌐 Live URLs:
- **Frontend:** `https://classora-lms-frontend.vercel.app`
- **Backend API:** `https://classora-lms.onrender.com/api/`
- **Admin Panel:** `https://classora-lms.onrender.com/admin/`

### 💰 Monthly Cost: **$0 FOREVER**

### 🔄 Auto-Updates:
Every time you push to GitHub:
```bash
git add .
git commit -m "New feature"
git push origin main
```
→ Render auto-deploys (2-3 min)
→ Vercel auto-deploys (30 sec)
→ Site updated automatically!

---

## 📋 Summary of Services Used

| Service | Purpose | Cost | Limit | Solution |
|---------|---------|------|-------|----------|
| **PlanetScale** | MySQL Database | $0 | 5GB | Archive old data |
| **Render** | Django Backend | $0 | Sleeps 15min | UptimeRobot keeps awake |
| **Vercel** | React Frontend | $0 | 100GB | Sufficient for most |
| **UptimeRobot** | Keepalive pings | $0 | 50 monitors | More than enough |
| **GitHub** | Code + Auto-deploy | $0 | Unlimited | Free forever |
| **TOTAL** | | **$0** | | |

---

## 🚀 How to Update Your System Over Time

### Make a Change:
```bash
# 1. Edit code locally
# 2. Test locally
python manage.py runserver

# 3. Commit and push
git add .
git commit -m "Added new AI feature"
git push origin main

# 4. DONE! Auto-deployment happens automatically:
#    - Render: Deploys in 2-3 minutes
#    - Vercel: Deploys in 30 seconds
#    - Live site updated!
```

### Database Changes:
```bash
# If you modify models:
python manage.py makemigrations
python manage.py migrate

# Commit and push - migrations run automatically on Render
git add .
git commit -m "Added new model field"
git push origin main
```

---

## 🎯 Your System Can Handle:

### With FREE tier:
- ✅ 100-500 concurrent users
- ✅ 5GB database (thousands of records)
- ✅ 100GB/month bandwidth
- ✅ 24/7 uptime (with UptimeRobot)

### When you grow beyond free:
**Upgrade path:**
- Render: $7/month (no sleep, more RAM)
- PlanetScale: $29/month (more storage)
- Vercel: $20/month (more bandwidth)
- **Total: $56/month** for serious production

---

## ⚡ Quick Commands Reference

### Deploy Backend Only:
```bash
# Push code
git push origin main
# Render auto-deploys in 2-3 minutes
```

### Deploy Frontend Only:
```bash
cd frontend
vercel --prod
```

### View Logs:
- **Render:** Dashboard → Service → Logs
- **Vercel:** Dashboard → Project → Functions

### Database Console:
- **PlanetScale:** Dashboard → Console (run SQL directly)

### Environment Variables:
- **Render:** Dashboard → Service → Environment
- **Vercel:** Dashboard → Project → Settings → Environment Variables

---

## 🆘 Troubleshooting

### Issue: "Database connection error"
**Fix:** 
1. Check DATABASE_URL in Render env vars
2. Make sure it includes `?ssl_ca=/etc/ssl/cert.pem`
3. Redeploy

### Issue: "CORS error" in browser
**Fix:**
1. Add your Vercel URL to CORS_ALLOWED_ORIGINS in settings
2. Redeploy

### Issue: "Static files not loading"
**Fix:**
```bash
# Run locally first to collect
python manage.py collectstatic --noinput

# Commit staticfiles folder OR ensure it's in .gitignore
# Render runs collectstatic during build
```

### Issue: "Cold starts taking too long"
**Fix:**
1. Check UptimeRobot is set up correctly
2. Verify URL in UptimeRobot matches your Render URL
3. Check interval is set to 5 minutes

---

## 🎉 YOU'RE DONE!

**What you achieved:**
- ✅ $0/month hosting forever
- ✅ GitHub auto-deployment
- ✅ Production-ready setup
- ✅ Database never sleeps (PlanetScale)
- ✅ Backend wakes quickly (UptimeRobot)
- ✅ Easy updates (git push)
- ✅ Professional quality hosting

**Time invested:** ~30 minutes
**Monthly cost:** $0 forever
**Maintenance:** Just `git push` for updates!

**Your LMS is now LIVE and FREE!** 🚀🎊
