#!/bin/bash

echo "🚀 Deploying Video Platform to GitHub Pages..."
echo ""

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "📁 Initializing Git repository..."
    git init
    echo ""
fi

# Check if remote exists
if ! git remote get-url origin > /dev/null 2>&1; then
    echo "⚠️  No 'origin' remote found."
    echo "Please create a GitHub repository and add it as origin:"
    echo "git remote add origin https://github.com/YOUR_USERNAME/video-app.git"
    echo ""
    exit 1
fi

# Add and commit all changes
echo "📝 Adding and committing changes..."
git add .
git commit -m "Deploy: Frontend for GitHub Pages with ngrok backend"

# Push to main branch
echo "📤 Pushing to GitHub..."
git push origin main

# Deploy frontend to GitHub Pages
echo "🌐 Building and deploying frontend..."
cd frontend
npm run build
npm run deploy

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🔗 Frontend will be available at:"
echo "   https://YOUR_USERNAME.github.io/video-app"
echo ""
echo "🔧 Make sure your backend is running with ngrok:"
echo "   cd backend && python main.py"
echo "   cd backend && .\ngrok.exe http 8000"
echo ""
echo "📊 Check deployment status:"
echo "   GitHub Actions: https://github.com/YOUR_USERNAME/video-app/actions"
echo "   GitHub Pages: Repository Settings > Pages"