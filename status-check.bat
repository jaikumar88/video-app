@echo off
title Video Calling Platform - Status Check
echo.
echo ==========================================
echo   Video Calling Platform Status Check
echo ==========================================
echo.

echo [1] Testing Local Backend (port 8000)...
curl -s http://localhost:8000/health 2>nul
if %errorlevel%==0 (
    echo ✅ Backend: RUNNING
) else (
    echo ❌ Backend: NOT RUNNING
)

echo.
echo [2] Testing Global Tunnel...
curl -s https://videoapp-global.loca.lt/health 2>nul
if %errorlevel%==0 (
    echo ✅ Global Tunnel: WORKING
    echo 🌍 Share this URL with participants: https://videoapp-global.loca.lt
) else (
    echo ❌ Global Tunnel: NOT AVAILABLE
    echo ⚠️  Need to restart tunnel
)

echo.
echo [3] Service Summary:
echo - Backend serves both frontend and API on port 8000
echo - Tunnel exposes everything globally
echo - Participants use: https://videoapp-global.loca.lt
echo.

echo Checking Frontend Accessibility...
echo ---------------------------------
curl -s -I https://videoapp-frontend.loca.lt | findstr "HTTP"
echo.

echo ==========================================
echo   Status Check Complete
echo ==========================================
echo.
echo If all checks passed, your platform is ready!
echo.
echo 🌐 Access your platform at:
echo    https://videoapp-frontend.loca.lt
echo.
echo 🔐 Login with:
echo    Email: admin@videoapp.com
echo    Password: admin
echo.
pause