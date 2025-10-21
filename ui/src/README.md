# Zook MVP UI - Local Testing Guide

## Quick Start

1. **Open the UI**: Navigate to `ui/src/` and open `index.html` in your browser
2. **Test without backend**: The UI will show connection errors but still function for camera access
3. **Test with backend**: Start the MediaMTX auth server on port 8080

## Testing Checklist

### ✅ Landing Page
- [ ] Ultra-minimalist design with massive white space
- [ ] "Zook" header in large monospace font
- [ ] Subtext about AI surveillance
- [ ] Green "Scan" button (outlined style)
- [ ] Footer with Kenya Data Protection Act compliance

### ✅ Authentication Flow
- [ ] Click "Scan" opens login modal
- [ ] Username/password form with monospace styling
- [ ] Consent checkbox required
- [ ] Error handling for invalid inputs
- [ ] Cancel button closes modal

### ✅ Dashboard View
- [ ] Split-screen layout: 70% video, 30% status panel
- [ ] Live camera feed (requires camera permission)
- [ ] Monospace detection logs
- [ ] "Pause Scan" / "Resume Scan" toggle
- [ ] Settings drawer with object detection toggles

### ✅ Mobile Responsive
- [ ] Vertical stack on screens <768px
- [ ] Touch-friendly button sizes
- [ ] Readable text at mobile sizes
- [ ] Settings drawer full-width on mobile

### ✅ Threat Detection Simulation
- [ ] Random 10% chance detection every 5 seconds
- [ ] Red border pulse animation on threat
- [ ] Log entries with timestamps and confidence
- [ ] Visual feedback in status panel

## Backend Integration Notes

**Current Status**: The `/api/auth` endpoint in `mediamtx_authserver/main.go` only handles user registration (`Add_user`). For production, you'll need:

1. **Login Endpoint**: Separate endpoint that validates credentials and returns JWT token
2. **Token Verification**: Middleware to verify tokens on protected routes
3. **AI Detection**: Real YOLOv12/FastAPI service at `http://localhost:8000/detect`

**MVP Workaround**: The UI stores the registration success message as a pseudo-token in localStorage for demonstration purposes.

## File Structure
```
ui/src/
├── index.html    # Main entry point with all views
├── style.css     # Minimalist monospace styling
└── app.js        # Vanilla JS application logic
```

## Browser Compatibility
- ✅ Chrome/Edge (recommended for camera access)
- ✅ Firefox
- ✅ Safari (iOS/macOS)
- ⚠️ Camera permissions required for full functionality

## Next Steps
1. Test camera access across different browsers
2. Verify responsive design on mobile devices
3. Integrate with real backend authentication
4. Connect to actual AI detection service
5. Add WebRTC streaming via MediaMTX
