@echo off
echo Setting up public URLs for Video App servers...
echo.

echo Starting backend tunnel (port 8000)...
start "Backend Tunnel" ssh -R 80:localhost:8000 serveo.net

echo.
echo Waiting 5 seconds...
timeout /t 5 /nobreak > nul

echo Starting frontend tunnel (port 3000)...
start "Frontend Tunnel" ssh -R 80:localhost:3000 serveo.net

echo.
echo Public URLs will be displayed in the new terminal windows.
echo Press any key to exit...
pause > nul