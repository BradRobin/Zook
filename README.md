# Zook

**AI-Powered Real-Time Surveillance Platform**

Zook is an innovative web application for real-time threat detection using live camera feeds. Built with a minimalist design philosophy, Zook enhances safety and enforces discipline in educational institutions, retail spaces, and public areas across Nairobi and beyond.

## 🚀 Quick Start

See **[QUICKSTART.md](QUICKSTART.md)** for 5-minute setup guide!

## 🏗️ Architecture

- **Frontend**: Vanilla JavaScript, HTML5, CSS3 (minimalist "calculator" design)
- **Backend**: Python FastAPI with JWT authentication
- **Database**: PostgreSQL with async SQLAlchemy
- **Streaming**: MediaMTX (WebRTC/RTSP) - *planned*
- **AI Detection**: YOLOv12/FastAPI - *in progress*

## ✨ Features

### Current (v1.0)
- ✅ User authentication with JWT tokens
- ✅ Session management and tracking
- ✅ Live camera feed integration
- ✅ Responsive UI (mobile/tablet/desktop)
- ✅ Auto-generated API documentation
- ✅ PostgreSQL database with sessions
- ✅ Secure password hashing (bcrypt)
- ✅ CORS configuration
- ✅ Stream validation for MediaMTX

### Planned
- 🔄 Real AI threat detection (YOLOv12)
- 🔄 WebRTC streaming integration
- 📋 Email/SMS alerts
- 📋 Multi-camera dashboard
- 📋 Drone camera integration
- 📋 Mobile app

## 📚 Documentation

- **[Quick Start Guide](QUICKSTART.md)** - Get running in 5 minutes
- **[Project Documentation](docs/PROJECT_DOCUMENTATION.md)** - Complete technical docs
- **[Backend README](backend/README.md)** - FastAPI server details
- **[Vision Document](docs/vision.md)** - Project goals and roadmap

## 🛠️ Tech Stack

**Backend (Python 3.11+)**
- FastAPI - Modern async web framework
- SQLAlchemy - Async ORM
- Pydantic - Data validation
- python-jose - JWT tokens
- passlib - Password hashing
- asyncpg - PostgreSQL driver

**Frontend**
- Vanilla JavaScript (zero dependencies)
- HTML5 + CSS3
- getUserMedia API for camera
- Canvas API for frame capture

**Infrastructure**
- PostgreSQL 14+
- MediaMTX (WebRTC server)
- ngrok (remote testing)

## 🚦 Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Modern browser with camera access

### Installation

```bash
# 1. Clone repository
git clone https://github.com/yourusername/Zook.git
cd Zook

# 2. Setup database
psql -U postgres
CREATE DATABASE zook;
\q
cd backend
psql -U postgres -d zook -f migrations/init.sql

# 3. Setup backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
uvicorn app.main:app --reload --port 8000

# 4. Setup frontend (new terminal)
cd ui/src
python -m http.server 3500
```

Visit:
- Frontend: http://localhost:3500
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Default Test User
- Username: `Brad`
- Password: `12345678`

## 📡 API Endpoints

- `POST /api/auth` - User registration
- `POST /api/login` - Login (returns JWT)
- `GET /api/verify` - Verify token
- `POST /api/logout` - Logout
- `POST /api/stream/validate` - MediaMTX validation
- `GET /docs` - Interactive API documentation

## 🔒 Security

- bcrypt password hashing (12 rounds)
- JWT tokens (HS256, 24h expiry)
- Session tracking with device info
- HTTPS redirect in production
- CORS protection
- Row Level Security (RLS) policies

## 🎯 Use Cases

- 🏫 **Schools**: Detect bullying, weapons, unauthorized access
- 🛒 **Retail**: Employee theft, customer safety
- 🚌 **Transportation**: Fleet monitoring, safety compliance
- 🛡️ **Security**: Enhanced monitoring, rapid response

## 🌍 Compliance

✅ Kenya Data Protection Act compliant
- Local processing
- Explicit user consent
- Minimal data retention
- Clear privacy policies

## 🤝 Contributing

This project is open-source. Contributions welcome!

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📞 Contact

Project by GenZ developers - Building discipline one scan at a time.

## 📄 License

Open-source foundation - License TBD

---

**Note**: This platform is designed for safety enhancement, not surveillance overreach. Always obtain proper consent and follow local regulations.

Zook: An innovative AI-powered web app for real-time surveillance, detecting harmful objects using live camera feeds. Built with a minimalist design, Zook enhances safety and enforces discipline in Nairobi and beyond, starting with a phone-cam MVP and scaling to drone integration. Open-source foundation, crafted for 24/7 monitoring by a GenZ team.
