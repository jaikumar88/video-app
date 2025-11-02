@echo off
echo ========================================
echo E2E Test Suite Setup
echo ========================================
echo.
echo Installing test dependencies...
pip install -r requirements-test.txt
echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Install ChromeDriver: choco install chromedriver
echo 2. Start backend: python main.py
echo 3. Start frontend: npm start (in frontend folder)
echo 4. Run tests: python test_e2e_suite.py
echo.
pause
