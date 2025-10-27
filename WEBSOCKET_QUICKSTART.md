# 🚀 Zook Real-Time Detection - Quick Start Guide

**Complete step-by-step guide to run the WebSocket-powered real-time threat detection system.**

---

## 📋 Prerequisites

- **Python 3.11+** installed
- **PostgreSQL** running (for backend)
- **Modern web browser** (Chrome, Firefox, Edge)
- **Webcam** (for testing)

---

## 🎯 Step-by-Step Instructions

### Step 1: Start PostgreSQL Database

**Windows:**
```powershell
# PostgreSQL should already be running as a service
# Verify it's running:
Get-Service postgresql*

# If not running, start it:
Start-Service postgresql-x64-16  # Adjust version number as needed
```

**Verify database connection:**
```bash
# Test connection (use your password)
psql -U postgres -d zook_db
# Type \q to exit
```

---

### Step 2: Start Backend Server

**Open PowerShell in the project root:**

```powershell
# Navigate to backend directory
cd backend

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Verify environment variables are set (check .env file exists)
# Should contain DATABASE_URL, SECRET_KEY, etc.

# Start the server
uvicorn app.main:app --reload --port 8000
```

**Expected output:**
```
INFO: Uvicorn running on http://127.0.0.1:8000
INFO: Starting up Zook Auth Server...
INFO: Environment: development
INFO: Database initialized successfully
INFO: Initializing YOLOv11 threat detection model...
INFO: Model loaded on device: cpu
INFO: Detection model initialized and ready
INFO: SessionManager initialized
INFO: Application startup complete.
```

**✅ Backend is ready when you see:**
- ✓ Database initialized
- ✓ YOLOv11 model loaded
- ✓ SessionManager initialized
- ✓ Application startup complete

---

### Step 3: Test Backend Health

**Open a NEW PowerShell window** (keep backend running):

```bash
# Test basic health
curl http://localhost:8000/

# Test WebSocket streaming health
curl http://localhost:8000/stream/health

# Expected response:
# {
#   "status": "healthy",
#   "service": "realtime_streaming",
#   "websocket_endpoint": "/ws/stream",
#   "stats": { ... }
# }
```

---

### Step 4: Start Frontend UI

**Open ANOTHER PowerShell window** (keep backend running):

```powershell
# Navigate to UI directory
cd ui

# Start simple HTTP server
python -m http.server 3000

# Or use Node.js if you have it:
# npx http-server -p 3000
```

**Expected output:**
```
Serving HTTP on :: port 3000 (http://[::]:3000/) ...
```

**✅ Frontend is ready at:** `http://localhost:3000`

---

### Step 5: Open the Application

1. **Open your browser** and navigate to: `http://localhost:3000`

2. **You should see:**
   - Zook landing page
   - "START SCAN" button
   - Calculator-style minimal UI

---

### Step 6: Login to Dashboard

1. **Click "START SCAN"** button

2. **Login with test credentials:**
   - **Username:** `Brad`
   - **Password:** `12345678`
   - ✓ Check the consent checkbox
   - Click **"Login"**

3. **Allow camera access** when browser prompts

---

### Step 7: Real-Time Detection Active!

**Once logged in, you should see:**

✅ **Video feed** displaying your camera  
✅ **Status indicators** in top-right corner:
   - **FPS:** Shows processing frame rate (should reach ~15 FPS)
   - **Recording:** Red dot appears when threat detected
   - **Idle:** Shows minutes since last detection

✅ **Status logs** at the bottom showing:
   - "Camera feed active"
   - "Connecting to real-time detection service..."
   - "✅ Real-time streaming active (15 FPS)"

✅ **Backend logs** showing:
   ```
   INFO: WebSocket connection attempt
   INFO: WebSocket authenticated: user Brad
   INFO: Session created: <session-id> (total active: 1)
   INFO: StreamProcessor started
   INFO: Processing loop started
   ```

---

### Step 8: Test Threat Detection

#### Option A: Test with Real Knife (Recommended)

1. **Hold a knife in front of the camera**
2. **Wait 2-3 seconds** for detection
3. **Look for:**
   - 🚨 Red border flash around video
   - Status log: "🚨 KNIFE detected at [time] - Confidence: XX%"
   - Recording indicator (red dot) appears
   - Backend logs show detection details

#### Option B: Test with Knife Image

1. **Find a knife image online** or use test images:
   ```bash
   # Download test image
   curl -o knife.jpg https://example.com/knife-image.jpg
   ```

2. **Display image on phone/tablet**
3. **Hold device in front of camera**

---

### Step 9: Verify Recording Started

**When threat is detected:**

1. **UI shows:**
   - 🔴 Recording indicator (pulsing red dot)
   - Log entry: "KNIFE detected"
   - Green FPS counter continues

2. **Backend saves recording to:**
   ```
   backend/recordings/
   └── <session-id>_<timestamp>.mp4
   ```

3. **Check backend logs:**
   ```
   INFO: Recording started for session <id>: ./recordings/...mp4
   INFO: Session <id>: Frame #100, FPS: 15.2, Detections: 3
   ```

4. **Recording continues** while threat is visible
5. **Recording stops** 30 seconds after last detection

---

### Step 10: Verify Idle Timeout (Optional)

**Test 5-minute idle timeout:**

1. **Remove knife from view**
2. **Wait 5 minutes** without showing any threats
3. **WebSocket will auto-disconnect:**
   - UI log: "Stream closed: Idle timeout (5 minutes without detection)"
   - Backend log: "Session removed: <id> (remaining: 0)"

4. **Click "Resume Scan"** to reconnect

---

## 🎛️ System Controls

### Pause/Resume Scanning
- **Click "Pause Scan"** - Stops frame streaming (keeps connection)
- **Click "Resume Scan"** - Resumes streaming

### Settings Panel
- **Click gear icon** (⚙️) - Opens settings drawer
- View system info and configuration

### Manual Disconnect
- **Refresh page** - Cleanly disconnects WebSocket
- **Close tab** - Automatically cleans up session

---

## 📊 Performance Monitoring

### Frontend Indicators

**FPS Counter:**
- Target: **15.0 FPS** (processing rate)
- Normal range: 14.5 - 15.5 FPS
- Low (<10 FPS): System overloaded

**Recording Indicator:**
- **Hidden:** No threats detected
- **Visible (red pulsing):** Recording active

**Idle Counter:**
- Shows minutes since last detection
- Appears after 1 minute
- Warning at 4+ minutes (timeout soon)

### Backend Logs

**Frame processing logs (every 100 frames):**
```
INFO: Session <id>: Frame #300, FPS: 15.1, Detections: 5, Processing: 85.3ms
```

**Key metrics:**
- **Processing time:** Should be <100ms per frame
- **FPS:** Should maintain ~15 FPS
- **Queue size:** Should be 0-5 (not building up)

### Monitor Active Sessions

```bash
# Check active sessions
curl http://localhost:8000/stream/sessions

# Response shows:
# - active_sessions: 1
# - session details: frame count, detections, recording status
```

---

## 🐛 Troubleshooting

### Backend Won't Start

**Error:** `ModuleNotFoundError: No module named 'ultralytics'`

**Fix:**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

**Error:** `Could not connect to database`

**Fix:**
```powershell
# Start PostgreSQL
Start-Service postgresql-x64-16

# Verify DATABASE_URL in .env
# Should be: postgresql://postgres:password@localhost/zook_db
```

---

**Error:** `Port 8000 already in use`

**Fix:**
```powershell
# Find process using port 8000
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess

# Kill it or use different port:
uvicorn app.main:app --reload --port 8001
```

---

### WebSocket Connection Fails

**Error:** "WebSocket connection error" or "Authentication failed"

**Fixes:**

1. **Check backend is running:**
   ```bash
   curl http://localhost:8000/stream/health
   ```

2. **Verify JWT token is valid:**
   - Logout and login again
   - Check browser console for token errors

3. **Check firewall/antivirus:**
   - Allow connections to localhost:8000
   - Disable temporarily to test

4. **Check browser console (F12):**
   - Look for WebSocket errors
   - Verify ws://localhost:8000 connection

---

### No Detections Occurring

**Issue:** Knife in frame but no detection

**Possible causes:**

1. **Model confidence too low:**
   - Pre-trained COCO model has ~65% accuracy for knives
   - Threshold is 90% (very strict)
   - **Solution:** Train custom model (see `ai/README.md`)

2. **Lighting conditions:**
   - Ensure good lighting
   - Avoid glare/reflections
   - Use clear knife image

3. **Debug detection:**
   ```bash
   # Check backend logs for detection attempts
   # Should see:
   # "YOLO detected X object(s)"
   # "Detection: class_id=43 (knife), confidence=XX%"
   ```

4. **Lower confidence threshold (temporary):**
   ```bash
   curl -X POST http://localhost:8000/detect/threshold \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"threshold": 0.5}'
   ```

---

### Recording Not Saving

**Issue:** Detection works but no MP4 file created

**Check:**

1. **Recordings directory exists:**
   ```bash
   ls backend/recordings/
   ```

2. **Backend has write permissions:**
   ```bash
   # Windows - check folder properties
   # Ensure Users have Write permission
   ```

3. **Check backend logs:**
   ```
   INFO: Recording started for session <id>
   INFO: Recording stopped: <path> (X frames, X.Xs, X.XXMB)
   ```

4. **OpenCV dependencies installed:**
   ```bash
   pip install opencv-python-headless==4.10.0.84
   ```

---

### High CPU Usage

**Issue:** CPU at 100%, FPS drops

**Optimizations:**

1. **Use GPU (if available):**
   ```python
   # In backend/.env
   DETECTION_DEVICE=cuda  # or mps for Mac
   ```

2. **Reduce frame rate:**
   ```python
   # In app.js, line ~18:
   this.targetFPS = 15;  // Reduce from 30
   ```

3. **Use quantized model (future):**
   - Train INT8 ONNX model for 2-3x speedup
   - See `ai/scripts/quantize_model.py`

---

### Frontend Not Loading

**Issue:** `localhost:3000` shows error

**Fixes:**

1. **Check Python HTTP server running:**
   ```powershell
   # Should see:
   # Serving HTTP on :: port 3000
   ```

2. **Try different port:**
   ```bash
   python -m http.server 8080
   # Then open http://localhost:8080
   ```

3. **Check browser console (F12):**
   - Look for JavaScript errors
   - Verify files loaded (Network tab)

---

## 🎉 Success Checklist

After following all steps, you should have:

- ✅ Backend running on `http://localhost:8000`
- ✅ Frontend accessible at `http://localhost:3000`
- ✅ WebSocket connection established
- ✅ Camera feed active
- ✅ FPS counter showing ~15 FPS
- ✅ Detection logs appearing
- ✅ Recording starts on threat detection
- ✅ Recordings saved to `backend/recordings/`

---

## 📚 Next Steps

### Improve Detection Accuracy

**Train custom model for >90% accuracy:**

```bash
cd ai

# Follow training guide
cat README.md
cat QUICKSTART.md

# Quick training:
python scripts/download_datasets.py
python scripts/prepare_dataset.py
python scripts/train.py --epochs 100
python scripts/export_model.py
```

See **`ai/README.md`** for complete training documentation.

### Deploy to Production

1. **Enable HTTPS/WSS** for secure WebSocket
2. **Use GPU** for better performance
3. **Configure CDN** for recordings
4. **Set up monitoring** (Prometheus/Grafana)
5. **Enable database session persistence**

See **`backend/README.md`** Docker deployment section.

### Add RTSP Support (Future)

**For drone cameras:**

1. Implement RTSP client (`backend/app/services/rtsp_client.py`)
2. Convert RTSP to frame queue
3. Use same processing pipeline

See **`yolov11-detection-service.plan.md`** Phase 6.

---

## 🔗 Documentation Links

- **Backend API:** `backend/README.md`
- **Custom Training:** `ai/README.md`
- **WebSocket Implementation:** `WEBSOCKET_IMPLEMENTATION_STATUS.md`
- **Testing Guide:** `backend/TEST_WEBSOCKET.md`
- **Full Plan:** `yolov11-detection-service.plan.md`

---

## 💬 Support

**Having issues?**

1. Check backend logs for errors
2. Check browser console (F12) for frontend errors
3. Review troubleshooting section above
4. Check `WEBSOCKET_IMPLEMENTATION_STATUS.md` for technical details

**System working? 🎊**

You now have a real-time threat detection system with:
- WebSocket streaming (15 FPS)
- <100ms latency
- Automatic recording
- 5-minute idle timeout
- Session management

---

**Happy detecting! 🔍🔪🚨**

