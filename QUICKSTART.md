# Zook - Quick Start Guide

## 🚀 Fast Setup (5 minutes)

### Prerequisites
- **Python 3.11+** ([Download](https://www.python.org/downloads/))
- **PostgreSQL 14+** ([Download](https://www.postgresql.org/download/))
- **Modern Browser** (Chrome, Firefox, or Edge)

### Step 1: Database Setup

```bash
# Start PostgreSQL (if not running)
# Windows: Start from Services or pgAdmin

# Create database
psql -U postgres
CREATE DATABASE zook;
\q

# Run migrations
cd backend
psql -U postgres -d zook -f migrations/init.sql
```

### Step 2: Backend Setup

**Windows (PowerShell):**
```powershell
cd backend
.\start_server.ps1
```

**Linux/Mac:**
```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your settings

# Start server
uvicorn app.main:app --reload --port 8000
```

Server will start at: **http://localhost:8000**  
API Docs: **http://localhost:8000/docs**

### Step 3: Frontend Setup

```bash
# Open new terminal
cd ui/src

# Option 1: Direct file open
# Open index.html in your browser

# Option 2: HTTP server (recommended)
# Python
python -m http.server 3500

# Node.js
npx http-server -p 3500
```

Frontend will be at: **http://localhost:3500**

### Step 4: Test the Application

1. **Register a user** (using API docs or backend README):
   ```bash
   curl -X POST http://localhost:8000/api/auth \
     -H "Content-Type: application/json" \
     -d '{"username":"testuser","password":"password123"}'
   ```

2. **Login via UI**:
   - Go to http://localhost:3500
   - Click "Scan" button
   - Enter credentials:
     - Username: `Brad` (pre-created test user)
     - Password: `12345678`
     - OR use your registered username
   - Check consent box
   - Click "Authenticate"

3. **Grant camera access** when prompted

4. **View the dashboard** with live camera feed

## 📚 Next Steps

- **API Documentation**: http://localhost:8000/docs
- **Full Documentation**: `docs/PROJECT_DOCUMENTATION.md`
- **Backend README**: `backend/README.md`
- **Frontend README**: `ui/src/README.md`

## 🔧 Common Issues

**Backend won't start:**
- Check PostgreSQL is running
- Verify `.env` file exists with correct DATABASE_URL
- Check port 8000 is not in use

**Frontend can't connect:**
- Verify backend is running on port 8000
- Check CORS origins in `.env` include `http://localhost:3500`
- Check browser console for errors

**Login fails:**
- Use default user: `Brad` / `12345678`
- Or register new user via `/api/auth` endpoint
- Check backend logs for errors

**Camera access denied:**
- Use HTTPS or localhost (HTTP works on localhost)
- Grant camera permissions in browser
- Try different browser if issues persist

## 🎯 Testing Endpoints

### Register User
```bash
POST http://localhost:8000/api/auth
{
  "username": "john",
  "password": "secure123"
}
```

### Login
```bash
POST http://localhost:8000/api/login
{
  "username": "john",
  "password": "secure123"
}

Response:
{
  "access_token": "eyJ...",
  "session_id": "uuid",
  "username": "john",
  "expires_in": 86400
}
```

### Verify Token
```bash
GET http://localhost:8000/api/verify
Authorization: Bearer <your-token>
```

## 🌐 Remote Testing (ngrok)

```bash
# Install ngrok: https://ngrok.com/download

# Start tunnels
ngrok start --config config.yml --all

# Update frontend apiUrl in ui/src/app.js with ngrok URL
```

## 📊 Project Status

✅ **Complete**:
- User authentication with JWT
- Session management
- PostgreSQL database
- Camera feed integration
- Responsive UI
- AI threat detection (YOLOv11 + CLIP validation)
- WebSocket streaming
- HTTPS encryption support

🔄 **In Progress**:
- WebRTC streaming
- Email notifications

## 🌐 Production Deployment

Ready to deploy with HTTPS? See our complete production guide:

**📘 [Production Deployment Guide](docs/PRODUCTION_DEPLOYMENT.md)**

Includes:
- ✅ **Cloudflare Tunnel setup** (free HTTPS/SSL)
- ✅ **Docker Compose** deployment
- ✅ **Security hardening** checklist
- ✅ **Monitoring & maintenance** guide
- ✅ **Troubleshooting** solutions

**Quick production setup:**

```bash
# 1. Set up Cloudflare Tunnel
sudo bash backend/scripts/install_cloudflare_tunnel.sh

# 2. Configure environment
cp backend/ENV_CONFIG.md backend/.env  # Edit with your values

# 3. Deploy with Docker
docker-compose -f docker-compose.production.yml up -d

# 4. Access at https://yourdomain.com
```

## 💡 Tips

- Use the interactive API docs at `/docs` to test endpoints
- Check backend logs for detailed error messages
- Frontend stores JWT in localStorage
- Default test user: `Brad` / `12345678`
- Sessions expire after 24 hours
- **Production:** Enable HTTPS before deploying (see deployment guide)

## 🆘 Need Help?

- **Production Deployment:** `docs/PRODUCTION_DEPLOYMENT.md`
- **Cloudflare Tunnel:** `backend/cloudflare-tunnel-setup.md`
- **Environment Config:** `backend/ENV_CONFIG.md`
- **Project Documentation:** `docs/PROJECT_DOCUMENTATION.md`
- **Backend Details:** `backend/README.md`
- **API Examples:** http://localhost:8000/docs
- **Troubleshooting:** Check browser console and backend logs

---

**Zook Project** - AI-Powered Surveillance Platform  
Built with FastAPI + Vanilla JS - Ready for 24/7 Monitoring 🔒

**Enterprise Features:**
- 🔐 HTTPS encryption with Cloudflare Tunnel (zero-cost SSL)
- 🤖 AI threat detection (YOLOv11 knife detection + CLIP validation)
- 📹 Real-time WebSocket streaming at 15fps
- 🗄️ PostgreSQL with automatic clip cleanup
- 🚀 Docker-ready production deployment


