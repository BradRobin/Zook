# Recording Manager Integration Note

## API Change in RecordingManager.start_recording()

### Updated Signature

```python
def start_recording(
    self,
    session_id: str,
    stream_session_id: str,  # NEW: Database stream_session ID
    detection_data: Optional[dict] = None
) -> str:
```

### How to Use

The `StreamSession` class now provides lazy initialization of the database record:

```python
# In your code that triggers recording (e.g., when threat is detected):

# 1. Ensure DB session exists (call once, safe to call multiple times)
await stream_session._ensure_db_session()

# 2. Start recording with the DB session ID
recording_manager = get_recording_manager()
recording_path = recording_manager.start_recording(
    session_id=stream_session.session_id,
    stream_session_id=str(stream_session.db_stream_session_id),
    detection_data={'threat_type': 'knife', 'confidence': 0.95}
)

# 3. Update StreamSession state
stream_session.start_recording(recording_path)
```

### Integration Points

If you have code that triggers recording (e.g., in a detection callback), you'll need to:

1. **Call `await stream_session._ensure_db_session()`** before first recording
2. **Pass `stream_session_id`** to `start_recording()`
3. **Stop recording with DB session:** Use `await recording_manager.stop_recording(..., db=stream_session.db, max_yolo_confidence=...)`

### Example Integration in Stream Processor

If you need to integrate recording triggering in `stream_processor.py`:

```python
async def _process_frame(self, frame_data: dict):
    # ... existing detection code ...
    
    # Register detection if threats found
    if threats:
        max_confidence = max(t.confidence for t in threats)
        self.session.register_detection(len(threats), max_confidence)
        
        # Start recording on first detection
        if not self.session.is_recording:
            from .recording_manager import get_recording_manager
            
            # Ensure DB session exists
            await self.session._ensure_db_session()
            
            # Start recording
            recording_manager = get_recording_manager()
            recording_path = recording_manager.start_recording(
                session_id=self.session.session_id,
                stream_session_id=str(self.session.db_stream_session_id),
                detection_data={'threats': [t.to_dict() for t in threats]}
            )
            self.session.start_recording(recording_path)
        
        # Add frame to recording
        if self.session.is_recording:
            recording_manager.add_frame(self.session.session_id, frame_data['bytes'])
```

### Backward Compatibility Note

The existing recording system may have a different integration pattern. If recording is already working in your system, you can either:

1. **Update the existing integration** to use the new API with `stream_session_id`
2. **Make `stream_session_id` optional** with a default value for backward compatibility

### Making it Optional (if needed):

```python
def start_recording(
    self,
    session_id: str,
    stream_session_id: Optional[str] = None,  # Made optional
    detection_data: Optional[dict] = None
) -> str:
    # ... existing code ...
    
    # Only store metadata if stream_session_id provided
    if stream_session_id:
        self.recording_metadata[session_id] = {
            'stream_session_id': stream_session_id,
            'file_path': output_path,
            'start_time': recorder.start_time,
            'detection_data': detection_data
        }
```

This way, existing code continues to work, but Clip DB records will only be created when `stream_session_id` is provided.

