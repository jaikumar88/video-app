@echo off
echo Starting Video Call Platform with Global Access...
echo.
echo IMPORTANT: This setup serves BOTH frontend and backend from port 8000
echo - No need to run frontend separately on port 3000
echo - Everything (React app + API) is served from one unified server
echo.

REM Start the unified backend server (serves both frontend and API)
echo [1/3] Starting unified server on port 8000 (Frontend + Backend)...
start "Unified Server" cmd /k "cd /d E:\workspace\python\video-app\backend && python main.py"

REM Wait for backend to start
timeout /t 5 /nobreak > nul

REM Start localtunnel
echo [2/3] Starting localtunnel to expose server globally...
start "LocalTunnel" cmd /k "cd /d E:\workspace\python\video-app && npx localtunnel --port 8000"

REM Wait for tunnel to establish
timeout /t 3 /nobreak > nul

echo [3/3] Setup complete!
echo.
echo Your video platform is now accessible globally via the tunnel URL.
echo Check the LocalTunnel window for the public URL (something like: https://xyz.loca.lt)
echo.
echo UNIFIED DEPLOYMENT - One server for everything:
echo - Local access: http://localhost:8000 (Frontend + API)
echo - Global access: [Check LocalTunnel window for URL]
echo - API endpoints: /api/v1/* (automatically handled)
echo - WebSocket: /ws (automatically handled)
echo.
echo DO NOT start frontend separately - it's already included!
echo.
echo To stop everything, close both windows that opened.
echo.
pause