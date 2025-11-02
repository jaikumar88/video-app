@echo off
echo 🚀 Deploying Video Platform to GitHub Pages...
echo.

REM Check if we're in a git repository
if not exist ".git" (
    echo 📁 Initializing Git repository...
    git init
    echo.
)

REM Add and commit all changes
echo 📝 Adding and committing changes...
echo    📋 .gitignore will protect sensitive files
echo    🔒 Environment files, databases, and secrets excluded
echo    📦 Only source code and configs will be committed
git add .
git commit -m "Deploy: Frontend for GitHub Pages with ngrok backend"

REM Check if remote exists and push
echo 📤 Pushing to GitHub...
git remote get-url origin >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  No 'origin' remote found.
    echo Please create a GitHub repository and add it as origin:
    echo git remote add origin https://github.com/YOUR_USERNAME/video-app.git
    echo.
    pause
    exit /b 1
)

git push origin main

REM Deploy frontend to GitHub Pages
echo 🌐 Building and deploying frontend...
cd frontend
npm run deploy

echo.
echo ✅ Deployment complete!
echo.
echo 🔗 Frontend will be available at:
echo    https://YOUR_USERNAME.github.io/video-app
echo.
echo 🔧 Make sure your backend is running with ngrok:
echo    cd backend ^&^& python main.py
echo    cd backend ^&^& .\ngrok.exe http 8000
echo.
echo 📊 Check deployment status:
echo    GitHub Actions: https://github.com/YOUR_USERNAME/video-app/actions
echo    GitHub Pages: Repository Settings ^> Pages
echo.
pause