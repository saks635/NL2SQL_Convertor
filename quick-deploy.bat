@echo off
echo 🚀 DEPLOYING YOUR APP IN 30 SECONDS...
echo.

echo ⚡ STEP 1: Deploying to Railway...
railway login
railway init
railway up
echo ✅ Backend deployed to Railway!

echo.
echo ⚡ STEP 2: Next Steps:
echo 1. Your backend is now live on Railway
echo 2. Go to https://vercel.com and deploy frontend folder
echo 3. Set REACT_APP_API_URL to your Railway URL
echo.

echo 🎉 DEPLOYMENT COMPLETE!
echo Check DEPLOY.md for full instructions
echo.
pause
