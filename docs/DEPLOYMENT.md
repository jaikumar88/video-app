# 🚀 Deployment Guide

This guide covers deploying the WorldClass Video Calling Platform in both local development and production cloud environments.

## 📋 Prerequisites

### Local Development
- Docker Desktop 4.0+
- Docker Compose 2.0+
- 8GB RAM minimum
- 20GB free disk space

### Production Deployment
- Cloud provider account (AWS/GCP/Azure)
- Domain name with SSL certificate
- Email service (Gmail/SendGrid)
- SMS service (Twilio)
- 16GB RAM minimum per server
- Load balancer
- CDN for static content

## 🏠 Local Development Setup

### Quick Start (Windows)

```cmd
# Clone the repository
git clone <your-repo-url>
cd video-app

# Run the setup script
setup-local.bat
```

### Quick Start (Linux/Mac)

```bash
# Clone the repository
git clone <your-repo-url>
cd video-app

# Make setup script executable
chmod +x setup-local.sh

# Run the setup script
./setup-local.sh
```

### Manual Setup

1. **Environment Configuration**
   ```bash
   # Copy environment files
   cp backend/.env.example backend/.env
   cp .env.production.example .env.production
   
   # Edit backend/.env with your settings
   nano backend/.env
   ```

2. **Start Services**
   ```bash
   # Build and start all services
   docker-compose -f docker-compose.local.yml up --build -d
   
   # View logs
   docker-compose -f docker-compose.local.yml logs -f
   ```

3. **Access Application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Redis: localhost:6379

### Local Configuration Options

| Service | Port | Purpose |
|---------|------|---------|
| Frontend | 3000 | React development server |
| Backend | 8000 | FastAPI application |
| PostgreSQL | 5432 | Database (production mode) |
| Redis | 6379 | Caching and sessions |
| TURN Server | 3478 | WebRTC connectivity |

## ☁️ Production Deployment

### Architecture Overview

```
Internet
    ↓
Load Balancer (AWS ALB/GCP LB/Azure LB)
    ↓
├── Frontend (React SPA)
├── Backend API (FastAPI)
├── WebRTC SFU (MediaSoup)
└── WebSocket (Socket.IO)
    ↓
├── PostgreSQL Database
├── Redis Cache
├── File Storage (S3/GCS/Blob)
└── Monitoring (Prometheus/Grafana)
```

### 1. Cloud Infrastructure Setup

#### AWS Deployment

```bash
# Create VPC and subnets
aws ec2 create-vpc --cidr-block 10.0.0.0/16

# Create security groups
aws ec2 create-security-group \
  --group-name videoapp-sg \
  --description "WorldClass Video App Security Group"

# Launch EC2 instances
aws ec2 run-instances \
  --image-id ami-12345678 \
  --count 2 \
  --instance-type t3.large \
  --security-group-ids sg-12345678
```

#### Google Cloud Deployment

```bash
# Create GKE cluster
gcloud container clusters create videoapp-cluster \
  --num-nodes=3 \
  --machine-type=e2-standard-4 \
  --zone=us-central1-a

# Deploy using Kubernetes
kubectl apply -f k8s/
```

#### Azure Deployment

```bash
# Create resource group
az group create --name videoapp-rg --location eastus

# Create AKS cluster
az aks create \
  --resource-group videoapp-rg \
  --name videoapp-aks \
  --node-count 3 \
  --node-vm-size Standard_D4s_v3
```

### 2. Database Setup

#### PostgreSQL Configuration

```sql
-- Create database and user
CREATE DATABASE videoapp_db;
CREATE USER videoapp_user WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE videoapp_db TO videoapp_user;

-- Optimize for video conferencing
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '1GB';
ALTER SYSTEM SET effective_cache_size = '3GB';
SELECT pg_reload_conf();
```

#### Redis Configuration

```redis
# redis.conf optimizations
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

### 3. Environment Configuration

Create production environment files:

```bash
# Production environment
ENVIRONMENT=production
DATABASE_URL=postgresql+asyncpg://user:pass@prod-db:5432/videoapp
REDIS_URL=redis://:password@prod-redis:6379/0

# Security
SECRET_KEY=your-ultra-secure-secret-key-here
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# External services
SMTP_SERVER=smtp.sendgrid.net
TWILIO_ACCOUNT_SID=your_twilio_sid
```

### 4. Deploy with Docker Compose

```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# Scale services
docker-compose -f docker-compose.prod.yml up -d --scale backend=3
```

### 5. Deploy with Kubernetes

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: videoapp

---
# k8s/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: videoapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: your-registry/videoapp-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
```

Deploy to Kubernetes:

```bash
kubectl apply -f k8s/
```

## 🔧 Configuration

### Backend Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `ENVIRONMENT` | Deployment environment | `production` |
| `DATABASE_URL` | PostgreSQL connection | `postgresql+asyncpg://...` |
| `SECRET_KEY` | JWT signing key | `ultra-secure-key` |
| `CORS_ORIGINS` | Allowed origins | `https://yourdomain.com` |
| `MAX_PARTICIPANTS_PER_MEETING` | Meeting capacity | `1000` |

### Frontend Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `REACT_APP_API_URL` | Backend API URL | `https://api.yourdomain.com` |
| `REACT_APP_WS_URL` | WebSocket URL | `wss://api.yourdomain.com` |
| `REACT_APP_ENVIRONMENT` | Environment | `production` |

### WebRTC Configuration

```javascript
// STUN/TURN server configuration
const rtcConfiguration = {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
    {
      urls: 'turn:your-turn-server.com:3478',
      username: 'your-username',
      credential: 'your-password'
    }
  ]
};
```

## 📊 Scaling for 1 Billion Users

### Architecture Patterns

1. **Horizontal Scaling**
   - Microservices architecture
   - Auto-scaling groups
   - Load balancing

2. **Database Sharding**
   - User-based sharding
   - Geographic sharding
   - Meeting-based partitioning

3. **CDN and Edge Computing**
   - Global CDN for static content
   - Edge servers for WebRTC
   - Regional data centers

4. **Caching Strategy**
   - Redis for sessions
   - Application-level caching
   - Database query caching

### Performance Optimizations

```yaml
# Auto-scaling configuration
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 10
  maxReplicas: 1000
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Database Scaling

```sql
-- Partitioning strategy for meetings table
CREATE TABLE meetings_2024_q1 PARTITION OF meetings
FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');

CREATE TABLE meetings_2024_q2 PARTITION OF meetings
FOR VALUES FROM ('2024-04-01') TO ('2024-07-01');

-- Indexes for performance
CREATE INDEX CONCURRENTLY idx_meetings_host_date 
ON meetings (host_user_id, scheduled_start_time);

CREATE INDEX CONCURRENTLY idx_participants_meeting_status
ON meeting_participants (meeting_id, status) 
WHERE status = 'joined';
```

## 🔒 Security

### SSL/TLS Configuration

```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /ws/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Firewall Rules

```bash
# AWS Security Group rules
aws ec2 authorize-security-group-ingress \
  --group-id sg-12345678 \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-id sg-12345678 \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0
```

## 📈 Monitoring

### Health Checks

```bash
# Backend health check
curl -f https://api.yourdomain.com/health

# Database health check
pg_isready -h your-db-host -p 5432

# Redis health check
redis-cli -h your-redis-host ping
```

### Metrics Collection

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'videoapp-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

## 🚨 Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```bash
   # Check what's using the port
   netstat -tulpn | grep :8000
   
   # Kill process using the port
   sudo kill -9 $(lsof -t -i:8000)
   ```

2. **Database Connection Issues**
   ```bash
   # Test database connection
   psql "postgresql://user:pass@localhost:5432/videoapp_db"
   
   # Check database logs
   docker logs videoapp-postgres
   ```

3. **WebRTC Connection Problems**
   ```javascript
   // Check STUN/TURN server connectivity
   const pc = new RTCPeerConnection({
     iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
   });
   ```

### Performance Issues

1. **High Memory Usage**
   ```bash
   # Monitor container memory
   docker stats videoapp-backend
   
   # Analyze memory usage
   docker exec videoapp-backend cat /proc/meminfo
   ```

2. **Slow Database Queries**
   ```sql
   -- Enable query logging
   ALTER SYSTEM SET log_statement = 'all';
   SELECT pg_reload_conf();
   
   -- Analyze slow queries
   SELECT query, calls, total_time, mean_time 
   FROM pg_stat_statements 
   ORDER BY mean_time DESC 
   LIMIT 10;
   ```

## 🔄 Updates and Maintenance

### Rolling Updates

```bash
# Zero-downtime deployment
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d --no-deps backend
```

### Database Migrations

```bash
# Run database migrations
docker exec videoapp-backend alembic upgrade head

# Create new migration
docker exec videoapp-backend alembic revision --autogenerate -m "Add new feature"
```

### Backup Strategy

```bash
# Database backup
pg_dump "postgresql://user:pass@host:5432/videoapp_db" | gzip > backup_$(date +%Y%m%d).sql.gz

# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump $DATABASE_URL | aws s3 cp - s3://your-backup-bucket/db_backup_$DATE.sql

# Redis backup
redis-cli --rdb dump.rdb
aws s3 cp dump.rdb s3://your-backup-bucket/redis_backup_$DATE.rdb
```

## 📞 Support

For deployment issues:
1. Check the logs: `docker-compose logs -f`
2. Verify configuration: Review `.env` files
3. Test connectivity: Use health check endpoints
4. Check resources: Monitor CPU, memory, and disk usage
5. Contact support: Create an issue in the repository

---

**Need help?** Check our [FAQ](FAQ.md) or create an issue in the repository.