# Zook End-to-End Testing Guide

## Overview

Comprehensive testing guide for manual and automated testing of the knife detection system.

## Prerequisites

### Backend Setup
1. Start PostgreSQL database (port 5432)
2. Run migrations: `cd backend && python -m app.database`
3. Start backend server: `uvicorn app.main:app --reload --port 8000`
4. Verify health: `curl http://localhost:8000/detect/health`

### Frontend Setup
1. Start UI server: `cd ui && python -m http.server 3500`
2. Open browser: `http://localhost:3500`

### Test Data
- Download sample knife images from:
  - https://www.kaggle.com/datasets/knife-detection
  - Or use your own knife photos
- Place in `backend/tests/fixtures/` directory

## Manual Testing Procedure

### Test 1: User Registration

**Steps:**
1. Navigate to `http://localhost:3500`
2. Click "Scan" button
3. In login modal, enter:
   - Username: `test_user_manual`
   - Password: `Test123!@#`
4. Check consent checkbox
5. Click "Authenticate"

**Expected Result:**
- User registered successfully
- JWT token stored in localStorage
- Redirected to dashboard with live camera feed

**Performance Check:**
- Registration should complete in <500ms
- Use Chrome DevTools Network tab to verify

**Edge Cases:**
- Try duplicate username → Should show error
- Try weak password → Should validate (if implemented)

### Test 2: Login Flow

**Steps:**
1. Logout (if logged in): `localStorage.clear()` in console
2. Refresh page
3. Click "Scan"
4. Enter existing credentials
5. Check consent checkbox
6. Click "Authenticate"

**Expected Result:**
- Login successful
- JWT token received
- Dashboard loads with camera feed

**Performance Check:**
- Login should complete in <500ms
- Check DevTools Network → `/api/login` timing

**Edge Cases:**
- Invalid password → 401 error
- Non-existent user → 401 error
- Empty fields → Form validation

### Test 3: Camera Permission

**Steps:**
1. Login to dashboard
2. Browser prompts for camera access
3. Click "Allow"

**Expected Result:**
- Camera feed appears in video element
- Feed is live (not frozen)
- "Scanning..." message in status logs

**Performance Check:**
- Camera should initialize in <2 seconds
- Check console for `getUserMedia` timing

**Edge Cases to Test:**

#### 3a. Camera Permission Denied

**Steps:**
1. Login to dashboard
2. Click "Block" on camera permission prompt

**Expected Result:**
- Error message: "Camera access denied"
- Clear instructions: "Grant camera access to continue"
- Option to retry or change permissions

**Manual Test:**
```javascript
// In console
navigator.mediaDevices.getUserMedia({ video: true })
  .catch(err => console.error("Camera error:", err.name, err.message));
```

#### 3b. No Camera Available

**Steps:**
1. Disable/disconnect camera in OS settings
2. Try to login and start scanning

**Expected Result:**
- Error: "No camera detected"
- Instructions to connect camera

### Test 4: Knife Detection (High Confidence)

**Steps:**
1. Login and grant camera access
2. Hold a real knife OR show a printed photo of a knife
3. Position in camera frame
4. Wait for detection (5 seconds for REST mode)

**Expected Result:**
- Red border pulse animation on video feed
- Log entry: `[HH:MM:SS] KNIFE DETECTED! Confidence: XX.X%`
- Confidence should be >90%
- Detection logged in status panel
- If recording enabled, clip saved

**Performance Check (Chrome DevTools):**

1. Open DevTools (F12)
2. Go to Network tab
3. Filter: `detect`
4. Observe POST request to `/detect`
5. Check timing:
   - **Total time: <1000ms** ✓
   - **Waiting (TTFB): <800ms** ✓
   - **Content Download: <100ms** ✓

**Console Logs to Verify:**
```
📸 Frame 1 captured (45.2KB)
⏱️ Request took 734ms
✅ Detection complete in 689ms
🚨 KNIFE DETECTED! Count: 1
[10:35:42] KNIFE DETECTED! Confidence: 94.3%
```

**Manual Performance Test:**
```javascript
// In browser console
async function testDetectionSpeed() {
  const canvas = document.createElement('canvas');
  const video = document.getElementById('feed');
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext('2d').drawImage(video, 0, 0);
  
  const blob = await new Promise(r => canvas.toBlob(r, 'image/jpeg', 0.8));
  const formData = new FormData();
  formData.append('image', blob, 'frame.jpg');
  
  const start = performance.now();
  const response = await fetch('http://localhost:8000/detect', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${window.zookApp.authToken}` },
    body: formData
  });
  const elapsed = performance.now() - start;
  const data = await response.json();
  
  console.log(`Latency: ${elapsed.toFixed(1)}ms`);
  console.log('Threats:', data.threats);
  return { elapsed, data };
}

// Run test
await testDetectionSpeed();
```

### Test 5: Low Confidence (<90%)

**Steps:**
1. Show an ambiguous object (e.g., pen, ruler, stick)
2. Wait for detection

**Expected Result:**
- Detection may occur with <90% confidence
- **NO red border pulse** (threshold not met)
- **NO alert logged** in status panel
- Console may show: `✓ No threats above threshold`

**Verify in Console:**
```javascript
// Monitor detection events
window.zookApp.activeDetectionService.onDetection = (threats, data) => {
  console.log('Raw detections:', threats);
  threats.forEach(t => {
    console.log(`${t.type}: ${(t.confidence*100).toFixed(1)}%`, 
      t.confidence >= 0.90 ? '→ ALERT' : '→ Ignored');
  });
};
```

### Test 6: No Threats Detected

**Steps:**
1. Show empty wall, desk, or face to camera
2. Wait for several detection cycles (30+ seconds)

**Expected Result:**
- No red border pulses
- Status logs show: "Scanning... No threats."
- Console: `✓ No threats detected`

### Test 7: Offline AI Service

**Steps:**
1. Login and start scanning
2. Stop backend server: Ctrl+C in backend terminal
3. Wait for next detection request

**Expected Result:**
- Error message: "AI offline—retry?"
- Log entry: "Detection service error: Failed to fetch"
- UI remains functional (not frozen)
- Can retry when backend restarts

**Manual Test:**
```javascript
// Simulate offline backend
const originalFetch = window.fetch;
window.fetch = (...args) => {
  if (args[0].includes('/detect')) {
    return Promise.reject(new Error('Network error: Backend offline'));
  }
  return originalFetch(...args);
};

// Restore after test
window.fetch = originalFetch;
```

### Test 8: Network Timeout

**Steps:**
1. Use Chrome DevTools to throttle network
2. DevTools → Network → Throttling → "Slow 3G"
3. Perform knife detection

**Expected Result:**
- Detection takes longer (may exceed 1s)
- Eventually completes or times out with error
- UI shows "Detecting..." status
- Error: "Request timeout" if exceeds limit

### Test 9: Token Expiration

**Steps:**
1. Login and wait 24 hours (or manually expire token)
2. Try to use detection

**Expected Result:**
- 401 Unauthorized error
- Redirected to login page
- Clear message: "Session expired. Please login again."

**Manual Test (Immediate Expiration):**
```javascript
// Corrupt token to simulate expiration
localStorage.setItem('zook_token', 'expired_token_xyz');
window.location.reload();
```

## Automated Testing

### Running Python Tests

```bash
# Install test dependencies
cd backend
pip install pytest pytest-asyncio httpx

# Run all E2E tests
pytest tests/test_e2e_detection.py -v

# Run with performance report
pytest tests/test_e2e_detection.py -v --durations=10

# Run specific test
pytest tests/test_e2e_detection.py::TestKnifeDetectionE2E::test_04_knife_detection_high_confidence -v

# Run edge case tests
pytest tests/test_edge_cases.py -v
```

### Test Output Example

```
========================= test session starts ==========================
collected 8 items

tests/test_e2e_detection.py::test_01_user_registration PASSED  [ 12%]
tests/test_e2e_detection.py::test_02_user_login PASSED         [ 25%]
tests/test_e2e_detection.py::test_03_health_check PASSED       [ 37%]
tests/test_e2e_detection.py::test_04_knife_detection_high_confidence PASSED [ 50%]
  ✓ Knife detected: 94.3% confidence
  ✓ Latency: 687.3ms
tests/test_e2e_detection.py::test_05_low_confidence_no_alert PASSED [ 62%]
tests/test_e2e_detection.py::test_06_no_threat_image PASSED    [ 75%]
tests/test_e2e_detection.py::test_07_invalid_token PASSED      [ 87%]
tests/test_e2e_detection.py::test_08_missing_authentication PASSED [100%]

========================== 8 passed in 12.34s ==========================
```

## Chrome DevTools Performance Profiling

### Network Timing Breakdown

1. **Open DevTools** (F12) → **Network** tab
2. **Filter**: `detect` or `ws/stream`
3. **Start scanning**
4. **Click on a request** to see timing details

**Key Metrics:**

| Phase | Target | Description |
|-------|--------|-------------|
| **Queueing** | <10ms | Time waiting for thread |
| **Stalled** | <20ms | Time waiting for socket |
| **DNS Lookup** | 0ms | (localhost, should be instant) |
| **Initial Connection** | <50ms | TCP handshake |
| **SSL** | 0ms | (HTTP, no SSL locally) |
| **Request Sent** | <5ms | Time sending request data |
| **Waiting (TTFB)** | **<800ms** | **Backend processing time** |
| **Content Download** | <100ms | Time receiving response |
| **Total** | **<1000ms** | **End-to-end latency** |

### Performance Tab Profiling

1. **DevTools** → **Performance** tab
2. **Click record** (circle icon)
3. **Perform detection** (show knife to camera)
4. **Stop recording** after 5-10 seconds
5. **Analyze**:
   - Frame rate should be ~15 FPS (WebSocket) or 0.2 FPS (REST/5s)
   - Main thread should not block >100ms
   - Look for red bars (long tasks)

### Memory Tab (Leak Detection)

1. **DevTools** → **Memory** tab
2. **Take snapshot** before scanning
3. **Scan for 5 minutes**
4. **Take snapshot** after scanning
5. **Compare snapshots**:
   - Memory should stabilize (not grow continuously)
   - No excessive object creation

## Expected Results Summary

| Test Case | Expected Outcome | Performance Target |
|-----------|------------------|--------------------|
| User Registration | 201 Created, JWT token | <500ms |
| User Login | 200 OK, JWT token | <500ms |
| Camera Access | Video stream active | <2000ms |
| Knife Detection (>90%) | Red border + log entry | <1000ms |
| Low Confidence (<90%) | No alert | <1000ms |
| No Threat | No alert | <1000ms |
| Offline AI | Error message, graceful handling | N/A |
| Invalid Token | 401 Unauthorized | <100ms |
| Camera Denied | Clear error + instructions | <100ms |
| Network Timeout | Timeout error + retry option | Configurable |

## Troubleshooting

### Detection Not Working

**Symptoms:** No detections, even with knife in frame

**Fixes:**
1. Check backend health: `curl http://localhost:8000/detect/health`
2. Verify model loaded: Look for "Model: yolo11n" in health response
3. Check console for errors
4. Verify token: `localStorage.getItem('zook_token')`
5. Test with existing script: `python backend/test_detection.py`

### High Latency (>1s)

**Symptoms:** Detection takes >1000ms

**Fixes:**
1. Check CPU usage (Task Manager / Activity Monitor)
2. Verify GPU available: Model should use CUDA if available
3. Reduce image quality: Lower JPEG quality to 0.6
4. Check network: Use localhost, not remote server
5. Close other applications using GPU

### Camera Not Accessible

**Symptoms:** `getUserMedia` fails

**Fixes:**
1. Check browser permissions: Settings → Privacy → Camera
2. Verify camera not in use by other app
3. Try different browser (Chrome recommended)
4. Check HTTPS requirement (not needed for localhost)
5. Test camera: Visit https://webcamtests.com/

### False Positives

**Symptoms:** Non-knife objects detected as knives

**Fixes:**
1. Check confidence score (should be >90%)
2. Improve lighting conditions
3. Reduce clutter in frame
4. Verify model accuracy with `backend/test_detection.py`
5. Consider retraining model with more data

## Test Data Sources

### Knife Images (For Testing)
- **Kaggle**: https://www.kaggle.com/datasets/knife-detection
- **Roboflow**: https://universe.roboflow.com/weapon-detection
- **Google Images**: Search "knife side view" (public domain)

### No-Threat Images
- Office supplies
- People (face, hands)
- Empty rooms
- Natural scenes

### Ambiguous Images (Low Confidence)
- Pens, pencils
- Rulers, sticks
- Tools (screwdriver, wrench)
- Kitchen utensils (spoon, fork)

## Continuous Integration (Future)

### GitHub Actions Workflow (`.github/workflows/test.yml`)

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio
      
      - name: Run migrations
        run: |
          cd backend
          python -m app.database
      
      - name: Start backend
        run: |
          cd backend
          uvicorn app.main:app --host 0.0.0.0 --port 8000 &
          sleep 10
      
      - name: Run tests
        run: |
          cd backend
          pytest tests/ -v --tb=short
```

## Reporting Issues

When reporting bugs, include:
1. **Test case** that failed
2. **Expected result**
3. **Actual result**
4. **Screenshots/videos** (if UI issue)
5. **Console logs** (Chrome DevTools)
6. **Network timing** (DevTools Network tab)
7. **Browser/OS** versions
8. **Backend logs** (terminal output)

## Contact

For questions or issues:
- GitHub Issues: [Your repo]/issues
- Email: support@zook.ai
- Docs: /docs/PROJECT_DOCUMENTATION.md

