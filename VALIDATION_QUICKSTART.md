# Quick Start Guide: Validation & Auto-Delete System

## Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This will install:
- `transformers` - For CLIP model
- `apscheduler` - For scheduled cleanup
- All existing dependencies

### 2. Run Database Migration

```bash
# Using psql directly
psql -U your_username -d zook -f migrations/002_clips_tracking.sql

# Or let SQLAlchemy create tables automatically on startup
python -m uvicorn app.main:app --reload
```

### 3. Verify Installation

Check logs on startup for:
```
INFO: Database initialized successfully
INFO: Detection model initialized and ready
INFO: CLIP validator initialized successfully
INFO: CLIP model: openai/clip-vit-base-patch32
INFO: ✓ Cleanup scheduler started (runs every 6 hours)
```

## How It Works

### Automatic Flow

1. **During Streaming Session:**
   - User connects via WebSocket
   - YOLO detects threats (confidence ≥90%)
   - Recording starts automatically
   - Frames saved to MP4 file
   - StreamSession tracks statistics

2. **When Session Ends (User Disconnects):**
   - StreamSession persisted to database
   - If no clips → session deleted immediately
   - If clips exist → triggers CLIP validation (async)

3. **CLIP Validation (Background):**
   - Extracts 10 frames from each clip
   - Classifies as threat vs safe
   - If confidence <90% → marks as false positive
   - Deletes file and soft-deletes DB record
   - If confidence ≥90% → keeps as valid threat

4. **Scheduled Cleanup (Every 6 Hours):**
   - Validates old clips (>24h) not yet validated
   - Deletes sessions with no valid clips
   - Cleans up orphaned files (>7 days)
   - Logs statistics

## Manual Testing

### Test CLIP Validation Directly

```python
# In Python shell or test script
from backend.app.services.clip_validator import get_clip_validator
import asyncio

validator = get_clip_validator(device='cpu')

# Test with a video file
async def test():
    confidence, threat_count, total = await validator.validate_video_async(
        'path/to/recording.mp4',
        num_frames=10
    )
    print(f"Confidence: {confidence:.2%}")
    print(f"Threats detected: {threat_count}/{total}")
    print(f"Valid threat: {validator.is_valid_threat(confidence)}")

asyncio.run(test())
```

### Manually Trigger Cleanup

```python
# In Python shell
from backend.app.services.cleanup_scheduler import get_cleanup_scheduler
from backend.app.database import AsyncSessionLocal
import asyncio

async def manual_cleanup():
    async def db_factory():
        return AsyncSessionLocal()
    
    scheduler = get_cleanup_scheduler(db_factory)
    await scheduler.run_cleanup()

asyncio.run(manual_cleanup())
```

### Check Database Records

```sql
-- View stream sessions
SELECT id, user_id, start_time, end_time, total_detections 
FROM stream_sessions 
ORDER BY start_time DESC 
LIMIT 10;

-- View clips with validation status
SELECT id, file_path, yolo_confidence, clip_confidence, 
       is_validated, deleted_at
FROM clips 
ORDER BY created_at DESC 
LIMIT 10;

-- Count valid vs false positive clips
SELECT 
    COUNT(*) FILTER (WHERE deleted_at IS NULL) as valid_clips,
    COUNT(*) FILTER (WHERE deleted_at IS NOT NULL) as false_positives
FROM clips;

-- Check sessions with no clips (should be auto-deleted)
SELECT s.id, s.total_detections, COUNT(c.id) as clip_count
FROM stream_sessions s
LEFT JOIN clips c ON c.stream_session_id = s.id AND c.deleted_at IS NULL
GROUP BY s.id
HAVING COUNT(c.id) = 0;
```

## API Endpoints

### Check Active Sessions
```bash
curl http://localhost:8000/stream/sessions
```

Response:
```json
{
  "active_sessions": 2,
  "sessions": [
    {
      "session_id": "abc-123",
      "user_id": "user-456",
      "total_detections": 5,
      "is_recording": true,
      "idle_minutes": 0.5
    }
  ]
}
```

### Health Check
```bash
curl http://localhost:8000/stream/health
```

## Configuration

### Adjust CLIP Confidence Threshold

Edit `backend/app/services/clip_validator.py`:
```python
def __init__(
    self,
    confidence_threshold: float = 0.90  # Change this (0.0-1.0)
):
```

### Adjust Cleanup Schedule

Edit `backend/app/services/cleanup_scheduler.py`:
```python
def __init__(
    self,
    validation_age_hours: int = 24,      # Age before validation
    cleanup_interval_hours: int = 6,      # How often to run
    batch_size: int = 100                 # Records per batch
):
```

### Adjust Recording Retention

Edit `backend/app/services/recording_manager.py`:
```python
def __init__(
    self,
    retention_days: int = 7,  # Keep recordings for N days
):
```

## Monitoring

### Check Logs

```bash
# Watch logs in real-time
tail -f backend/logs/app.log

# Look for cleanup events
grep "Cleanup task completed" backend/logs/app.log

# Look for false positives
grep "False positive detected" backend/logs/app.log
```

### Key Log Messages

**Successful Validation:**
```
INFO: Valid threat confirmed: Clip def456 (YOLO: 95%, CLIP: 94%)
```

**False Positive Detected:**
```
INFO: False positive detected: Clip abc123 (YOLO: 92%, CLIP: 78%)
INFO: Deleted false positive file: /recordings/session_20231123.mp4 (12.5 MB)
```

**Cleanup Summary:**
```
INFO: Cleanup task completed
INFO: Duration: 45.2s
INFO: Clips validated: 23
INFO: Clips deleted (false positives): 5
INFO: Sessions deleted: 2
INFO: Files deleted: 7
INFO: Disk space freed: 78.5 MB
```

## Troubleshooting

### CLIP Model Download Issues

If CLIP model fails to download:
```bash
# Pre-download the model
python -c "from transformers import CLIPModel, CLIPProcessor; CLIPModel.from_pretrained('openai/clip-vit-base-patch32'); CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32')"
```

### Scheduler Not Running

Check logs for:
```
INFO: ✓ Cleanup scheduler started (runs every 6 hours)
```

If missing, check:
- APScheduler installed: `pip list | grep apscheduler`
- No errors in startup logs
- Database connection working

### Clips Not Being Validated

Check:
1. Clips exist in database: `SELECT * FROM clips LIMIT 5;`
2. Clip files exist on disk: `ls backend/recordings/`
3. Validation attempted: Check `validation_attempted_at` field
4. Errors in logs: `grep "Error validating clip" logs/app.log`

### False Positives Not Being Deleted

Check:
1. CLIP confidence threshold: Should be 0.90 (90%)
2. Validation results: Check `clip_confidence` field in database
3. File permissions: Ensure app can delete files
4. Soft delete working: Check `deleted_at` field

## Performance Considerations

### CPU Usage
- CLIP validation is CPU-intensive
- Runs in background to not block API
- Consider running on separate worker if needed

### Disk Space
- Monitor recordings directory size
- Adjust retention period if disk fills up
- Check cleanup logs for freed space

### Database
- Indexes created for fast queries
- Batch processing prevents memory issues
- Old records auto-deleted

## Next Steps

1. **Deploy to Production:**
   - Set `ENVIRONMENT=production` in `.env`
   - Use GPU for faster CLIP validation: `device='cuda'`
   - Monitor logs and disk space

2. **Fine-tune Thresholds:**
   - Adjust CLIP confidence based on false positive rate
   - Adjust validation age if needed
   - Adjust cleanup frequency

3. **Scale Up:**
   - Use dedicated CLIP validation worker
   - Implement queue for validation tasks
   - Add monitoring/alerting

Enjoy your automated validation and cleanup system! 🎉

