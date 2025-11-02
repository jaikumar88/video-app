@echo off
title Video Calling Platform - Public Setup
echo.
echo ========================================
echo   Video Calling Platform Setup
echo   Exposing servers globally via ngrok
echo ========================================
echo.

echo Step 1/4: Starting Backend Server...
echo --------------------------------
start "Backend Server" cmd /k "cd /d E:\workspace\python\video-app\backend && python main.py"
echo ✓ Backend server starting on port 8000
echo.

echo Step 2/4: Starting Frontend Server...
echo ----------------------------------
start "Frontend Server" cmd /k "cd /d E:\workspace\python\video-app\frontend && npm start"
echo ✓ Frontend server starting on port 3000
echo.

echo Step 3/4: Waiting for servers to initialize...
echo --------------------------------------------
echo Please wait 30 seconds for servers to fully start...
timeout /t 30 /nobreak

echo Step 4/4: Exposing servers via public tunnels...
echo ----------------------------------------------
start "Backend Tunnel" cmd /k "cd /d E:\workspace\python\video-app && npx localtunnel --port 8000 --subdomain videoapp-backend"
echo ✓ Backend tunnel: https://videoapp-backend.loca.lt

timeout /t 5 /nobreak

start "Frontend Tunnel" cmd /k "cd /d E:\workspace\python\video-app && npx localtunnel --port 3000 --subdomain videoapp-frontend"
echo ✓ Frontend tunnel: https://videoapp-frontend.loca.lt

echo.
echo ========================================
echo   🎉 Setup Complete!
echo ========================================
echo.
echo Your video calling platform is now accessible globally:
echo.
echo 🌐 Frontend (User Interface):
echo    https://videoapp-frontend.loca.lt
echo.
echo 🔧 Backend API:
echo    https://videoapp-backend.loca.lt
echo.
echo 🔐 Admin Login:
echo    Email: admin@videoapp.com
echo    Password: admin
echo.
echo 📋 Features Available:
echo    ✓ User registration and authentication
echo    ✓ Admin panel for user management  
echo    ✓ Meeting creation and management
echo    ✓ Video/audio calling with WebRTC
echo    ✓ Screen sharing and chat
echo    ✓ Participant invitations via email
echo    ✓ Real-time communication
echo.
echo 🌍 Global Access:
echo    ✓ No localhost restrictions
echo    ✓ Share with remote participants
echo    ✓ Test from any device/network
echo    ✓ Demo to clients worldwide
echo.
echo ⚠️  Keep this window open to maintain the tunnels
echo.
pause