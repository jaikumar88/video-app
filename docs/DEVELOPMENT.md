# WorldClass Video Calling Platform - Development Guide

## 🚀 Complete Setup & Development Instructions

### Prerequisites
- **Node.js 18+** and npm/yarn
- **Python 3.11+** and pip
- **Docker & Docker Compose**
- **Git**

### 📁 Project Structure Overview
```
video-app/
├── backend/                 # FastAPI Python backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Configuration & database
│   │   ├── models/         # Database models
│   │   └── services/       # Business logic services
│   ├── main.py            # Application entry point
│   └── requirements.txt   # Python dependencies
├── frontend/              # React TypeScript frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── services/      # API & WebRTC services
│   │   ├── store/         # Redux store
│   │   └── pages/         # Route pages
│   └── package.json      # Node.js dependencies
├── docker/               # Docker configurations
└── docs/                # Documentation
```

## 🛠 Development Setup (Local Mode)

### 1. Clone and Navigate
```bash
cd e:\workspace\python\video-app
```

### 2. Backend Setup
```bash
# Navigate to backend
cd backend

# Create Python virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Create environment file
copy .env.example .env

# Initialize database (SQLite for local)
python -c "
from app.core.database import create_tables
import asyncio
asyncio.run(create_tables())
"

# Start backend server
python main.py
# Server runs at: http://localhost:8000
```

### 3. Frontend Setup
```bash
# Open new terminal
cd frontend

# Install Node.js dependencies
npm install
# or
yarn install

# Create environment file
copy .env.example .env.local

# Start development server
npm start
# or
yarn start
# Frontend runs at: http://localhost:3000
```

### 4. Docker Setup (Alternative)
```bash
# From project root
docker-compose -f docker-compose.local.yml up --build

# Services available at:
# - Frontend: http://localhost:3000
# - Backend: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

## 🎯 Key Features Implemented

### ✅ Backend (FastAPI)
- **Authentication System**: Email/phone registration with JWT tokens
- **Meeting Management**: Create, join, leave, end meetings
- **User Profiles**: Profile management and settings
- **WebSocket Signaling**: Real-time WebRTC communication
- **Database Models**: SQLite (local) / PostgreSQL (production)
- **API Documentation**: Auto-generated Swagger docs

### ✅ Frontend (React + TypeScript)
- **Authentication Pages**: Login, register, verify email/phone
- **Dashboard**: Meeting overview and management
- **Meeting Room**: Video calling interface with WebRTC
- **Real-time Communication**: WebSocket integration
- **Responsive Design**: Material-UI components
- **State Management**: Redux Toolkit

### ✅ Video Calling Features
- **WebRTC Integration**: Peer-to-peer video/audio
- **Screen Sharing**: Share desktop/application screen
- **Meeting Controls**: Mute/unmute, video on/off
- **Participant Management**: Join, leave, participant list
- **Real-time Messaging**: WebSocket-based signaling

## 🔧 Environment Configuration

### Backend Environment Variables (.env)
```bash
# Application
ENVIRONMENT=local
SECRET_KEY=your-super-secret-key-here
DEBUG=true

# Database
DATABASE_URL=sqlite:///./app.db

# CORS
CORS_ORIGINS=["http://localhost:3000"]

# Email (SMTP)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# SMS (Twilio)
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=your-twilio-number

# JWT
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### Frontend Environment Variables (.env.local)
```bash
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_WS_URL=ws://localhost:8000
REACT_APP_APP_NAME=WorldClass Video Platform
```

## 🔄 Development Workflow

### Running the Application
1. **Backend First**:
   ```bash
   cd backend
   venv\Scripts\activate
   python main.py
   ```

2. **Frontend Second**:
   ```bash
   cd frontend
   npm start
   ```

3. **Access Application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Making Code Changes
- **Backend**: FastAPI auto-reloads on file changes
- **Frontend**: React dev server hot-reloads automatically
- **Database**: SQLite file persists data between restarts

## 🧪 Testing Video Calling

### Local Testing Steps
1. **Register Two Users**:
   - Open http://localhost:3000 in two different browsers
   - Register with different email addresses
   - Verify accounts (check console logs for verification codes)

2. **Create Meeting**:
   - Login as first user
   - Create a new meeting from dashboard
   - Copy meeting ID or URL

3. **Join Meeting**:
   - Login as second user
   - Join meeting using ID/URL
   - Grant camera/microphone permissions

4. **Test Features**:
   - Video/audio toggle
   - Screen sharing
   - Participant list
   - Leave/end meeting

## 📚 API Endpoints

### Authentication
- `POST /auth/register` - Register with email/phone
- `POST /auth/login` - Login user
- `POST /auth/verify-email` - Verify email code
- `POST /auth/verify-phone` - Verify SMS code
- `POST /auth/refresh` - Refresh JWT token

### Meetings
- `POST /meetings` - Create meeting
- `GET /meetings` - List user's meetings
- `GET /meetings/{id}` - Get meeting details
- `POST /meetings/{id}/join` - Join meeting
- `POST /meetings/{id}/leave` - Leave meeting
- `POST /meetings/{id}/end` - End meeting

### Users
- `GET /users/profile` - Get user profile
- `PUT /users/profile` - Update profile
- `GET /users/settings/meeting` - Get meeting settings
- `PUT /users/settings/meeting` - Update meeting settings

### WebSocket
- `WS /ws/{meeting_id}?token={jwt}` - Real-time signaling

## 🏗 Architecture Design

### Scalability for 1 Billion Users

#### Infrastructure
- **Load Balancers**: NGINX/HAProxy for request distribution
- **Auto-scaling**: Kubernetes pods based on CPU/memory
- **Database Sharding**: Horizontal partitioning by region
- **CDN**: Static content delivery optimization
- **Caching**: Redis for sessions and frequent data

#### WebRTC Architecture
- **STUN/TURN Servers**: For NAT traversal
- **SFU (Selective Forwarding Unit)**: For multi-party calls
- **Media Servers**: Distributed across regions
- **Recording Services**: Separate microservice for recordings

#### Deployment Strategy
- **Microservices**: Independent scaling of components
- **Container Orchestration**: Kubernetes clusters
- **Multi-region**: Geographic distribution
- **Database Replication**: Master-slave configuration
- **Message Queues**: For async processing

## 🐛 Common Issues & Solutions

### Backend Issues
1. **Database Connection**: Ensure SQLite file permissions
2. **CORS Errors**: Check CORS_ORIGINS in .env
3. **Import Errors**: Activate virtual environment
4. **Port Conflicts**: Change port in main.py if 8000 is busy

### Frontend Issues
1. **Module Not Found**: Run `npm install`
2. **API Connection**: Verify backend is running
3. **WebSocket Errors**: Check WebSocket URL format
4. **TypeScript Errors**: Install missing type definitions

### WebRTC Issues
1. **Camera/Mic Permission**: Grant browser permissions
2. **Connection Failed**: Check STUN server configuration
3. **No Video/Audio**: Verify media constraints
4. **Signaling Errors**: Check WebSocket connection

## 📈 Performance Monitoring

### Metrics to Track
- **Connection Times**: WebRTC setup duration
- **Video Quality**: Resolution, FPS, bitrate
- **Network Stats**: Packet loss, latency, jitter
- **Server Resources**: CPU, memory, bandwidth
- **User Experience**: Join success rate, call quality

### Logging
- **Backend**: Python logging to files/console
- **Frontend**: Browser console and error tracking
- **WebRTC**: Connection statistics and quality metrics
- **Infrastructure**: Server metrics and alerts

## 🚀 Production Deployment

### Docker Production Build
```bash
# Build and deploy
docker-compose -f docker-compose.prod.yml up --build -d

# Scale services
docker-compose -f docker-compose.prod.yml up --scale backend=3 -d
```

### Environment Setup
1. **PostgreSQL Database**: Replace SQLite
2. **Redis Cache**: For sessions and real-time data
3. **NGINX**: Reverse proxy and load balancer
4. **SSL Certificates**: HTTPS/WSS encryption
5. **TURN Servers**: For enterprise NAT traversal

### Monitoring & Alerts
- **Health Checks**: Automated service monitoring
- **Error Tracking**: Centralized error collection
- **Performance Metrics**: Application and infrastructure
- **User Analytics**: Usage patterns and behavior

This development guide provides everything needed to run and develop the WorldClass Video Calling Platform locally and understand the architecture for production scaling.