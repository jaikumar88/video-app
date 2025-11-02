# Video App Deployment Guide

## Environment Configuration

The application uses separate environment files for local development and production:

### 🏠 Local Development
- **File**: `.env.local`
- **Backend**: `http://localhost:8000`
- **WebSocket**: `ws://localhost:8000`
- **Command**: `npm start`

### 🌐 Production (Ngrok)
- **File**: `.env.production`
- **Backend**: `https://uncurdling-joane-pantomimical.ngrok-free.dev`
- **WebSocket**: `wss://uncurdling-joane-pantomimical.ngrok-free.dev`
- **Command**: `npm run build`

## Running Locally

1. **Start Backend** (Terminal 1):
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

2. **Start Frontend** (Terminal 2):
```bash
cd frontend
npm start
```
- Automatically uses `.env.local`
- Opens at `http://localhost:3000`

## Building for Production

1. **Start Ngrok Tunnel**:
```bash
ngrok http 8000 --domain=uncurdling-joane-pantomimical.ngrok-free.dev
```

2. **Build Frontend**:
```bash
cd frontend
npm run build
```
- Automatically uses `.env.production`
- Creates optimized build in `build/` folder

## Deploying to GitHub Pages

### Option 1: Manual Deployment

1. **Build the production version**:
```bash
cd frontend
npm run build
```

2. **Push to GitHub**:
```bash
git add .
git commit -m "Deploy production build"
git push origin main
```

3. **Deploy to GitHub Pages**:
```bash
npm run deploy
```

### Option 2: Automated GitHub Actions

Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        working-directory: ./frontend
        run: npm ci
      
      - name: Build
        working-directory: ./frontend
        run: npm run build
      
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./frontend/build
```

## Environment Files Summary

| File | Git Tracked | Purpose |
|------|-------------|---------|
| `.env` | ❌ No | Base template (ignored) |
| `.env.local` | ❌ No | Local development (ignored by .gitignore) |
| `.env.production` | ✅ Yes | Production ngrok URLs (committed) |

## Testing After Deployment

### Local Test:
```bash
npm start
```
- Should connect to `http://localhost:8000`
- Open two browser windows/tabs
- Create meeting in first window
- Copy meeting link to second window

### Production Test:
```bash
npm run build
npm install -g serve
serve -s build -p 3000
```
- Should connect to `https://uncurdling-joane-pantomimical.ngrok-free.dev`
- Test with two different devices/browsers

## Troubleshooting

### WebSocket Connection Issues
- **Local**: Check backend is running on port 8000
- **Production**: Verify ngrok tunnel is active
- **CORS**: Ngrok URL must match exactly in `.env.production`

### Video/Audio Issues
1. Check browser console for media permissions
2. Verify HTTPS/WSS for production (required for media access)
3. Check STUN server connectivity in network tab

### Build Errors
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

## Current Status

✅ Environment separation configured  
✅ Local development working  
✅ Two participants can join meetings  
✅ Participants visible with names  
🔄 Video display issues (admin black screen)  
🔄 Audio transmission debugging needed
