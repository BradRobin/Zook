# Zook UI - Manual E2E Testing Checklist

Quick reference for QA testers performing manual end-to-end testing.

## Prerequisites

- [ ] Backend running at `http://localhost:8000`
- [ ] UI running at `http://localhost:3500`
- [ ] Camera connected and working
- [ ] Test user credentials ready (e.g., `Brad` / `12345678`)

## Test 1: Landing Page

**Navigate to:** `http://localhost:3500`

- [ ] Page loads within 2 seconds
- [ ] "Zook" header visible in large font
- [ ] Subtext: "Live AI surveillance for safety..."
- [ ] Green "Scan" button visible
- [ ] Privacy notice visible: "Data processed locally per Kenya Data Protection Act 2019"
- [ ] "Privacy Notice" link is clickable
- [ ] Philosophy text: "Building discipline one scan at a time"

**Performance:**
- [ ] Page load time < 2s (check Network tab)

## Test 2: Privacy Notice

**Action:** Click "Privacy Notice" link

- [ ] Modal opens with privacy disclosure
- [ ] 9 sections visible (Data Controller, What Data We Collect, etc.)
- [ ] Content is scrollable
- [ ] ODPC contact information present
- [ ] "I Understand" button closes modal
- [ ] "Close" button closes modal

## Test 3: Registration/Login

**Action:** Click "Scan" button

- [ ] Login modal opens
- [ ] Username field present
- [ ] Password field present
- [ ] Consent checkbox with privacy link
- [ ] "Authenticate" button present
- [ ] "Cancel" button closes modal

**Enter credentials and submit:**

- [ ] New user: Registration successful message
- [ ] Existing user: Login successful
- [ ] Invalid credentials: Error message shown
- [ ] Modal closes on success
- [ ] Redirected to dashboard

**Performance:**
- [ ] Auth completes in <500ms

## Test 4: Camera Access

**After successful login:**

- [ ] Browser prompts for camera permission
- [ ] Click "Allow"
- [ ] Camera feed appears in video element
- [ ] Video is live (not frozen)
- [ ] "Scanning... No threats." appears in status logs

**Edge Case - Camera Denied:**

- [ ] Logout: `localStorage.clear()` in console
- [ ] Login again
- [ ] Click "Block" on camera prompt
- [ ] Error message displayed
- [ ] Clear instructions to grant access

**Performance:**
- [ ] Camera initializes in <2s

## Test 5: Dashboard UI

**Verify all elements present:**

- [ ] Live camera feed (70% width)
- [ ] Status panel (30% width)
- [ ] "Ask Zook:" search box
- [ ] Detection log area
- [ ] "Pause Scan" button
- [ ] "Settings" button
- [ ] Privacy bar at bottom of page

## Test 6: Knife Detection - High Confidence

**Preparation:**
- [ ] Hold a real knife OR
- [ ] Show printed photo of knife to camera

**Expected Results:**
- [ ] Red border pulse animation appears on video feed
- [ ] Log entry: `[HH:MM:SS] KNIFE DETECTED! Confidence: XX.X%`
- [ ] Confidence shows >90%
- [ ] Detection logged in status panel
- [ ] If recording enabled: Recording indicator shows

**Performance (Chrome DevTools):**
- [ ] Open DevTools (F12) → Network tab
- [ ] Filter: "detect"
- [ ] Total request time <1000ms
- [ ] Waiting (TTFB) <800ms

## Test 7: Low Confidence Detection

**Preparation:**
- [ ] Show pen, ruler, or stick to camera
- [ ] Wait for detection cycle

**Expected Results:**
- [ ] NO red border pulse (threshold not met)
- [ ] NO alert in status panel
- [ ] Console may show low confidence detection but ignored

## Test 8: No Threats

**Preparation:**
- [ ] Show empty wall, desk, or your face to camera
- [ ] Wait 30+ seconds

**Expected Results:**
- [ ] No red border pulses
- [ ] Status logs show: "Scanning... No threats."
- [ ] No false alarms

## Test 9: Search Functionality

**Action:** Use "Ask Zook:" search box

- [ ] Type: "show knife detections from today"
- [ ] Click "Search" button
- [ ] Search results appear
- [ ] Video players for matching clips
- [ ] Each result shows timestamp and confidence
- [ ] Videos are playable

**Test queries:**
- [ ] "clips from yesterday"
- [ ] "high confidence detections"
- [ ] "all my recordings"

## Test 10: Settings Menu

**Action:** Click "Settings" button

- [ ] Settings drawer opens from right
- [ ] Alert email field present
- [ ] Detection toggles present (Knives, Guns, Weapons)
- [ ] Privacy & Data section present
- [ ] "View Privacy Notice" button
- [ ] "Download My Data" button
- [ ] "Delete Account" button (red/danger style)
- [ ] "Close" button closes drawer

**Test Privacy Actions:**
- [ ] Click "View Privacy Notice" → Modal opens
- [ ] Click "Download My Data" → Shows message (not implemented yet)
- [ ] Click "Delete Account" → Confirmation dialog appears

## Test 11: Offline Backend

**Setup:**
- [ ] Stop backend server (Ctrl+C in terminal)
- [ ] Wait for next detection attempt

**Expected Results:**
- [ ] Error message in logs: "Detection service error..."
- [ ] UI remains functional (not frozen)
- [ ] Can restart backend and continue

## Test 12: Network Throttling

**Setup (Chrome DevTools):**
- [ ] DevTools → Network tab
- [ ] Throttling dropdown → "Slow 3G"
- [ ] Perform detection

**Expected Results:**
- [ ] Detection takes longer but eventually completes
- [ ] Error shown if timeout exceeded
- [ ] UI shows "Detecting..." status

## Test 13: Token Expiration

**Simulate expiration:**

```javascript
// In browser console
localStorage.setItem('zook_token', 'expired_token_xyz');
window.location.reload();
```

**Expected Results:**
- [ ] 401 error when attempting detection
- [ ] Redirected to login page (or error shown)
- [ ] Clear message about session expiration

## Test 14: Mobile Responsiveness

**Resize browser to mobile width (<768px):**

- [ ] Layout switches to vertical stack
- [ ] Video on top, status panel below
- [ ] All buttons remain accessible
- [ ] Text remains readable
- [ ] Settings drawer is full-width
- [ ] Privacy bar remains visible

## Test 15: Performance - Extended Session

**Run for 5 minutes:**

- [ ] Leave scanning running
- [ ] Perform several detections
- [ ] Check Chrome DevTools → Memory tab

**Expected Results:**
- [ ] Memory usage stabilizes (no continuous growth)
- [ ] No console errors
- [ ] No UI lag or freezing
- [ ] Frame rate remains stable

## Test 16: Multiple Tabs

**Open Zook in 2 browser tabs:**

- [ ] Both tabs can access camera independently
- [ ] Detections work in both tabs
- [ ] No interference between tabs
- [ ] Token works in both tabs

## Test 17: Browser Compatibility

**Test in different browsers:**

- [ ] Chrome (primary)
- [ ] Firefox
- [ ] Edge
- [ ] Safari (if available)

**Each browser should:**
- [ ] Load UI correctly
- [ ] Access camera
- [ ] Perform detections
- [ ] Display alerts properly

## Test 18: Logout and Re-login

**Actions:**
1. [ ] Scan for threats (generate some activity)
2. [ ] Logout: `localStorage.clear()` in console
3. [ ] Refresh page
4. [ ] Login again with same credentials

**Expected Results:**
- [ ] Previous session data accessible (if persisted)
- [ ] New session starts cleanly
- [ ] No errors from previous session

## Performance Benchmarks Summary

| Action | Target Time | Pass/Fail |
|--------|-------------|-----------|
| Page Load | <2s | [ ] |
| Authentication | <500ms | [ ] |
| Camera Init | <2s | [ ] |
| Detection | <1000ms | [ ] |
| UI Interaction | <100ms | [ ] |

## Common Issues & Fixes

### Camera Not Working
- Check browser permissions (Settings → Privacy → Camera)
- Ensure camera not in use by another app
- Try refreshing page
- Test camera at https://webcamtests.com/

### Detection Not Working
- Verify backend is running: `curl http://localhost:8000/detect/health`
- Check console for errors (F12)
- Verify token: `localStorage.getItem('zook_token')`
- Try re-login

### High Latency
- Check network tab (should be localhost)
- Verify backend not overloaded (CPU usage)
- Close other tabs/applications
- Check image quality setting

### UI Not Responsive
- Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
- Clear cache
- Check console for JavaScript errors

## Test Report Template

```
Test Date: _______________
Tester: _______________
Browser: _______________ Version: _______________
OS: _______________

Tests Passed: _____ / 18
Tests Failed: _____
Critical Issues: _____
Minor Issues: _____

Notes:
_______________________________________
_______________________________________
_______________________________________
```

## Sign-Off

- [ ] All critical tests passed
- [ ] Performance targets met
- [ ] No blocking issues found
- [ ] Ready for deployment

**Tester Signature:** _______________  
**Date:** _______________

