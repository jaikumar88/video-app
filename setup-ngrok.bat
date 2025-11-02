@echo off
title Video Calling Platform - ngrok Setup
echo.
echo ========================================
echo   Video Calling Platform - ngrok Setup
echo   Single URL for both Frontend & Backend
echo ========================================
echo.

echo Step 1/3: Starting Backend Server...
echo --------------------------------
start "Backend Server" cmd /k "cd /d E:\workspace\python\video-app\backend && python main.py"
echo ✓ Backend server starting on port 8000
echo.

echo Step 2/3: Waiting for server to initialize...
echo ------------------------------------------
echo Please wait 20 seconds for server to fully start...
timeout /t 20 /nobreak

echo Step 3/3: Starting ngrok tunnel...
echo --------------------------------
echo Opening ngrok tunnel for unified access...
start "ngrok Tunnel" cmd /k "cd /d E:\workspace\python\video-app\backend && ngrok.exe http 8000"

echo.
echo ========================================
echo   🎉 Setup Complete!
echo ========================================
echo.
echo Your video calling platform will be available at:
echo.
echo 🌐 **Check the ngrok terminal window for your public URL**
echo    Format: https://[random-subdomain].ngrok-free.dev
echo.
echo 🔐 Admin Login:
echo    Email: admin@videoapp.com
echo    Password: admin
echo.
echo 📋 Features Available:
echo    ✓ Complete web application (frontend + backend)
echo    ✓ User registration and authentication
echo    ✓ Admin panel for user management  
echo    ✓ Meeting creation and management
echo    ✓ Video/audio calling with WebRTC
echo    ✓ Screen sharing and chat
echo    ✓ Participant invitations via email
echo    ✓ Real-time communication
echo.
echo 🌍 Global Access Benefits:
echo    ✓ Single URL for everything
echo    ✓ No localhost restrictions
echo    ✓ Share with remote participants
echo    ✓ Works on any device/network
echo    ✓ Professional deployment setup
echo.
echo ⚠️  Keep the ngrok window open to maintain the tunnel
echo.
echo 📱 Once ngrok starts, copy the https URL and share it!
echo.
pause