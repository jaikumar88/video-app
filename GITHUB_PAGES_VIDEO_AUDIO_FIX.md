# How to Fix Audio/Video on GitHub Pages Deployed App

## The Problem
GitHub Pages (static hosting) cannot run your Python backend. Your video/audio needs:
- WebRTC signaling server (backend)
- WebSocket for real-time communication (backend)
- Meeting management APIs (backend)

## Current Setup (Temporary Solution)
✅ Frontend: GitHub Pages (https://jaikumar88.github.io/video-app-frontend)
✅ Backend: Your local machine via ngrok (https://uncurdling-joane-pantomimical.ngrok-free.dev)

## Why Video/Audio Doesn't Work Sometimes

### Issue #1: Ngrok Tunnel Not Running
**Symptom**: App loads but can't connect to backend
**Fix**: Keep ngrok running:
```bash
cd backend
ngrok http 8000 --log=stdout
```

### Issue #2: Backend Not Running
**Symptom**: 502 Bad Gateway or connection errors
**Fix**: Keep backend running:
```bash
cd backend
python main.py
```

### Issue #3: Ngrok URL Changed
**Symptom**: App shows old ngrok URL in errors
**Fix**: Free ngrok changes URL on restart. Either:
- Use same domain with ngrok paid plan
- Update .env.production and redeploy when ngrok URL changes

### Issue #4: CORS/HTTPS Issues
**Symptom**: Browser blocks requests
**Fix**: Backend already has CORS configured for GitHub Pages domain

## Quick Test Right Now

1. **Check if backend is running:**
```bash
curl https://uncurdling-joane-pantomimical.ngrok-free.dev/health
```

2. **Check if GitHub Pages app can connect:**
- Open: https://jaikumar88.github.io/video-app-frontend
- Open browser console (F12)
- Look for API connection errors

3. **Test video/audio:**
- Register/Login on GitHub Pages app
- Create a meeting
- Join meeting
- Enable camera/microphone when browser prompts

## Permanent Solutions

### Option 1: Deploy Backend to Cloud (RECOMMENDED)
Deploy your backend to always-on cloud hosting:

**Free Options:**
- **Railway** (https://railway.app) - 500 hours/month free
- **Render** (https://render.com) - Free tier available
- **Fly.io** (https://fly.io) - Free tier available
- **PythonAnywhere** - Free tier with limitations

**Paid Options:**
- **AWS EC2** - $5-10/month
- **DigitalOcean** - $6/month
- **Azure App Service** - Pay as you go
- **Google Cloud Run** - Pay per use

### Option 2: Use ngrok Static Domain (Paid)
- **ngrok Pro**: $10/month for static domain
- URL never changes
- No need to redeploy frontend

### Option 3: Run 24/7 on Your Computer
- Keep your computer on 24/7
- Keep backend + ngrok running
- Not recommended (power, internet issues)

## Steps to Deploy Backend to Railway (FREE)

1. **Sign up**: https://railway.app (use GitHub account)

2. **Create New Project** → Deploy from GitHub

3. **Add Environment Variables:**
```env
DATABASE_URL=sqlite:///./app.db
SECRET_KEY=your-secret-key
ALLOWED_ORIGINS=https://jaikumar88.github.io
```

4. **Railway gives you a URL** like: `https://your-app.railway.app`

5. **Update frontend .env.production:**
```env
REACT_APP_API_URL=https://your-app.railway.app/api/v1
REACT_APP_WS_URL=wss://your-app.railway.app/ws
```

6. **Redeploy frontend:**
```bash
npm run deploy
```

## Current Status Check

Run this to verify everything is working:
```bash
# Backend health
curl https://uncurdling-joane-pantomimical.ngrok-free.dev/health

# Should return: {"status": "healthy"}
```

If this returns healthy, your audio/video SHOULD work on:
https://jaikumar88.github.io/video-app-frontend

## Troubleshooting Steps

1. **Open GitHub Pages app**: https://jaikumar88.github.io/video-app-frontend
2. **Open Browser Console** (F12)
3. **Look for errors**:
   - "Failed to fetch" = Backend not reachable
   - "CORS" = CORS issue (backend config)
   - "401" = Authentication issue
   - "Mixed content" = HTTP/HTTPS mismatch

4. **Check Network Tab**:
   - See if API calls to ngrok URL are succeeding
   - Check WebSocket connection status

## Why Your Current Setup Should Work

✅ Backend is running (localhost:8000)
✅ Ngrok tunnel is active (uncurdling-joane-pantomimical.ngrok-free.dev)
✅ Frontend .env.production points to ngrok URL
✅ Frontend is deployed to GitHub Pages

**The audio/video SHOULD be working right now!**

## Test It Now

1. Go to: https://jaikumar88.github.io/video-app-frontend
2. Register/Login
3. Create meeting
4. Join meeting
5. Allow camera/microphone permissions when browser asks
6. Video/audio should work!

If it doesn't work, check browser console for specific error messages.
