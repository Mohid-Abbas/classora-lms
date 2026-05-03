# 🆓 COMPLETELY FREE Deployment Guide - $0 Forever

## 💰 $0/Month Stack (Truly Free Forever)

| Component | Service | Cost | Limitations |
|-----------|---------|------|-------------|
| **Backend** | Render | $0 | Sleeps after 15 min idle |
| **Database** | PlanetScale | $0 | 5GB storage, 1B rows |
| **Frontend** | Vercel | $0 | 100GB bandwidth |
| **Media Storage** | Cloudinary | $0 | 25GB storage |
| **TOTAL** | | **$0/month** | **Forever Free** |

---

## 🎯 Best Free Options Comparison

### Backend Hosting (Choose ONE)

#### 1. **Render** ⭐ RECOMMENDED
**Cost:** $0 forever
**Limits:** 
- Sleeps after 15 min inactivity (cold start ~30 seconds)
- 512 MB RAM
- 0.1 CPU cores
- 750 hours/month

**Pros:**
- ✅ Truly free forever
- ✅ Native Django support
- ✅ Automatic HTTPS
- ✅ GitHub auto-deploy
- ✅ Custom domains

**Cons:**
- ❌ Cold starts after sleep
- ❌ Limited resources

**Best for:** Development, demos, small user base (< 100 daily users)

---

#### 2. **PythonAnywhere**
**Cost:** $0 forever
**Limits:**
- 1 daily scheduled task
- 100 seconds CPU/day
- 500 MB disk
- MySQL included

**Pros:**
- ✅ Django-optimized
- ✅ MySQL included
- ✅ No cold starts
- ✅ SSH access

**Cons:**
- ❌ Limited CPU time
- ❌ Daily restarts required
- ❌ Limited bandwidth

**Best for:** Personal projects, learning

---

#### 3. **Oracle Cloud Always Free**
**Cost:** $0 forever (not a trial!)
**Limits:**
- 2 AMD-based Compute VMs (1/8 OCPU, 1GB RAM each)
- 2 Block Volumes (200GB total)
- 10 TB outbound data/month

**Pros:**
- ✅ Truly unlimited time
- ✅ Full control
- ✅ No sleep/cold starts
- ✅ Can run 24/7
- ✅ Generous resources

**Cons:**
- ❌ Complex setup
- ❌ Requires DevOps knowledge
- ❌ Must manually configure everything

**Best for:** Production, learning cloud/DevOps

---

#### 4. **Google App Engine**
**Cost:** $0 (28 instance hours/day)
**Limits:**
- 28 frontend instance hours/day
- 9 backend instance hours/day
- 1GB egress/day
- Cloud SQL not included (use separate DB)

**Pros:**
- ✅ Google infrastructure
- ✅ Automatic scaling
- ✅ No server management

**Cons:**
- ❌ Daily limits
- ❌ Complex configuration
- ❌ No persistent MySQL (must use Cloud SQL paid or Firestore)

---

### Database (Choose ONE)

#### 1. **PlanetScale** ⭐ RECOMMENDED
**Cost:** $0 forever
**Limits:**
- 5GB storage
- 1 billion rows
- 1 database
- 1 production branch

**Pros:**
- ✅ Serverless MySQL (compatible with Django)
- ✅ Git-like branching
- ✅ Deploy requests
- ✅ Auto-scaling
- ✅ No connection limits

**Cons:**
- ❌ No foreign keys (in free tier)
- ❌ Single production branch

**Workaround:** Foreign keys can be enforced in application layer

---

#### 2. **Neon**
**Cost:** $0 forever
**Limits:**
- 500 MB storage
- 3 projects
- 100 compute hours/month

**Pros:**
- ✅ Serverless PostgreSQL
- ✅ Branching
- ✅ Good for small projects

**Cons:**
- ❌ Very limited storage (500MB)

---

#### 3. **Supabase**
**Cost:** $0 forever
**Limits:**
- 500 MB database
- 2GB file storage
- 50,000 users
- 500K real-time messages

**Pros:**
- ✅ PostgreSQL + extras
- ✅ Auth included
- ✅ Real-time subscriptions

**Cons:**
- ❌ Limited storage
- ❌ Limited bandwidth

---

#### 4. **Render PostgreSQL** (if using Render hosting)
**Cost:** $0 forever
**Limits:**
- 90-day expiration (can be renewed)
- 1GB storage

**Pros:**
- ✅ Easy integration
- ✅ No setup

**Cons:**
- ❌ 90-day limit (must manually renew)

---

### Frontend (Vercel - UNBEATABLE)
**Cost:** $0 forever
**Limits:**
- 100GB bandwidth/month
- 6,000 build minutes/month
- 100 deployments/day

**Best part:** No meaningful limits for most projects!

---

## 🏆 RECOMMENDED FREE STACK

### **For $0/month Forever:**

```
┌─────────────────────────────────────────┐
│  Frontend: Vercel ($0)                 │
│  - React app                            │
│  - Auto-deploy from GitHub              │
│  - 100GB bandwidth                      │
└────────────────┬────────────────────────┘
                 │ API calls
                 ▼
┌─────────────────────────────────────────┐
│  Backend: Render ($0)                    │
│  - Django + Gunicorn                    │
│  - Sleeps after 15 min                  │
│  - Wakes on first request (~30s)        │
└────────────────┬────────────────────────┘
                 │ Database queries
                 ▼
┌─────────────────────────────────────────┐
│  Database: PlanetScale ($0)              │
│  - Serverless MySQL                     │
│  - 5GB storage                          │
│  - 1B rows                              │
│  - No sleep, always on                  │
└─────────────────────────────────────────┘
```

**Total Cost: $0/month forever**

---

## 🚀 Step-by-Step: Deploy for FREE

### Step 1: Prepare Your Code for Render

Create `render.yaml` in project root:

```yaml
services:
  - type: web
    name: classora-lms
    runtime: python
    buildCommand: |
      pip install -r requirements.txt
      python manage.py collectstatic --noinput
      python manage.py migrate
    startCommand: gunicorn classora.wsgi:application
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: DATABASE_URL
        fromDatabase:
          name: classora-db
          property: connectionString
      - key: SECRET_KEY
        generateValue: true
      - key: WEB_CONCURRENCY
        value: 2

databases:
  - name: classora-db
    databaseName: classora
    user: classora
```

---

### Step 2: Use PlanetScale Instead of Render DB (Better!)

Why PlanetScale over Render's free PostgreSQL?
- ✅ PlanetScale never expires (Render's DB expires in 90 days)
- ✅ More storage (5GB vs 1GB)
- ✅ MySQL (what you already use)

#### Setup PlanetScale:

1. Go to https://planetscale.com/
2. Sign up with GitHub (free forever)
3. Create database:
   - Name: `classora-lms`
   - Region: Pick closest to your users
4. Get connection string:
   - Go to database → "Connect"
   - Select "Django"
   - Copy the `DATABASE_URL`

5. Update Django settings:

```python
# settings.py
import dj_database_url

# PlanetScale database
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL'),
        conn_max_age=600,
        ssl_require=True  # Important for PlanetScale
    )
}
```

6. Install driver:
```bash
pip install mysqlclient dj-database-url
# OR for better compatibility:
pip install PyMySQL dj-database-url
```

If using PyMySQL, add to `__init__.py`:
```python
import pymysql
pymysql.install_as_MySQLdb()
```

---

### Step 3: Update requirements.txt

Add these for production:

```
# Core
django>=5.0,<6.0
djangorestframework>=3.14.0
djangorestframework-simplejwt>=5.3.0
django-cors-headers>=4.3.0
python-dotenv>=1.0.0

# Production
gunicorn>=21.2.0
dj-database-url>=2.1.0
whitenoise>=6.6.0
PyMySQL>=1.1.0  # For PlanetScale compatibility

# AI
google-generativeai>=0.8.0
```

---

### Step 4: Create Production Settings

Create `classora/settings_production.py`:

```python
from .settings import *
import dj_database_url

# Production overrides
DEBUG = False
ALLOWED_HOSTS = ['.onrender.com', 'your-custom-domain.com']

# Database - PlanetScale
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

# Security
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# CORS - Update with your Vercel URL
CORS_ALLOWED_ORIGINS = [
    "https://your-app.vercel.app",
    "https://your-app-git-main-yourname.vercel.app",  # Preview deploys
]

# Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
```

---

### Step 5: Deploy to Render (Free Tier)

1. **Push to GitHub:**
```bash
git add .
git commit -m "Production deployment ready"
git push origin main
```

2. **Create Render Account:**
   - Go to https://render.com/
   - Sign up with GitHub

3. **New Web Service:**
   - Click "New +" → "Web Service"
   - Connect your GitHub repo
   - Select branch: `main`

4. **Configure:**
   - **Name:** `classora-lms`
   - **Runtime:** Python 3
   - **Build Command:**
     ```bash
     pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
     ```
   - **Start Command:**
     ```bash
     gunicorn classora.wsgi:application
     ```
   - **Plan:** Free ($0)

5. **Environment Variables:**
   Click "Advanced" and add:
   ```
   DATABASE_URL=mysql://username:password@host.region.psdb.cloud/database?ssl_ca=/etc/ssl/cert.pem
   SECRET_KEY=your-random-secret-key-here-min-50-chars
   GEMINI_API_KEY=AIzaSy...
   DEBUG=False
   DJANGO_SETTINGS_MODULE=classora.settings_production
   ```

6. **Deploy:**
   - Click "Create Web Service"
   - Wait for build (2-5 minutes)
   - Your API is live!

**URL:** `https://classora-lms.onrender.com`

---

### Step 6: Deploy Frontend to Vercel

1. **Prepare frontend:**
```bash
cd frontend

# Create vercel.json
cat > vercel.json << 'EOF'
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
EOF

# Update API URL in src/api/client.js
# Change from localhost to Render URL
```

2. **Deploy:**
```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
vercel --prod

# When asked:
# ? Set up and deploy? [Y/n] Y
# ? Which scope? [your-username]
# ? Link to existing project? [n]
# ? What's your project name? [classora-lms-frontend]
```

3. **Set Environment Variable:**
```bash
vercel env add VITE_API_URL
# Enter: https://classora-lms.onrender.com
```

**Frontend Live!** 🎉

---

## 🔧 Keeping Render Awake (Avoid Cold Starts)

### Problem:
Render free tier sleeps after 15 min inactivity. First request takes 30+ seconds.

### Solutions:

#### Option 1: Cron Job (UptimeRobot) - FREE
Use UptimeRobot to ping your API every 10 minutes:

1. Go to https://uptimerobot.com/
2. Create free account
3. Add new monitor:
   - Type: HTTP(s)
   - URL: `https://classora-lms.onrender.com/api/lms/ai/status/`
   - Interval: Every 5 minutes (free tier allows this)
4. Your app stays awake!

**Cost:** $0

---

#### Option 2: GitHub Actions (FREE)
Create `.github/workflows/keepalive.yml`:

```yaml
name: Keep Render Alive

on:
  schedule:
    - cron: '*/10 * * * *'  # Every 10 minutes
  workflow_dispatch:

jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Ping Render
        run: |
          curl -s https://classora-lms.onrender.com/api/lms/ai/status/ > /dev/null
          echo "Pinged at $(date)"
```

**Note:** GitHub Actions free tier: 2000 minutes/month = ~66 minutes/day
Every 10 minutes = 144 pings/day × 5 seconds = 720 seconds = 12 minutes/day ✅

---

#### Option 3: Accept Cold Starts
For development/demo purposes, cold starts are fine.
For production with users, use Option 1 or 2.

---

## 📊 Storage for Media Files (Images, Uploads)

### Problem:
Render free tier doesn't persist files between deploys.

### Solution: Cloudinary (FREE)

**Cost:** $0 forever (25GB storage)

#### Setup:

1. Sign up: https://cloudinary.com/
2. Get credentials from dashboard
3. Install:
```bash
pip install cloudinary django-cloudinary-storage
```

4. Update settings:
```python
INSTALLED_APPS = [
    # ... existing apps
    'cloudinary',
    'cloudinary_storage',
]

# Cloudinary settings
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.getenv('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.getenv('CLOUDINARY_API_KEY'),
    'API_SECRET': os.getenv('CLOUDINARY_API_SECRET'),
}

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
MEDIA_URL = '/media/'
```

5. Environment variables:
```
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

---

## 🔄 System Updates Over Time

### GitHub-Based Workflow (FREE)

Your deployment will auto-update on every git push!

```
Developer → Git Push → GitHub → Auto Deploy → Live
```

#### Setup:

**Render:** Already auto-deploys on push to main

**Vercel:** Already auto-deploys on push to main

**PlanetScale:** Schema changes via deploy requests

#### Update Process:

1. **Code changes locally:**
```bash
# Make changes
git add .
git commit -m "New feature: AI flashcards"
git push origin main
```

2. **Auto-deployment:**
   - Render: Auto-deploys (2-3 min)
   - Vercel: Auto-deploys (30 sec)
   - Preview URLs created for testing

3. **Database migrations:**
   - Render runs `migrate` in build command
   - Or run manually:
   ```bash
   render shell
   python manage.py migrate
   ```

4. **Rollback if needed:**
   - Git revert: `git revert HEAD`
   - Render keeps last deploys
   - PlanetScale has branches for schema changes

---

## 📋 Complete Cost Breakdown

### Monthly Cost: $0

| Service | Tier | Cost | What You Get |
|---------|------|------|--------------|
| **Render** | Free | $0 | 512MB RAM, sleeps after 15min |
| **PlanetScale** | Free | $0 | 5GB MySQL, never sleeps |
| **Vercel** | Hobby | $0 | 100GB bandwidth |
| **Cloudinary** | Free | $0 | 25GB storage |
| **UptimeRobot** | Free | $0 | 50 monitors, 5min checks |
| **GitHub** | Free | $0 | Unlimited repos, Actions |
| **TOTAL** | | **$0** | |

---

## ⚠️ Limitations & Workarounds

### Limitation 1: Cold Starts on Render
**Workaround:** UptimeRobot keeps it awake (FREE)

### Limitation 2: No Foreign Keys in PlanetScale Free
**Workaround:** 
- Enforce in Django models
- Use `on_delete=models.CASCADE` in Django
- Validate in serializers

### Limitation 3: 5GB Database Limit
**Workaround:**
- Archive old data periodically
- Compress large text fields
- Delete old submissions/attempts after semester

### Limitation 4: 15min Sleep on Render
**Workaround:**
- Accept for dev/staging
- Use UptimeRobot for production
- Or upgrade to $7/month paid tier (no sleep)

---

## 🚀 Production Checklist

Before going live:

- [ ] Set strong SECRET_KEY
- [ ] Configure CORS with actual frontend URL
- [ ] Set DEBUG=False
- [ ] Add Cloudinary for media files
- [ ] Set up UptimeRobot for keepalive
- [ ] Test all AI endpoints
- [ ] Verify database migrations work
- [ ] Check static files serving
- [ ] Test user registration/login
- [ ] Verify email notifications (if any)

---

## 🎯 Summary

### **Your FREE Stack:**
- ✅ **Render** - Django backend ($0, sleeps after 15min)
- ✅ **PlanetScale** - MySQL database ($0, 5GB, never sleeps)
- ✅ **Vercel** - React frontend ($0, 100GB bandwidth)
- ✅ **Cloudinary** - File storage ($0, 25GB)
- ✅ **UptimeRobot** - Keepalive pings ($0)

### **Total: $0/month forever**

### **To avoid cold starts:**
Add UptimeRobot (free) to ping every 5 minutes

### **To update system:**
Just `git push` - auto-deploy happens!

### **When you outgrow free tier:**
- Render: $7/month (no sleep, more RAM)
- PlanetScale: $29/month (more storage, branches)
- Vercel: $20/month (more bandwidth, team features)

**This setup can handle 100-500 users easily for FREE!** 🎉
