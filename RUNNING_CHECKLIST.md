# ✅ Zook Application Running Checklist

Follow this checklist to launch your real-time threat detection system.

---

## 📝 Pre-Flight Checks

- [ ] PostgreSQL database is running
- [ ] Python 3.11+ installed
- [ ] Backend virtual environment created
- [ ] Backend dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file configured in backend directory
- [ ] Webcam connected and working

---

## 🚀 Launch Sequence

### Terminal 1: Backend Server

**Current Directory:** `C:\Users\bradr\OneDrive\Documents\GitHub\Zook`

```powershell
# Step 1.1: Navigate to backend
cd backend
```
- [ ] Navigated to backend directory

```powershell
# Step 1.2: Activate virtual environment
.\venv\Scripts\Activate.ps1
```
- [ ] Virtual environment activated (should see `(venv)` in prompt)

```powershell
# Step 1.3: Start backend server
uvicorn app.main:app --reload --port 8000
```
- [ ] Server starting...

**Wait for these log messages:**
- [ ] ✓ "Database initialized successfully"
- [ ] ✓ "Initializing YOLOv11 threat detection model..."
- [ ] ✓ "Model loaded on device: cpu"
- [ ] ✓ "Detection model initialized and ready"
- [ ] ✓ "SessionManager initialized"
- [ ] ✓ "Application startup complete"

**Backend Status:** ✅ RUNNING

---

### Terminal 2: Frontend Server

**Open NEW PowerShell window**

**Current Directory:** `C:\Users\bradr\OneDrive\Documents\GitHub\Zook`

```powershell
# Step 2.1: Navigate to UI
cd ui
```
- [ ] Navigated to UI directory

```powershell
# Step 2.2: Start frontend server
python -m http.server 3000
```
- [ ] Frontend serving on port 3000
- [ ] See message: "Serving HTTP on :: port 3000..."

**Frontend Status:** ✅ RUNNING

---

### Browser: Open Application

```
Step 3.1: Open browser and navigate to:
http://localhost:3000
```
- [ ] Browser opened
- [ ] Page loaded successfully
- [ ] See "Zook" landing page

```
Step 3.2: Click "START SCAN" button
```
- [ ] Login modal appeared

```
Step 3.3: Enter credentials:
Username: Brad
Password: 12345678
```
- [ ] Username entered
- [ ] Password entered
- [ ] Consent checkbox checked

```
Step 3.4: Click "Login" button
```
- [ ] Login successful
- [ ] Dashboard page appeared

```
Step 3.5: Allow camera access (browser prompt)
```
- [ ] Camera permission granted
- [ ] Video feed showing

---

## 🔍 Verification Checks

### Frontend Verification

**Look for these on dashboard:**

- [ ] ✓ Video feed is active (showing camera)
- [ ] ✓ Status log shows: "Camera feed active"
- [ ] ✓ Status log shows: "Connecting to real-time detection service..."
- [ ] ✓ Status log shows: "✅ Real-time streaming active (15 FPS)"
- [ ] ✓ Stream status indicators visible (top-right corner)
- [ ] ✓ FPS counter showing (should reach 14-15)
- [ ] ✓ No error messages in status logs

**Browser Console Check (F12):**
- [ ] Open Developer Tools (F12)
- [ ] Switch to Console tab
- [ ] Should see: "✅ WebSocket connected"
- [ ] Should see: "📩 Welcome: Stream connected successfully"
- [ ] No red error messages

---

### Backend Verification

**Check Terminal 1 (backend) for these logs:**

- [ ] ✓ "INFO: WebSocket connection attempt"
- [ ] ✓ "INFO: WebSocket authenticated: user Brad"
- [ ] ✓ "INFO: WebSocket accepted for user Brad"
- [ ] ✓ "INFO: Session created: <uuid> (total active: 1)"
- [ ] ✓ "INFO: StreamProcessor created for session"
- [ ] ✓ "INFO: StreamProcessor started for session"
- [ ] ✓ "INFO: Processing loop started for session"

**After 10-15 seconds, should see frame processing:**
- [ ] ✓ Periodic logs: "Session <id>: Frame #100, FPS: 15.x, Detections: X"

---

### API Health Check

**Open Terminal 3 (NEW PowerShell):**

```bash
# Test WebSocket service health
curl http://localhost:8000/stream/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "service": "realtime_streaming",
  "websocket_endpoint": "/ws/stream",
  "stats": {
    "active_sessions": 1,
    "total_frames_received": 150,
    "total_detections": 0,
    "recording_sessions": 0
  }
}
```

- [ ] ✓ Status is "healthy"
- [ ] ✓ Active sessions: 1
- [ ] ✓ Frames being received

```bash
# List active sessions
curl http://localhost:8000/stream/sessions
```

- [ ] ✓ Shows 1 active session
- [ ] ✓ Session details visible

---

## 🧪 Detection Test

### Test 1: Real Knife Detection

```
Step 1: Hold a knife in front of camera
Step 2: Keep it in frame for 3-5 seconds
Step 3: Observe results
```

**Expected behavior:**
- [ ] ✓ Video border flashes red
- [ ] ✓ Status log shows: "🚨 KNIFE detected at [time] - Confidence: XX%"
- [ ] ✓ Recording indicator (red pulsing dot) appears
- [ ] ✓ Backend logs show detection details

**Backend should show:**
```
INFO: Session <id>: Frame #X, FPS: 15.x, Detections: 1, Processing: XXms
INFO: Recording started for session <id>: ./recordings/...mp4
```
- [ ] ✓ Backend confirms detection
- [ ] ✓ Recording started message

### Test 2: Verify Recording File

```bash
# Check recordings directory
ls backend/recordings/
```

**Expected:**
- [ ] ✓ New .mp4 file created
- [ ] ✓ Filename format: `<session-id>_<timestamp>.mp4`
- [ ] ✓ File size > 0 (recording has data)

### Test 3: Recording Continues

```
Step 1: Keep knife in view
Step 2: Watch recording indicator stay active
Step 3: Remove knife from view
Step 4: Wait 30 seconds
```

**Expected:**
- [ ] ✓ Recording indicator stays visible while knife present
- [ ] ✓ Recording indicator disappears 30 seconds after knife removed
- [ ] ✓ Backend logs: "Recording stopped"

---

## 🎯 Performance Metrics

### Target Metrics

**Frontend:**
- [ ] FPS counter: **14-16 FPS** (green)
- [ ] Browser CPU: **<30%**
- [ ] No frame drops or stuttering
- [ ] Smooth video playback

**Backend:**
- [ ] Processing time: **<100ms per frame**
- [ ] CPU usage: **<50%** (4-core system)
- [ ] Memory: **<500MB per session**
- [ ] Queue size: **0-5 frames**

**Network:**
- [ ] WebSocket connection: **OPEN**
- [ ] No disconnections
- [ ] Latency: **<100ms**

---

## ✅ Success Criteria

**System is working correctly if ALL of these are true:**

- [x] Backend server running without errors
- [x] Frontend accessible at localhost:3000
- [x] Login successful
- [x] Camera feed active
- [x] WebSocket connected
- [x] FPS counter showing 14-16
- [x] Detection works (knife appears → alert shows)
- [x] Recording starts on detection
- [x] Recording file saved to disk
- [x] No errors in browser console
- [x] No errors in backend logs
- [x] Performance within target metrics

---

## 🐛 Troubleshooting

If any checks fail, see:
- **Quick fixes:** `START_HERE.md`
- **Detailed guide:** `WEBSOCKET_QUICKSTART.md`
- **Technical details:** `WEBSOCKET_IMPLEMENTATION_STATUS.md`

---

## 🎊 All Checks Passed?

**Congratulations! Your real-time threat detection system is operational!**

### What You Have:
✅ WebSocket streaming at 15 FPS  
✅ Real-time knife detection (<100ms latency)  
✅ Automatic video recording  
✅ 5-minute idle timeout  
✅ Session management  

### Next Steps:
1. **Improve accuracy:** Train custom model (`ai/README.md`)
2. **Deploy:** Use Docker for production (`backend/README.md`)
3. **Monitor:** Set up Prometheus/Grafana
4. **Extend:** Add RTSP support for drones

---

**Need help?** Refer to the documentation in the root directory.

**System working?** Start testing with different scenarios! 🎉

