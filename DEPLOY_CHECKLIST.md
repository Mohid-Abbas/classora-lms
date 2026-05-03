# 🚀 Quick Deployment Checklist

## ⚡ Fastest Way to Deploy (15 minutes)

### Step 1: Prepare Backend (5 min)

```bash
# Create required files
echo "python-3.11.0" > runtime.txt

# Create Procfile
cat > Procfile << 'EOF'
web: python manage.py migrate && python manage.py collectstatic --noinput && gunicorn classora.wsgi:application --bind 0.0.0.0:$PORT
EOF

# Add to requirements.txt
pip install gunicorn dj-database-url whitenoise psycopg2-binary
pip freeze > requirements.txt
```

### Step 2: Update Settings (5 min)

Add to `classora/settings.py`:

```python
import dj_database_url

# Production Database
if 'DATABASE_URL' in os.environ:
    DATABASES = {
        'default': dj_database_url.parse(os.environ.get('DATABASE_URL'))
    }

# Static Files
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Security
DEBUG = os.getenv('DEBUG', 'False') == 'True'
SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-key')
ALLOWED_HOSTS = ['*']  # Railway provides domain

# CORS
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
]
```

### Step 3: Push to GitHub (2 min)

```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

### Step 4: Deploy to Railway (3 min)

1. Go to https://railway.app/
2. Click "New Project" → "Deploy from GitHub"
3. Select your repo
4. Click "Add Database" → "MySQL"
5. Add Environment Variables:
   - `SECRET_KEY` = generate random string
   - `GEMINI_API_KEY` = your API key
   - `DEBUG` = False
6. Deploy automatically happens!

**Backend Live!** 🎉

---

### Step 5: Deploy Frontend to Vercel (5 min)

```bash
cd frontend

# Create vercel.json
cat > vercel.json << 'EOF'
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
EOF

# Deploy
npm install -g vercel
vercel --prod

# When asked for environment variables:
# VITE_API_URL = your-railway-url.up.railway.app
```

**Frontend Live!** 🎉

---

## 🌐 Recommended Cloud Database

### Option 1: Railway MySQL (Easiest)
- ✅ Included with Railway
- ✅ Auto-configured
- ✅ Backups included
- ✅ Cost: $0-5/month

### Option 2: PlanetScale (Serverless)
- ✅ Serverless MySQL
- ✅ Free tier: 5GB
- ✅ Git-like branching
- ✅ Cost: $0-29/month

**For your project: Use Railway MySQL (included free)**

---

## 💰 Cost Breakdown

| Service | Monthly Cost | Why |
|---------|-------------|-----|
| **Railway** (Backend) | $0-5 | Free tier sufficient |
| **Railway MySQL** | $0 | Included in free tier |
| **Vercel** (Frontend) | $0 | Free tier sufficient |
| **Domain** (Optional) | $10-15/year | Custom domain |
| **TOTAL** | **$0-5/month** | |

---

## 🔐 Environment Variables Needed

### Railway (Backend)
```
DATABASE_URL=automatically-added-by-railway
SECRET_KEY=your-random-secret-key-here
GEMINI_API_KEY=AIzaSy...
DEBUG=False
ALLOWED_HOSTS=*
```

### Vercel (Frontend)
```
VITE_API_URL=https://your-app.up.railway.app
```

---

## 📱 Access URLs After Deployment

- **Backend API:** `https://your-app.up.railway.app/api/`
- **Frontend:** `https://your-app.vercel.app`
- **Admin Panel:** `https://your-app.up.railway.app/admin/`

---

## ⚠️ Common Issues & Fixes

### Issue 1: "Module not found" error
**Fix:** Make sure `requirements.txt` includes:
```
gunicorn
dj-database-url
whitenoise
psycopg2-binary
```

### Issue 2: "Static files not found"
**Fix:** Run `python manage.py collectstatic` locally before pushing

### Issue 3: "CORS error" in browser
**Fix:** Add frontend URL to `CORS_ALLOWED_ORIGINS` in settings

### Issue 4: "Database connection failed"
**Fix:** Check `DATABASE_URL` is set in Railway variables

---

## 🎯 Summary

**Best Stack for Your LMS:**
- ✅ **Railway** - Django backend + MySQL (easiest)
- ✅ **Vercel** - React frontend (fastest)
- ✅ **Total Cost** - $0-5/month to start
- ✅ **Time to Deploy** - 15 minutes

**Why not others:**
- ❌ Heroku - No free tier anymore
- ❌ AWS - Too complex for now
- ❌ Vercel alone - Can't run Django backend

**Deploy with Railway + Vercel and you're live in 15 minutes!** 🚀
