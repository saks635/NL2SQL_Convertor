# 🚀 GET YOUR LIVE URLs IN 2 MINUTES!

## ⚡ STEP 1: Create GitHub Repo (30 seconds)

1. Go to https://github.com/new
2. Repository name: `smartdesk-nl2sql`
3. Make it **Public**
4. Click **Create repository**
5. Copy the commands GitHub shows you

## ⚡ STEP 2: Push Your Code (30 seconds)

Run these commands in your terminal:

```powershell
git remote add origin https://github.com/YOURUSERNAME/smartdesk-nl2sql.git
git branch -M main
git push -u origin main
```

## ⚡ STEP 3: Deploy Backend to Railway (1 minute)

**CLICK THIS LINK:** 
👉 https://railway.app/new/template?template=https://github.com/YOURUSERNAME/smartdesk-nl2sql

OR:
1. Go to https://railway.app
2. Sign up with GitHub
3. Click "Deploy from GitHub repo"
4. Select your `smartdesk-nl2sql` repo
5. **BOOM! Your backend is deploying!**

**Your backend URL will be:** `https://smartdesk-nl2sql-production.up.railway.app`

## ⚡ STEP 4: Deploy Frontend to Vercel (1 minute)

**CLICK THIS LINK:**
👉 https://vercel.com/new/git/external?repository-url=https://github.com/YOURUSERNAME/smartdesk-nl2sql&project-name=smartdesk-frontend&framework=create-react-app&root-directory=frontend

OR:
1. Go to https://vercel.com
2. Sign up with GitHub
3. Click "New Project"
4. Import your GitHub repo
5. Set **Root Directory** to `frontend`
6. Add environment variable:
   - `REACT_APP_API_URL` = `https://your-railway-url.railway.app`
7. **Deploy!**

**Your frontend URL will be:** `https://smartdesk-frontend.vercel.app`

---

## 🎉 ALTERNATIVE: Super Fast Free Options

### Option A: Render.com (1-click)
👉 https://render.com/deploy?repo=https://github.com/YOURUSERNAME/smartdesk-nl2sql

### Option B: Netlify (1-click frontend)
👉 https://app.netlify.com/start/deploy?repository=https://github.com/YOURUSERNAME/smartdesk-nl2sql

---

## 📱 AFTER DEPLOYMENT:

✅ **Backend URL:** `https://your-app.railway.app/api/health`
✅ **Frontend URL:** `https://your-app.vercel.app`

### Test Your App:
1. Open your frontend URL
2. Upload a SQLite database file
3. Ask: "Show me all tables"
4. Get instant results!

---

## 🔑 Don't Forget:

Add these environment variables in Railway:
- `GEMINI_API_KEY` - Get free from https://makersuite.google.com/app/apikey
- `COHERE_API_KEY` - Get free from https://cohere.ai

**TOTAL TIME: 2-3 MINUTES FOR LIVE URLS! 🚀**
