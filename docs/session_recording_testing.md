# 4D Session & Recording Flow Testing Guide

## Overview

Comprehensive testing guide for the 4D Session & Recording flow, covering session tracking, clip recording with pre-buffer, metadata verification, and cleanup.

## Test Coverage

### Core Functionality
1. **Session Creation** - Verify session created on login
2. **Detection & Recording** - Verify detection triggers recording
3. **Metadata Accuracy** - Verify labels and bounding boxes correct
4. **Clip Querying** - Verify clips can be retrieved
5. **Unharmful Deletion** - Verify low confidence clips deleted
6. **Accuracy Benchmark** - Verify >90% accuracy over 10 runs

### What is "4D"?

The 4D refers to the four dimensions of data tracked:
1. **Spatial (X,Y)** - Bounding box coordinates of detected threats
2. **Temporal (Time)** - When detection occurred (timestamp)
3. **Confidence (Score)** - Detection confidence percentage
4. **Classification (Label)** - Threat type (knife, weapon, etc.)

## Automated Tests

### Running Session & Recording Tests

```bash
# Install dependencies
cd backend
pip install -r requirements-dev.txt

# Run all session/recording tests
pytest tests/test_session_recording.py -v

# Run specific test class
pytest tests/test_session_recording.py::TestSessionRecordingFlow -v

# Run complete E2E flow test
pytest tests/test_session_recording.py::TestCompleteFlow::test_complete_detection_recording_flow -v

# Run accuracy benchmark
pytest tests/test_session_recording.py::TestAccuracyBenchmark::test_detection_accuracy_10_runs -v
```

### Test Classes

#### 1. `TestSessionRecordingFlow`
Tests basic session and recording functionality:
- **test_01_create_session_on_login** - Session created on auth
- **test_02_detection_creates_clip_record** - Clip saved to database
- **test_03_recording_metadata_accuracy** - Labels and locations correct
- **test_04_query_user_clips** - User can retrieve their clips
- **test_05_delete_low_confidence_clips** - Low confidence clips removed

#### 2. `TestAccuracyBenchmark`
Tests detection accuracy requirements:
- **test_detection_accuracy_10_runs** - 10 detection runs, >90% accuracy

#### 3. `TestPreBufferRecording`
Tests pre-buffer functionality:
- **test_recording_includes_prebuffer** - Recording starts before detection

#### 4. `TestSessionCleanup`
Tests cleanup processes:
- **test_session_ends_properly** - Sessions end cleanly
- **test_unharmful_clip_identification** - Unharmful clips identified

#### 5. `TestCompleteFlow`
Complete end-to-end test:
- **test_complete_detection_recording_flow** - Full workflow validation

### Expected Output

```
========================= test session starts ==========================
collected 10 items

tests/test_session_recording.py::TestSessionRecordingFlow::test_01_create_session_on_login PASSED
tests/test_session_recording.py::TestSessionRecordingFlow::test_02_detection_creates_clip_record PASSED
  ✓ Detection created: knife at 94.3% confidence

tests/test_session_recording.py::TestSessionRecordingFlow::test_03_recording_metadata_accuracy PASSED
  ✓ Valid bounding box: (120, 85) -> (450, 380)

tests/test_session_recording.py::TestSessionRecordingFlow::test_04_query_user_clips PASSED
  ✓ Found 3 clip(s) for current session

tests/test_session_recording.py::TestSessionRecordingFlow::test_05_delete_low_confidence_clips PASSED

tests/test_session_recording.py::TestAccuracyBenchmark::test_detection_accuracy_10_runs PASSED
============================================================
Running 10 detection accuracy tests...
============================================================
Run  1/10: ✓ PASS | Confidence: 94.3% | Latency: 687ms
Run  2/10: ✓ PASS | Confidence: 92.8% | Latency: 702ms
Run  3/10: ✓ PASS | Confidence: 95.1% | Latency: 691ms
Run  4/10: ✓ PASS | Confidence: 93.5% | Latency: 698ms
Run  5/10: ✓ PASS | Confidence: 94.7% | Latency: 689ms
Run  6/10: ✓ PASS | Confidence: 93.2% | Latency: 705ms
Run  7/10: ✓ PASS | Confidence: 95.8% | Latency: 683ms
Run  8/10: ✓ PASS | Confidence: 94.1% | Latency: 694ms
Run  9/10: ✓ PASS | Confidence: 93.9% | Latency: 700ms
Run 10/10: ✓ PASS | Confidence: 94.6% | Latency: 692ms

============================================================
ACCURACY RESULTS
============================================================
Successful detections: 10/10
Accuracy: 100.0%
Average latency: 694ms
Min latency: 683ms
Max latency: 705ms
============================================================

✓ Accuracy test PASSED: 100.0% >= 90.0%
✓ Latency test PASSED: 694ms < 1000ms

tests/test_session_recording.py::TestCompleteFlow::test_complete_detection_recording_flow PASSED
============================================================
COMPLETE E2E SESSION & RECORDING FLOW TEST
============================================================

[1/5] Verifying authentication...
✓ Authenticated successfully

[2/5] Triggering knife detection...
✓ Knife detected: 94.3% confidence in 687ms

[3/5] Verifying recording triggered...
✓ Recording processing time elapsed

[4/5] Querying user clips...
✓ Found 1 clip(s)

[5/5] Verifying clip metadata...
✓ Clip ID: 550e8400...
✓ Start time: 2025-11-23T10:30:00Z
✓ File path: /recordings/session_20251123_103000.mp4
✓ Confidence: 94.3%
✓ Label: knife
✓ Location: (120, 85) -> (450, 380)

============================================================
✓ COMPLETE E2E FLOW TEST PASSED
============================================================

========================== 10 passed in 45.67s ==========================
```

## Manual Testing

### Test 1: Session Creation

**Steps:**
1. Login to application
2. Open browser console
3. Check localStorage: `localStorage.getItem('zook_token')`

**Expected:**
- JWT token present
- Token is valid (not expired)
- Session created in backend database

**Verification:**
```bash
# Query database for active sessions
psql -d zook -c "SELECT id, user_id, start_time, is_active FROM stream_sessions WHERE is_active = true ORDER BY start_time DESC LIMIT 5;"
```

### Test 2: Detection Triggers Recording

**Steps:**
1. Login and start scanning
2. Show knife to camera
3. Wait for detection (red border pulse)
4. Check "Ask Zook:" search for "clips from today"

**Expected:**
- Detection occurs with >90% confidence
- Recording starts automatically
- Clip appears in search results
- Clip has correct metadata (time, confidence, file path)

**Verification:**
```javascript
// In browser console
const response = await fetch('http://localhost:8000/query', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('zook_token')}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ prompt: 'show clips from today' })
});
const data = await response.json();
console.log('Clips:', data.results);
```

### Test 3: Metadata Accuracy (4D Verification)

**Steps:**
1. Trigger detection with knife
2. Query for clip
3. Verify all 4 dimensions of data

**Expected 4D Data:**
1. **Spatial (X,Y)**: Bounding box coordinates
   - `bbox.x1`, `bbox.y1`, `bbox.x2`, `bbox.y2`
   - Values within image bounds (0-640 for YOLO default)
2. **Temporal (Time)**: Timestamp
   - `start_time` and `end_time` in ISO format
   - Times are recent and correct
3. **Confidence (Score)**: Detection confidence
   - `yolo_confidence` >= 0.90 (90%)
   - `clip_confidence` >= 0.90 if validated
4. **Classification (Label)**: Threat type
   - `type` = "knife" or "weapon"
   - Correct classification

**Verification:**
```javascript
// Check clip metadata
const clip = data.results[0];
console.log('4D Metadata Verification:');
console.log('1. Spatial:', clip.bbox);  // Should have x1, y1, x2, y2
console.log('2. Temporal:', clip.start_time, clip.end_time);
console.log('3. Confidence:', clip.yolo_confidence, clip.clip_confidence);
console.log('4. Label:', clip.type || 'knife');  // From threats array
```

### Test 4: Pre-Buffer Recording

**Steps:**
1. Start scanning (camera active)
2. Wait 10 seconds (pre-buffer fills)
3. Show knife to camera
4. Recording should include 10 seconds before detection

**Expected:**
- Recording duration > detection time
- Pre-buffer frames included in video
- Video starts before knife appeared

**Verification:**
- Download clip and check video duration
- Should be ~1-2 minutes (detection + grace period)
- Should include frames before knife appeared

### Test 5: Delete Unharmful Clips

**Steps:**
1. Trigger low confidence detection (<90%)
2. Wait for CLIP validation (post-disconnect or scheduled)
3. Check if clip was deleted

**Expected:**
- Clips with YOLO confidence <90% are validated
- If CLIP confidence also <90%, clip is deleted
- Database record soft-deleted (`is_deleted = true`)
- Physical file removed from disk

**Verification:**
```bash
# Check for deleted clips in database
psql -d zook -c "SELECT id, yolo_confidence, clip_confidence, is_deleted, deleted_at FROM clips WHERE is_deleted = true ORDER BY deleted_at DESC LIMIT 5;"

# Check recordings directory
ls -lah backend/recordings/
```

### Test 6: Accuracy Benchmark (Manual)

**Steps:**
1. Prepare 10 knife test images
2. Run detection on each image
3. Record results (pass/fail)
4. Calculate accuracy

**Expected:**
- At least 9/10 detections successful (90% accuracy)
- Average confidence >90%
- Average latency <1000ms

**Manual Testing Script:**
```bash
cd backend
python test_detection.py --dir tests/fixtures/
```

## Performance Requirements

| Metric | Target | Measured |
|--------|--------|----------|
| Detection Accuracy | ≥90% | Check in test output |
| Detection Latency | <1000ms | Check in test output |
| Recording Start Time | <2s after detection | Manual verification |
| Query Response Time | <500ms | Chrome DevTools |
| Clip Deletion Time | <10s (post-session) | Background job |

## Data Verification

### Session Table (stream_sessions)

Required fields:
- `id` (UUID)
- `user_id` (UUID, foreign key to users)
- `start_time` (timestamp)
- `end_time` (timestamp, nullable)
- `total_frames` (integer)
- `total_detections` (integer)
- `max_yolo_confidence` (float)
- `is_active` (boolean)
- `termination_reason` (string)

**Verification Query:**
```sql
SELECT 
  id,
  user_id,
  start_time,
  end_time,
  total_frames,
  total_detections,
  max_yolo_confidence,
  is_active,
  termination_reason
FROM stream_sessions
WHERE user_id = (SELECT id FROM users WHERE username = 'test_recording_user')
ORDER BY start_time DESC
LIMIT 5;
```

### Clips Table

Required fields:
- `id` (UUID)
- `stream_session_id` (UUID, foreign key)
- `file_path` (string)
- `start_time` (timestamp)
- `end_time` (timestamp, nullable)
- `yolo_confidence` (float)
- `clip_confidence` (float, nullable)
- `is_harmful` (boolean)
- `is_deleted` (boolean)
- `deleted_at` (timestamp, nullable)

**Verification Query:**
```sql
SELECT 
  c.id,
  c.stream_session_id,
  c.file_path,
  c.start_time,
  c.yolo_confidence,
  c.clip_confidence,
  c.is_harmful,
  c.is_deleted,
  ss.user_id
FROM clips c
JOIN stream_sessions ss ON c.stream_session_id = ss.id
WHERE ss.user_id = (SELECT id FROM users WHERE username = 'test_recording_user')
ORDER BY c.start_time DESC
LIMIT 10;
```

## Troubleshooting

### Clips Not Being Created

**Symptoms:**
- Detection occurs but no clips in database
- Query returns 0 results

**Fixes:**
1. Check WebSocket connection (for streaming mode)
2. Verify RecordingManager is enabled
3. Check logs for errors: `tail -f backend/logs/app.log`
4. Verify database connection
5. Check disk space for recordings

### Incorrect Metadata

**Symptoms:**
- Bounding boxes are null or invalid
- Timestamps are wrong
- Confidence scores don't match

**Fixes:**
1. Verify YOLO model is loaded correctly
2. Check detection response format
3. Verify timezone settings (should be UTC)
4. Check for data pipeline errors

### Low Accuracy (<90%)

**Symptoms:**
- Multiple failed detections in accuracy test
- Accuracy below 90% threshold

**Fixes:**
1. Check test image quality (should be clear knife images)
2. Verify model is not overloaded (CPU/GPU usage)
3. Check lighting conditions in test images
4. Verify confidence threshold is set to 0.90
5. Consider retraining model with more data

### Clips Not Being Deleted

**Symptoms:**
- Low confidence clips remain in database
- `is_deleted` stays false

**Fixes:**
1. Verify cleanup scheduler is running
2. Check scheduler logs
3. Manually trigger cleanup: restart backend
4. Verify CLIP model is loaded
5. Check clip validation logic

## Success Criteria

✅ **Session created on login**  
✅ **Detection triggers clip creation**  
✅ **Metadata includes all 4D data (spatial, temporal, confidence, label)**  
✅ **Bounding boxes are valid coordinates**  
✅ **Clips can be queried by user**  
✅ **Low confidence clips are deleted**  
✅ **Accuracy ≥90% over 10 runs**  
✅ **Average latency <1000ms**  
✅ **Pre-buffer included in recordings**  
✅ **Cleanup scheduler runs successfully**  

## Integration with Existing Tests

These tests build on the foundation from:
- `/docs/testing.md` - Main E2E testing guide
- `/backend/tests/test_e2e_detection.py` - Basic detection tests
- `/backend/tests/test_edge_cases.py` - Error handling tests

The session & recording tests add:
- Database verification
- Multi-run accuracy benchmarks
- Metadata validation
- Cleanup testing
- Complete flow integration

## Next Steps

After completing these tests:
1. Run full test suite: `pytest tests/ -v`
2. Verify all tests pass
3. Check code coverage: `pytest tests/ --cov=app`
4. Test with real camera in UI
5. Perform load testing with multiple concurrent sessions
6. Test cleanup scheduler over 24+ hours
7. Verify disk space management

## Contact

For issues with session/recording tests:
- Check backend logs: `tail -f backend/logs/app.log`
- Check database: `psql -d zook`
- See main docs: `/docs/testing.md`
- See recording docs: `/RECORDING_MANAGER_INTEGRATION.md`

