@echo off
echo ========================================
echo Running E2E Test Suite
echo ========================================
echo.
echo Checking prerequisites...
echo.

REM Check if backend is running
curl -s http://localhost:8000/health > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Backend is not running!
    echo Please start backend first: python main.py
    echo.
    pause
    exit /b 1
)
echo [OK] Backend is running

REM Check if ChromeDriver is available
where chromedriver > nul 2>&1
if errorlevel 1 (
    echo [WARNING] ChromeDriver not found in PATH
    echo Install with: choco install chromedriver
    echo.
)

echo.
echo Starting E2E tests...
echo.

python test_e2e_suite.py

echo.
echo ========================================
echo Test execution completed
echo ========================================
echo.
pause
