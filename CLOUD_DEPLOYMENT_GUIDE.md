# Classora LMS - Cloud Database & Deployment Guide

## 🌐 Option 1: Vercel vs Other Platforms

### **Vercel (RECOMMENDED for Frontend)**
**Best for:** React/Vue/Next.js frontend apps

**Pros:**
- ✅ Serverless - scales automatically
- ✅ Fast global CDN
- ✅ Easy GitHub integration
- ✅ Free tier generous (100GB bandwidth)
- ✅ Automatic deployments on git push
- ✅ Preview deployments for PRs

**Cons:**
- ❌ Not ideal for Django backend (serverless limitations)
- ❌ No persistent file storage
- ❌ Function execution time limits (10s hobby, 60s pro)

**Verdict:** Great for frontend, but you'll need separate backend hosting

---

### **Railway / Render / Heroku (RECOMMENDED for Full Stack)**
**Best for:** Django + React full-stack apps

#### **Railway (TOP PICK)**
**Pros:**
- ✅ Native Django support
- ✅ Easy MySQL/PostgreSQL integration
- ✅ Automatic HTTPS
- ✅ Environment variables management
- ✅ Generous free tier ($5/month credit)
- ✅ One-click deploy from GitHub
- ✅ Automatic database backups

**Pricing:**
- Free tier: $5 credit/month (enough for small app)
- Paid: ~$10-20/month for production

**Setup Time:** 10 minutes

---

#### **Render (ALTERNATIVE)**
**Pros:**
- ✅ Free tier never expires
- ✅ Native Django support
- ✅ Automatic deploys
- ✅ Custom domains

**Cons:**
- ❌ Free tier: Web service sleeps after 15 min inactivity
- ❌ Slower cold starts

**Pricing:**
- Free: $0 (with limitations)
- Paid: $7-25/month

---

#### **Heroku**
**Pros:**
- ✅ Industry standard, well documented
- ✅ Easy scaling

**Cons:**
- ❌ No free tier anymore ($7/month minimum)
- ❌ Expensive for production

**Pricing:**
- Basic: $7/month
- Production: $25-250/month

---

### **AWS / GCP / Azure (For Scale)**
**Best for:** Large-scale production with DevOps team

**Pros:**
- ✅ Full control
- ✅ Massive scalability
- ✅ Enterprise features

**Cons:**
- ❌ Complex setup
- ❌ Expensive if not managed well
- ❌ Overkill for small-medium projects

**Pricing:**
- AWS: $20-100+/month
- GCP: Similar pricing
- Azure: Similar pricing

---

## 🏆 FINAL RECOMMENDATION

### **For Your Classora LMS:**

**Option A: Railway (EASIEST - 10 min setup)**
- Best balance of ease and features
- Good free tier
- Perfect for Django + React
- Automatic database + deployment

**Option B: Render (CHEAPEST)**
- Truly free tier
- Good for development/testing
- May have cold start delays

**Option C: AWS RDS + EC2 (MOST CONTROL)**
- Use when you have 1000+ users
- Requires more setup knowledge

---

## 🚀 Deployment Walkthrough: Railway (Recommended)

### Step 1: Prepare Your Code

#### 1.1 Create `runtime.txt`
```bash
echo "python-3.11.0" > runtime.txt
```

#### 1.2 Create `Procfile`
```
web: gunicorn classora.wsgi:application --bind 0.0.0.0:$PORT
```

#### 1.3 Update `requirements.txt`
Add these if not present:
```
gunicorn==21.2.0
dj-database-url==2.1.0
psycopg2-binary==2.9.9  # For PostgreSQL (Railway default)
whitenoise==6.6.0  # For static files
```

#### 1.4 Update `settings.py` for Production

```python
# Add at top
import dj_database_url

# Database configuration for Railway
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL'),
        conn_max_age=600
    )
}

# Static files (WhiteNoise)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Security
DEBUG = os.getenv('DEBUG', 'False') == 'True'
SECRET_KEY = os.getenv('SECRET_KEY')
ALLOWED_HOSTS = ['*']  # Railway provides its own domain

# CORS for production
CORS_ALLOWED_ORIGINS = [
    "https://your-frontend.vercel.app",  # Add your frontend URL
    "http://localhost:5173",  # For local development
]
```

#### 1.5 Create `railway.json` (Optional)
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python manage.py migrate && python manage.py collectstatic --noinput && gunicorn classora.wsgi:application",
    "healthcheckPath": "/api/lms/ai/status/",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

---

### Step 2: Push to GitHub

```bash
# Initialize git (if not done)
git init
git add .
git commit -m "Ready for Railway deployment"

# Create GitHub repository and push
git remote add origin https://github.com/YOUR_USERNAME/classora-lms.git
git branch -M main
git push -u origin main
```

---

### Step 3: Deploy to Railway

#### 3.1 Sign Up
- Go to https://railway.app/
- Sign up with GitHub

#### 3.2 Create New Project
1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose your `classora-lms` repository

#### 3.3 Add MySQL Database
1. Click "New" → "Database" → "Add MySQL"
2. Railway automatically creates database
3. Connection string auto-added to environment

#### 3.4 Configure Environment Variables
In Railway Dashboard → Your Project → Variables:

```
DATABASE_URL=${{MySQL.MYSQL_URL}}  # Auto-generated
SECRET_KEY=your-very-secret-key-here
DEBUG=False
GEMINI_API_KEY=your-gemini-api-key
ALLOWED_HOSTS=${{RAILWAY_STATIC_URL}}
CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app
```

#### 3.5 Deploy
1. Railway automatically deploys on git push
2. Monitor logs in Railway dashboard
3. Visit the provided URL

**Your backend is now live!** 🎉

---

## 🚀 Deploy Frontend to Vercel

### Step 1: Prepare Frontend

#### Update API Base URL
In `frontend/src/api/client.js`:

```javascript
const BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export const apiClient = axios.create({
  baseURL: `${BASE_URL}/api/`,
  headers: {
    'Content-Type': 'application/json',
  },
});
```

#### Create `vercel.json`
```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

---

### Step 2: Push Frontend to GitHub (Separate Repo or Subfolder)

Option A: Separate repository for frontend
```bash
cd frontend
git init
git add .
git commit -m "Initial frontend commit"
git remote add origin https://github.com/YOUR_USERNAME/classora-lms-frontend.git
git push -u origin main
```

Option B: Use GitHub Actions to deploy frontend folder

---

### Step 3: Deploy to Vercel

1. Go to https://vercel.com/
2. Sign up with GitHub
3. Click "Add New Project"
4. Import your frontend repository
5. Configure:
   - **Framework Preset:** Vite
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
   - **Environment Variables:**
     - `VITE_API_URL=https://your-railway-app.up.railway.app`

6. Click Deploy

**Your frontend is now live!** 🎉

---

## 📊 Cloud Database Options

### Option 1: Railway MySQL (EASIEST)
- ✅ Included with Railway deployment
- ✅ Automatic backups
- ✅ Scales automatically
- ✅ $0 (uses free tier credit)

### Option 2: PlanetScale (SERVERLESS MYSQL)
**Best for:** Serverless applications

**Pros:**
- ✅ Serverless MySQL (scales to zero)
- ✅ Free tier: 5GB storage, 1 billion rows
- ✅ Branching (like Git for databases)
- ✅ Deploy requests (like PRs for schema)

**Setup:**
1. Sign up: https://planetscale.com/
2. Create database
3. Get connection string
4. Add to environment variables

### Option 3: AWS RDS (MOST CONTROL)
**For:** Production with DevOps team

**Pricing:**
- db.t3.micro: ~$13/month
- Storage: $0.115/GB/month

**Setup:**
1. Create RDS MySQL instance
2. Configure security groups
3. Get endpoint URL
4. Update DATABASE_URL

### Option 4: Google Cloud SQL
**For:** GCP-based infrastructure

**Pricing:**
- db-f1-micro: ~$7/month
- Storage: $0.19/GB/month

---

## 🔐 Security Checklist for Production

### Environment Variables
```bash
# Required
SECRET_KEY=complex-random-string-here
DATABASE_URL=mysql://user:pass@host:port/db
GEMINI_API_KEY=your-api-key
DEBUG=False

# Optional but recommended
AWS_ACCESS_KEY_ID=your-key      # If using S3 for media
AWS_SECRET_ACCESS_KEY=your-secret
SENTRY_DSN=your-sentry-url       # Error tracking
```

### Django Security Settings
```python
# settings.py
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'
```

---

## 💰 Cost Comparison (Monthly Estimates)

### Development/Small (< 100 users)
| Service | Cost | Notes |
|---------|------|-------|
| Railway | $0-5 | Free tier sufficient |
| Render | $0 | Free tier, sleeps after 15min |
| Vercel | $0 | Free tier sufficient |
| PlanetScale | $0 | Free tier sufficient |
| **Total** | **$0-5** | |

### Production/Medium (100-1000 users)
| Service | Cost | Notes |
|---------|------|-------|
| Railway | $10-20 | Pro plan |
| Render | $7-25 | Starter plan |
| Vercel | $0-20 | Pro if needed |
| AWS RDS | $15-30 | db.t3.small |
| **Total** | **$20-75** | |

### Scale/Large (1000+ users)
| Service | Cost | Notes |
|---------|------|-------|
| AWS/GCP | $100-500+ | Multiple instances |
| RDS | $50-200 | db.t3.medium+ |
| Load Balancer | $20-50 | |
| **Total** | **$200-1000+** | |

---

## 📱 Quick Start Commands

### Deploy to Railway (10 minutes)
```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Link project
railway link

# 4. Add database
railway add --database mysql

# 5. Add environment variables
railway variables set SECRET_KEY=your-key GEMINI_API_KEY=your-key

# 6. Deploy
railway up

# 7. Open in browser
railway open
```

### Deploy Frontend to Vercel (5 minutes)
```bash
# 1. Install Vercel CLI
npm install -g vercel

# 2. Deploy
cd frontend
vercel --prod

# 3. Set environment variable
vercel env add VITE_API_URL
# Enter your Railway backend URL
```

---

## 🎯 My Recommendation for You

### **Phase 1: Development (Now)**
- **Backend:** Railway ($0-5/month)
- **Database:** Railway MySQL (included)
- **Frontend:** Vercel ($0/month)
- **Total:** $0-5/month

### **Phase 2: Production (When you have users)**
- **Backend:** Railway Pro ($10-20/month)
- **Database:** PlanetScale or Railway MySQL
- **Frontend:** Vercel Pro ($20/month) if needed
- **Total:** $20-50/month

### **Phase 3: Scale (1000+ users)**
- **Backend:** AWS/GCP with auto-scaling
- **Database:** AWS RDS or Cloud SQL
- **CDN:** CloudFlare or AWS CloudFront
- **Total:** $200+/month

---

## 📞 Support & Resources

### Railway
- Docs: https://docs.railway.app/
- Discord: https://discord.gg/railway
- Status: https://status.railway.app/

### Vercel
- Docs: https://vercel.com/docs
- Discord: https://vercel.com/discord

### PlanetScale
- Docs: https://planetscale.com/docs

### Django Deployment
- Docs: https://docs.djangoproject.com/en/stable/howto/deployment/

---

## 🚀 Summary

**Easiest Path:**
1. ✅ Railway for Django backend + MySQL
2. ✅ Vercel for React frontend
3. ✅ Both have generous free tiers
4. ✅ Automatic deployments from GitHub
5. ✅ SSL, domains, scaling included

**Time to Deploy:** 15-30 minutes  
**Cost to Start:** $0-5/month  
**Scaling:** Automatic or one-click

**Start with Railway + Vercel - they're perfect for your LMS!** 🎉
