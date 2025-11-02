# Video Calling Platform - GitHub Pages Deployment

## Architecture Overview

**Frontend**: Deployed on GitHub Pages (Static hosting)
**Backend**: Running locally via ngrok tunnel

This setup gives you:
- ✅ Permanent frontend URL on GitHub Pages
- ✅ Backend running on your local machine via ngrok
- ✅ Global access for participants
- ✅ Automatic frontend deployments via GitHub Actions

## Current URLs

**Frontend (GitHub Pages)**: `https://YOUR_GITHUB_USERNAME.github.io/video-app`
**Backend (ngrok)**: `https://uncurdling-joane-pantomimical.ngrok-free.dev`

## Setup Instructions

### 1. Create GitHub Repository

```bash
# Navigate to your project
cd E:\workspace\python\video-app

# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: Video calling platform"

# Create repository on GitHub.com with name "video-app"
# Then add remote
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/video-app.git

# Push to GitHub
git push -u origin main
```

### 2. Configure GitHub Pages

1. Go to your repository on GitHub.com
2. Click **Settings** tab
3. Scroll to **Pages** section
4. Source: Select **GitHub Actions**
5. The workflow will automatically deploy on push

### 3. Update Frontend Configuration

Edit `frontend/package.json` and replace `YOUR_GITHUB_USERNAME` with your actual GitHub username:

```json
"homepage": "https://YOUR_ACTUAL_USERNAME.github.io/video-app"
```

### 4. Keep Backend Running

Make sure your backend is always running with ngrok:

```bash
# Terminal 1: Start backend
cd backend
python main.py

# Terminal 2: Start ngrok
cd backend  
.\ngrok.exe http 8000
```

## Manual Deployment (Alternative)

If you prefer manual deployment:

```bash
cd frontend

# Build for production
npm run build

# Deploy to GitHub Pages
npm run deploy
```

## Updating ngrok URL

If your ngrok URL changes, update these files:

1. `frontend/.env.production`
2. `.github/workflows/deploy-frontend.yml` (environment variables)

Then commit and push to trigger redeployment.

## Environment Variables

**Development** (`.env`):
```
REACT_APP_API_URL=/api/v1
REACT_APP_WS_URL=/ws
```

**Production** (`.env.production`):
```
REACT_APP_API_URL=https://uncurdling-joane-pantomimical.ngrok-free.dev/api/v1
REACT_APP_WS_URL=wss://uncurdling-joane-pantomimical.ngrok-free.dev/ws
```

## How It Works

1. **Frontend**: Static React app hosted on GitHub Pages
2. **API Calls**: Frontend makes requests to ngrok URL
3. **WebSocket**: Real-time connections via ngrok WebSocket URL
4. **CORS**: Backend allows GitHub Pages origin
5. **Deployment**: Automatic via GitHub Actions on push

## Benefits

- ✅ Frontend is always available (GitHub Pages uptime)
- ✅ Backend runs on your machine (full control)
- ✅ Easy to update frontend (git push)
- ✅ No hosting costs for frontend
- ✅ Participants get reliable frontend access

## Sharing with Users

**Primary URL**: `https://YOUR_GITHUB_USERNAME.github.io/video-app`

Users will:
1. Access the GitHub Pages frontend
2. Frontend connects to your ngrok backend
3. Get full video calling functionality

## Troubleshooting

### Frontend shows connection errors:
- Check if ngrok is running
- Verify ngrok URL in `.env.production`
- Check CORS settings in backend

### GitHub Pages not updating:
- Check GitHub Actions tab for build status
- Verify workflow permissions in repository settings
- Ensure main branch is being pushed to

### ngrok URL changes:
- Update environment files
- Commit and push to redeploy frontend
- Restart ngrok with: `.\ngrok.exe http 8000`