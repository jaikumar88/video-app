#!/bin/bash

# Local Development Setup Script
# This script sets up the development environment for the WorldClass Video app

echo "🎥 Setting up WorldClass Video Calling Platform - Local Development"
echo "=================================================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker Desktop first."
    echo "   Download from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose found"

# Create environment file if it doesn't exist
if [ ! -f "backend/.env" ]; then
    echo "📝 Creating backend environment file..."
    cp backend/.env.example backend/.env
    echo "✅ Created backend/.env from template"
    echo "📝 Please review and update backend/.env with your configuration"
fi

# Create frontend environment file if it doesn't exist
if [ ! -f "frontend/.env" ]; then
    echo "📝 Creating frontend environment file..."
    cat > frontend/.env << EOL
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
REACT_APP_ENVIRONMENT=local
EOL
    echo "✅ Created frontend/.env"
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p backend/uploads
mkdir -p backend/recordings
mkdir -p backend/data
echo "✅ Created directories"

# Build and start services
echo "🐳 Building and starting Docker services..."
docker-compose -f docker-compose.local.yml up --build -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are running
echo "🔍 Checking service status..."
docker-compose -f docker-compose.local.yml ps

# Test backend health
echo "🏥 Testing backend health..."
if curl -f http://localhost:8000/health &> /dev/null; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
fi

# Test frontend
echo "🌐 Testing frontend..."
if curl -f http://localhost:3000 &> /dev/null; then
    echo "✅ Frontend is accessible"
else
    echo "❌ Frontend is not accessible"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📱 Access the application:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Documentation: http://localhost:8000/docs"
echo ""
echo "🔧 Useful commands:"
echo "   View logs: docker-compose -f docker-compose.local.yml logs -f"
echo "   Stop services: docker-compose -f docker-compose.local.yml down"
echo "   Restart services: docker-compose -f docker-compose.local.yml restart"
echo ""
echo "📚 Next steps:"
echo "   1. Review and update backend/.env with your email/SMS credentials"
echo "   2. Visit http://localhost:3000 to start using the app"
echo "   3. Check the documentation in the docs/ folder"