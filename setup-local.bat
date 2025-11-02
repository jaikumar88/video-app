@echo off
REM Local Development Setup Script for Windows
REM This script sets up the development environment for the WorldClass Video app

echo 🎥 Setting up WorldClass Video Calling Platform - Local Development
echo ==================================================================

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed. Please install Docker Desktop first.
    echo    Download from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose is not installed. Please install Docker Compose first.
    pause
    exit /b 1
)

echo ✅ Docker and Docker Compose found

REM Create environment file if it doesn't exist
if not exist "backend\.env" (
    echo 📝 Creating backend environment file...
    copy "backend\.env.example" "backend\.env"
    echo ✅ Created backend\.env from template
    echo 📝 Please review and update backend\.env with your configuration
)

REM Create frontend environment file if it doesn't exist
if not exist "frontend\.env" (
    echo 📝 Creating frontend environment file...
    echo REACT_APP_API_URL=http://localhost:8000 > frontend\.env
    echo REACT_APP_WS_URL=ws://localhost:8000 >> frontend\.env
    echo REACT_APP_ENVIRONMENT=local >> frontend\.env
    echo ✅ Created frontend\.env
)

REM Create necessary directories
echo 📁 Creating necessary directories...
if not exist "backend\uploads" mkdir "backend\uploads"
if not exist "backend\recordings" mkdir "backend\recordings"
if not exist "backend\data" mkdir "backend\data"
echo ✅ Created directories

REM Build and start services
echo 🐳 Building and starting Docker services...
docker-compose -f docker-compose.local.yml up --build -d

REM Wait for services to start
echo ⏳ Waiting for services to start...
timeout /t 10 /nobreak > nul

REM Check if services are running
echo 🔍 Checking service status...
docker-compose -f docker-compose.local.yml ps

REM Test backend health
echo 🏥 Testing backend health...
curl -f http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo ❌ Backend health check failed
) else (
    echo ✅ Backend is healthy
)

echo.
echo 🎉 Setup complete!
echo.
echo 📱 Access the application:
echo    Frontend: http://localhost:3000
echo    Backend API: http://localhost:8000
echo    API Documentation: http://localhost:8000/docs
echo.
echo 🔧 Useful commands:
echo    View logs: docker-compose -f docker-compose.local.yml logs -f
echo    Stop services: docker-compose -f docker-compose.local.yml down
echo    Restart services: docker-compose -f docker-compose.local.yml restart
echo.
echo 📚 Next steps:
echo    1. Review and update backend\.env with your email/SMS credentials
echo    2. Visit http://localhost:3000 to start using the app
echo    3. Check the documentation in the docs\ folder

pause