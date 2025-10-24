# Zook Frontend - Quick Start Guide

## Prerequisites
- Backend server running on `http://localhost:8000`
- Python installed (for development server)
- Modern web browser with camera access

## Quick Start

### 1. Start the Backend (if not already running)
```powershell
cd ..\backend
.\start_server.ps1
```

### 2. Start the Frontend
```powershell
cd ui
.\start_ui.ps1
```

### 3. Open in Browser
Navigate to: **http://localhost:3500**

## Testing the UI

### Login Credentials
Use the pre-created test user:
- **Username:** `Brad`
- **Password:** `12345678`

### Features to Test
1. **Landing Page**
   - Click "Scan" button to trigger login

2. **Authentication**
   - Enter credentials
   - Check consent checkbox
   - Click "Authenticate"

3. **Dashboard**
   - Grant camera permissions when prompted
   - View live camera feed
   - Monitor detection logs (simulated for MVP)
   - Toggle pause/resume scanning
   - Access settings

## How It Works

### Authentication Flow
1. User clicks "Scan" → Login modal appears
2. User enters credentials → Sent to backend `/api/login`
3. Backend returns JWT token + session ID
4. Frontend stores token in localStorage
5. All subsequent requests include JWT in headers

### Camera Feed
- Uses browser's `getUserMedia` API
- Video displayed at 1280x720 (ideal)
- Frames captured every 5 seconds for analysis

### Detection (MVP)
Currently simulated with:
- 10% random detection probability
- Simulated threats (knife/gun/weapon)
- Visual alerts (red border pulse)
- Detection logs with timestamps

## Troubleshooting

### "This site can't be reached"
- Ensure backend is running: `http://localhost:8000`
- Check port 3500 is not in use
- Try `http://127.0.0.1:3500` instead

### "Cannot connect to server"
- Backend must be running first
- Check backend is on port 8000: `netstat -ano | findstr :8000`
- Restart backend if needed

### Camera not working
- Grant camera permissions in browser
- Check camera is not in use by another app
- Try different browser (Chrome/Edge recommended)

### Authentication fails
- Verify backend database is initialized
- Check credentials: Username=`Brad`, Password=`12345678`
- Check browser console for detailed errors (F12)

## API Endpoints Used

### Authentication
- `POST /api/login` - User login
- `GET /api/verify` - Token verification
- `POST /api/logout` - User logout (future)

### Detection (Future)
- `POST /detect` - Send camera frame for AI analysis

## Architecture

```
┌─────────────────────────────────────────────┐
│  Browser (http://localhost:3500)            │
│  ┌─────────────────────────────────────┐   │
│  │  Landing Page (index.html)          │   │
│  │  - Minimal UI                        │   │
│  │  - "Scan" button triggers auth       │   │
│  └─────────────────────────────────────┘   │
│                    ↓                         │
│  ┌─────────────────────────────────────┐   │
│  │  Login Modal                         │   │
│  │  - Username/Password                 │   │
│  │  - Consent checkbox                  │   │
│  └─────────────────────────────────────┘   │
│                    ↓                         │
│         POST /api/login                      │
│         (Backend: localhost:8000)            │
│                    ↓                         │
│  ┌─────────────────────────────────────┐   │
│  │  Dashboard                           │   │
│  │  - Live camera feed (70%)            │   │
│  │  - Detection logs (30%)              │   │
│  │  - Control buttons                   │   │
│  │  - Settings drawer                   │   │
│  └─────────────────────────────────────┘   │
│                    ↓                         │
│         Capture frames every 5s              │
│         POST /detect (future)                │
└─────────────────────────────────────────────┘
```

## Next Steps

1. ✅ Test authentication with existing user
2. ✅ Verify camera feed works
3. ✅ Check detection simulation
4. ⏳ Integrate real AI detection API
5. ⏳ Add MediaMTX streaming
6. ⏳ Implement multi-camera support

## Files Overview

- `index.html` - Main HTML structure
- `app.js` - Application logic and API calls
- `style.css` - Minimalist styling
- `start_ui.ps1` - Development server launcher

## Security Notes

- JWT tokens stored in localStorage
- Tokens expire after 24 hours (1440 minutes)
- Camera feed processed locally in browser
- HTTPS required for production (not localhost)

## Support

For issues or questions, check:
- Backend API docs: http://localhost:8000/docs
- Browser console (F12) for JavaScript errors
- Backend terminal for server logs

