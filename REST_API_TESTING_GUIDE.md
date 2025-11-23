# REST API Detection - Quick Testing Guide

## Prerequisites

1. Backend server running on `http://localhost:8000`
2. Frontend server running on `http://localhost:3500`
3. Test user credentials (e.g., username: `Brad`, password: `12345678`)

## Testing REST API Mode

### Method 1: Browser Console (Quick Test)

1. **Login to the app**:
   - Navigate to `http://localhost:3500`
   - Click "Scan"
   - Enter credentials
   - Grant camera access

2. **Switch to REST mode via console**:
   ```javascript
   // Stop current scanning
   window.zookApp.stopScanning();
   
   // Switch to REST mode
   window.zookApp.detectionMode = 'rest';
   
   // Start REST API scanning
   await window.zookApp.startScanning();
   ```

3. **Watch the console for logs**:
   - `🎬 Starting REST API detection (5s intervals)`
   - `📸 Frame N captured (XX.XKB)` - every 5 seconds
   - `✅ Detection complete in XX.Xms`
   - `✓ No threats detected` or `🚨 KNIFE DETECTED!`

4. **Test with a knife (or image of knife)**:
   - Hold a knife or show a picture of a knife to the camera
   - Wait for next capture (up to 5 seconds)
   - Should see:
     - `🚨 KNIFE DETECTED! Count: 1`
     - `[HH:MM:SS] KNIFE DETECTED! Confidence: XX.X%`
     - Red border pulse on video feed
     - Log entry in status panel

### Method 2: Code Modification (Permanent Switch)

Edit `ui/src/app.js` line ~574:

```javascript
// Change from:
this.detectionMode = 'websocket';

// To:
this.detectionMode = 'rest';
```

Then refresh the page and login normally.

## Testing Checklist

### ✅ Basic Functionality
- [ ] Login successful
- [ ] Camera access granted
- [ ] Console shows "Starting REST API detection"
- [ ] Frames captured every ~5 seconds
- [ ] Frame size logged (should be 50-200KB typically)

### ✅ Detection Works
- [ ] Show knife to camera
- [ ] Wait up to 5 seconds
- [ ] Red border pulse appears
- [ ] Console log shows KNIFE DETECTED
- [ ] Log entry appears in status panel
- [ ] Confidence >= 90% shown

### ✅ Error Handling
- [ ] **Stop backend**: Should see "AI service offline" errors
- [ ] **Invalid token**: Should see "Authentication failed" and stop scanning
- [ ] **Network issues**: Should continue scanning, log errors

### ✅ Status Updates
- [ ] FPS counter shows ~0.2 (1 frame per 5 seconds)
- [ ] Processing time shown in status
- [ ] No recording indicator (REST mode doesn't record)

### ✅ Pause/Resume
- [ ] Click "Pause Scan" → stops capturing
- [ ] Console shows "REST API detection stopped"
- [ ] Click "Resume Scan" → restarts capturing

### ✅ Memory Leaks
- [ ] Leave running for 5 minutes
- [ ] Check browser memory (should be stable)
- [ ] No interval leaks after pause
- [ ] Canvas memory stable

## Expected Behavior

### Normal Operation (No Threats)
```
📸 Frame 1 captured (85.3KB)
✅ Detection complete in 156.2ms
✓ No threats detected

📸 Frame 2 captured (87.1KB)
✅ Detection complete in 142.8ms
✓ No threats detected
```

### Knife Detected
```
📸 Frame 5 captured (89.5KB)
✅ Detection complete in 178.3ms
🚨 KNIFE DETECTED! Count: 1
[10:32:15] KNIFE DETECTED! Confidence: 94.3%
```

### Backend Offline
```
📸 Frame 3 captured (86.2KB)
Detection error: Failed to fetch
AI service offline. Retrying in 5 seconds...
```

## API Request Example

When a frame is captured, the following request is sent:

```http
POST /detect HTTP/1.1
Host: localhost:8000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary...

------WebKitFormBoundary...
Content-Disposition: form-data; name="image"; filename="frame.jpg"
Content-Type: image/jpeg

<binary JPEG data>
------WebKitFormBoundary...--
```

## Comparing Modes

### WebSocket Mode (Default)
- Frames captured continuously at 30fps
- Backend processes at 15fps
- Real-time detection (<100ms latency)
- Recording supported
- Higher bandwidth usage

### REST API Mode (New)
- Frames captured every 5 seconds
- Backend processes immediately
- 5+ second latency
- No recording
- Lower bandwidth usage

## Troubleshooting

### "No frame captured, skipping detection"
- Camera not ready yet
- Wait a few seconds after login
- Check video element has loaded

### "Failed to create blob from canvas"
- Browser doesn't support Canvas.toBlob
- Try a modern browser (Chrome, Firefox, Edge)

### No red border pulse
- Detection confidence < 90%
- Check console for actual confidence value
- Try different knife or closer to camera

### "Authentication failed"
- Token expired
- Logout and login again
- Check token in localStorage

### High processing time (>500ms)
- Backend server overloaded
- GPU not available (using CPU)
- Large image resolution

## Performance Metrics

**Expected values:**
- Frame capture: < 50ms
- Network request: 20-100ms (local)
- Backend processing: 30-150ms (GPU) or 200-500ms (CPU)
- Total time: 100-300ms typically

**Bandwidth usage:**
- ~80-100KB per frame
- Every 5 seconds = ~16-20KB/s
- Compare to WebSocket: ~480-600KB/s (30fps)

## Switch Back to WebSocket

```javascript
// In browser console
window.zookApp.stopScanning();
window.zookApp.detectionMode = 'websocket';
await window.zookApp.startScanning();
```

Or refresh the page (WebSocket is default).

---

Happy testing! 🎉

