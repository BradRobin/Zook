# Production Deployment Guide

Complete guide for deploying Zook to production with HTTPS encryption using Cloudflare Tunnel.

## Overview

This guide covers deploying Zook with:
- **HTTPS encryption** via Cloudflare Tunnel (free SSL)
- **Production-hardened FastAPI** backend
- **PostgreSQL** with SSL
- **Automated deployment** via Docker Compose
- **Security best practices**

## Prerequisites

Before starting, ensure you have:

- [x] Linux server (VPS, dedicated, or on-premises)
- [x] Domain name (can register through Cloudflare or any registrar)
- [x] Cloudflare account (free tier sufficient)
- [x] SSH access to server
- [x] 2GB+ RAM, 10GB+ disk space
- [x] Docker & Docker Compose installed (or Python 3.11+)

## Deployment Options

Choose your deployment method:

### Option A: Docker Compose (Recommended)
- Easiest setup
- Isolated environment
- Easy scaling
- [Jump to Docker Deployment](#docker-deployment)

### Option B: Direct Installation
- More control
- Lower resource usage
- Manual dependency management
- [Jump to Direct Deployment](#direct-deployment)

---

## Docker Deployment

### Step 1: Prepare Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose -y

# Verify installation
docker --version
docker-compose --version
```

### Step 2: Clone Repository

```bash
# Clone your Zook repository
git clone https://github.com/yourusername/zook.git
cd zook
```

### Step 3: Set Up Cloudflare Tunnel

Follow the complete setup guide:

```bash
# Read the setup guide
cat backend/cloudflare-tunnel-setup.md

# Or run automated installer
sudo bash backend/scripts/install_cloudflare_tunnel.sh
```

Key steps:
1. Add domain to Cloudflare
2. Install cloudflared
3. Authenticate with Cloudflare
4. Create tunnel
5. Configure DNS routing

After setup, you should have:
- `backend/cloudflare-tunnel.yml` - Tunnel configuration
- `backend/cloudflare-credentials.json` - Tunnel credentials

### Step 4: Configure Environment

Create `.env` file in project root:

```bash
cat > .env <<EOF
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=$(openssl rand -hex 16)

# JWT Secret (generate secure key)
JWT_SECRET_KEY=$(openssl rand -hex 32)

# Production URL
PRODUCTION_URL=https://zook.yourdomain.com

# Cloudflare Tunnel Token (get from tunnel credentials)
CLOUDFLARE_TUNNEL_TOKEN=your-tunnel-token-here
EOF

# Secure the file
chmod 600 .env
```

**Important:** Replace `zook.yourdomain.com` with your actual domain.

### Step 5: Update Tunnel Configuration

Edit `backend/cloudflare-tunnel.yml`:

```yaml
tunnel: YOUR_TUNNEL_ID
credentials-file: /etc/cloudflared/credentials.json

ingress:
  - hostname: zook.yourdomain.com  # <-- Update this
    service: http://backend:8000
    originRequest:
      noTLSVerify: true
      connectTimeout: 30s
      disableChunkedEncoding: false
  
  - service: http_status:404
```

### Step 6: Launch Services

```bash
# Start all services
docker-compose -f docker-compose.production.yml up -d

# Check status
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f
```

Expected output:
```
NAME                    STATUS              PORTS
zook-postgres-prod      Up (healthy)        127.0.0.1:5432->5432/tcp
zook-backend-prod       Up (healthy)        127.0.0.1:8000->8000/tcp
zook-cloudflared        Up                  
```

### Step 7: Verify Deployment

```bash
# Test local backend
curl http://localhost:8000/health

# Test production HTTPS URL
curl https://zook.yourdomain.com/health

# Should return: {"status":"healthy","service":"zook-auth-server"}
```

### Step 8: Create Admin User

```bash
# Access backend container
docker-compose -f docker-compose.production.yml exec backend bash

# Create admin user
python3 -c "
from app.database import AsyncSessionLocal
from app.models import User
from app.security import get_password_hash
import asyncio

async def create_admin():
    async with AsyncSessionLocal() as db:
        admin = User(
            username='admin',
            hashed_password=get_password_hash('change-this-password'),
            is_active=True
        )
        db.add(admin)
        await db.commit()
        print('Admin user created: admin / change-this-password')

asyncio.run(create_admin())
"
```

### Step 9: Access Your Application

1. **Open in browser:** `https://zook.yourdomain.com`
2. **Click "Scan" button**
3. **Login with:** `admin` / `change-this-password`
4. **Grant camera permission**
5. **Start monitoring!**

### Step 10: Security Hardening

```bash
# Enable firewall
sudo ufw allow ssh
sudo ufw allow 443/tcp
sudo ufw enable

# Set up automatic updates
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure -plow unattended-upgrades

# Configure log rotation
sudo cat > /etc/logrotate.d/zook <<EOF
/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    missingok
    delaycompress
    copytruncate
}
EOF
```

---

## Direct Deployment

### Step 1: Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip -y

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Install system dependencies for AI models
sudo apt install libgl1 libglib2.0-0 libsm6 libxext6 libxrender-dev -y
```

### Step 2: Set Up Database

```bash
# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql <<EOF
CREATE DATABASE zook;
CREATE USER zookadmin WITH PASSWORD 'your-strong-password';
GRANT ALL PRIVILEGES ON DATABASE zook TO zookadmin;
\q
EOF

# Run migrations
cd backend
sudo -u postgres psql -d zook -f migrations/init.sql
sudo -u postgres psql -d zook -f migrations/002_clips_tracking.sql
```

### Step 3: Set Up Backend

```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file
cat > .env <<EOF
DATABASE_URL=postgresql+asyncpg://zookadmin:your-strong-password@localhost:5432/zook
DATABASE_SSL_MODE=require
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
CORS_ORIGINS=https://zook.yourdomain.com
ENVIRONMENT=production
USE_HTTPS=true
ENFORCE_HTTPS_REDIRECT=true
CLOUDFLARE_TUNNEL_ENABLED=true
PRODUCTION_URL=https://zook.yourdomain.com
USE_CUSTOM_MODEL=true
CUSTOM_MODEL_PATH=app/models/custom_knife_model.pt
DETECTION_DEVICE=cpu
DETECTION_CONFIDENCE_THRESHOLD=0.90
EOF

chmod 600 .env
```

### Step 4: Set Up Cloudflare Tunnel

```bash
# Run automated installer
sudo bash scripts/install_cloudflare_tunnel.sh

# Or follow manual setup
cat cloudflare-tunnel-setup.md
```

### Step 5: Create Systemd Service

```bash
# Create service file
sudo cat > /etc/systemd/system/zook-backend.service <<EOF
[Unit]
Description=Zook FastAPI Backend
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/path/to/zook/backend
Environment="PATH=/path/to/zook/backend/venv/bin"
ExecStart=/path/to/zook/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Update paths in the file above, then:
sudo systemctl daemon-reload
sudo systemctl enable zook-backend
sudo systemctl start zook-backend

# Check status
sudo systemctl status zook-backend
```

### Step 6: Verify Deployment

```bash
# Test backend
curl http://localhost:8000/health

# Test HTTPS
curl https://zook.yourdomain.com/health

# View logs
sudo journalctl -u zook-backend -f
```

---

## Post-Deployment Configuration

### SSL Certificate Verification

```bash
# Check SSL certificate
openssl s_client -connect zook.yourdomain.com:443 -servername zook.yourdomain.com

# Should show Cloudflare certificate
# Issuer: C=US, O=Cloudflare, Inc., CN=Cloudflare Inc ECC CA-3
```

### Security Headers Test

Visit https://securityheaders.com/ and test your domain. You should see:
- Strict-Transport-Security
- X-Content-Type-Options
- X-Frame-Options
- Content-Security-Policy

### WebSocket (WSS) Test

```bash
# Install wscat
npm install -g wscat

# Get JWT token
TOKEN=$(curl -s -X POST https://zook.yourdomain.com/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your-password"}' | jq -r '.access_token')

# Test WebSocket
wscat -c "wss://zook.yourdomain.com/ws/stream?token=$TOKEN"
```

### Performance Testing

```bash
# Install Apache Bench
sudo apt install apache2-utils -y

# Test API performance
ab -n 1000 -c 10 https://zook.yourdomain.com/health

# Should show:
# - Requests per second: >500
# - Time per request: <20ms
```

---

## Monitoring & Maintenance

### View Logs

**Docker Deployment:**
```bash
# All services
docker-compose -f docker-compose.production.yml logs -f

# Specific service
docker-compose -f docker-compose.production.yml logs -f backend
```

**Direct Deployment:**
```bash
# Backend logs
sudo journalctl -u zook-backend -f

# Cloudflare Tunnel logs
sudo journalctl -u cloudflared -f
```

### Database Backup

**Docker:**
```bash
# Backup
docker-compose -f docker-compose.production.yml exec postgres \
  pg_dump -U postgres zook > backup-$(date +%Y%m%d).sql

# Restore
cat backup-20250101.sql | docker-compose -f docker-compose.production.yml exec -T postgres \
  psql -U postgres zook
```

**Direct:**
```bash
# Backup
sudo -u postgres pg_dump zook > backup-$(date +%Y%m%d).sql

# Restore
sudo -u postgres psql zook < backup-20250101.sql
```

### Update Application

**Docker:**
```bash
cd zook
git pull
docker-compose -f docker-compose.production.yml build
docker-compose -f docker-compose.production.yml up -d
```

**Direct:**
```bash
cd zook
git pull
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart zook-backend
```

### Monitor Resources

```bash
# CPU and Memory usage
docker stats  # Docker
htop  # Direct

# Disk space
df -h

# Database size
docker-compose -f docker-compose.production.yml exec postgres \
  psql -U postgres -c "SELECT pg_size_pretty(pg_database_size('zook'));"
```

---

## Troubleshooting

### Issue: 502 Bad Gateway

**Possible causes:**
- Backend not running
- Cloudflare Tunnel not connected
- Wrong service URL in tunnel config

**Solution:**
```bash
# Check backend
curl http://localhost:8000/health

# Check tunnel
sudo systemctl status cloudflared
cloudflared tunnel info <tunnel-name>

# Restart services
docker-compose -f docker-compose.production.yml restart
```

### Issue: WebSocket Connection Failed

**Possible causes:**
- CORS not configured correctly
- Token expired
- Cloudflare WebSocket not enabled

**Solution:**
```bash
# Check CORS in .env
grep CORS_ORIGINS backend/.env

# Check tunnel config has disableChunkedEncoding: false
cat backend/cloudflare-tunnel.yml

# Test with fresh token
```

### Issue: Camera Access Blocked

**Possible causes:**
- Using HTTP instead of HTTPS
- Browser permissions denied
- Mixed content (loading HTTP resources on HTTPS page)

**Solution:**
- Verify URL starts with `https://`
- Check browser console for mixed content warnings
- Ensure USE_HTTPS=true in backend .env

### Issue: High CPU Usage

**Solution:**
```bash
# Reduce workers
# In docker-compose.production.yml or uvicorn command:
--workers 2  # Instead of 4

# Use GPU for detection (if available)
DETECTION_DEVICE=cuda

# Reduce detection confidence threshold
DETECTION_CONFIDENCE_THRESHOLD=0.85
```

---

## Security Checklist

Before going live:

- [ ] Changed all default passwords
- [ ] Generated strong JWT_SECRET_KEY
- [ ] Enabled DATABASE_SSL_MODE=require
- [ ] Set ENFORCE_HTTPS_REDIRECT=true
- [ ] Updated CORS_ORIGINS (removed localhost)
- [ ] Configured firewall (only allow ports 22, 443)
- [ ] Set up automated backups
- [ ] Configured log rotation
- [ ] Tested SSL certificate
- [ ] Verified security headers
- [ ] Tested WebSocket over WSS
- [ ] Set up monitoring/alerting
- [ ] Documented credentials securely
- [ ] Reviewed Cloudflare security settings
- [ ] Enabled rate limiting in Cloudflare
- [ ] Configured WAF rules

---

## Performance Optimization

### Enable GPU Detection

If server has NVIDIA GPU:

```bash
# Install CUDA toolkit
# Follow: https://developer.nvidia.com/cuda-downloads

# Update .env
DETECTION_DEVICE=cuda

# Restart backend
docker-compose -f docker-compose.production.yml restart backend
```

### Enable Redis Caching

```bash
# Add Redis to docker-compose.production.yml
redis:
  image: redis:7-alpine
  container_name: zook-redis
  networks:
    - internal
  restart: unless-stopped

# Update backend to use Redis for session caching
# (Feature to be implemented)
```

### CDN for Static Assets

Use Cloudflare's CDN:
1. Go to Cloudflare Dashboard
2. Enable "Auto Minify" for JS/CSS
3. Enable "Brotli" compression
4. Set cache rules for static assets

---

## Scaling Considerations

### Horizontal Scaling

To handle more users:

```yaml
# docker-compose.production.yml
backend:
  deploy:
    replicas: 3  # Run 3 backend instances
```

Add load balancer (Nginx):

```nginx
upstream zook_backend {
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}
```

### Database Replication

For high availability:

```yaml
# Add PostgreSQL replica
postgres-replica:
  image: postgres:15-alpine
  environment:
    POSTGRES_MASTER_SERVICE_HOST: postgres
```

---

## Support & Resources

- **Documentation:** `docs/PROJECT_DOCUMENTATION.md`
- **Cloudflare Setup:** `backend/cloudflare-tunnel-setup.md`
- **Environment Config:** `backend/ENV_CONFIG.md`
- **Cloudflare Community:** https://community.cloudflare.com/
- **FastAPI Docs:** https://fastapi.tiangolo.com/

---

## Next Steps

After successful deployment:

1. **Set up monitoring** - Use Cloudflare Analytics, Sentry, or Prometheus
2. **Configure alerting** - Email/SMS alerts for downtime
3. **Plan backups** - Automated daily backups with off-site storage
4. **Review logs** - Set up log aggregation (ELK, Splunk, etc.)
5. **Performance tuning** - Monitor and optimize based on usage patterns
6. **Security audit** - Regular penetration testing
7. **Documentation** - Keep deployment docs updated

**Congratulations!** Your Zook surveillance system is now live with enterprise-grade HTTPS encryption! 🎉

