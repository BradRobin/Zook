"""
Recording Manager for threat detection video capture.

Handles video recording when threats are detected, including starting/stopping
recordings, saving to MP4 format, and automatic cleanup of old recordings.
"""
import asyncio
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List
import cv2
import numpy as np
from PIL import Image
from io import BytesIO

logger = logging.getLogger(__name__)


class VideoRecorder:
    """
    Records video frames to MP4 file.
    
    Uses OpenCV VideoWriter for H.264 encoding.
    """
    
    def __init__(
        self,
        output_path: str,
        fps: int = 15,
        resolution: tuple = (640, 640),
        bitrate: int = 1000000  # 1 Mbps
    ):
        """
        Initialize video recorder.
        
        Args:
            output_path: Path to save MP4 file
            fps: Frames per second
            resolution: Video resolution (width, height)
            bitrate: Target bitrate in bits per second
        """
        self.output_path = output_path
        self.fps = fps
        self.resolution = resolution
        self.bitrate = bitrate
        
        # Create directory if needed
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize VideoWriter
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # MP4 codec
        self.writer = cv2.VideoWriter(
            output_path,
            fourcc,
            fps,
            resolution
        )
        
        self.frame_count = 0
        self.start_time = datetime.utcnow()
        self.is_recording = True
        
        if not self.writer.isOpened():
            raise RuntimeError(f"Failed to open video writer: {output_path}")
        
        logger.info(f"VideoRecorder started: {output_path} ({fps}fps, {resolution})")
    
    def add_frame(self, frame_bytes: bytes) -> bool:
        """
        Add a frame to the recording.
        
        Args:
            frame_bytes: JPEG frame data
            
        Returns:
            True if frame added successfully
        """
        try:
            # Convert JPEG bytes to numpy array
            image = Image.open(BytesIO(frame_bytes))
            frame = np.array(image)
            
            # Convert RGB to BGR (OpenCV format)
            if len(frame.shape) == 3 and frame.shape[2] == 3:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            # Resize if needed
            if frame.shape[:2] != self.resolution[::-1]:  # height, width
                frame = cv2.resize(frame, self.resolution)
            
            # Write frame
            self.writer.write(frame)
            self.frame_count += 1
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding frame to recording: {e}")
            return False
    
    def stop(self):
        """Stop recording and close file."""
        if self.is_recording:
            self.is_recording = False
            self.writer.release()
            
            duration = (datetime.utcnow() - self.start_time).total_seconds()
            file_size = os.path.getsize(self.output_path) / (1024 * 1024)  # MB
            
            logger.info(
                f"Recording stopped: {self.output_path} "
                f"({self.frame_count} frames, {duration:.1f}s, {file_size:.2f}MB)"
            )
    
    def __del__(self):
        """Ensure video writer is released."""
        if hasattr(self, 'writer') and self.writer is not None:
            self.writer.release()


class RecordingManager:
    """
    Manages video recordings for threat detection sessions.
    
    Handles starting/stopping recordings, maintaining recording state,
    and cleaning up old recordings.
    """
    
    def __init__(
        self,
        recordings_dir: str = "./recordings",
        retention_days: int = 7,
        grace_period_seconds: int = 30
    ):
        """
        Initialize recording manager.
        
        Args:
            recordings_dir: Directory to store recordings
            retention_days: Days to keep recordings before deletion
            grace_period_seconds: Seconds to continue recording after last detection
        """
        self.recordings_dir = Path(recordings_dir)
        self.recordings_dir.mkdir(parents=True, exist_ok=True)
        
        self.retention_days = retention_days
        self.grace_period_seconds = grace_period_seconds
        
        self.active_recordings: dict[str, VideoRecorder] = {}
        self.last_detection_times: dict[str, datetime] = {}
        
        logger.info(
            f"RecordingManager initialized: {recordings_dir} "
            f"(retention: {retention_days} days, grace: {grace_period_seconds}s)"
        )
    
    def start_recording(
        self,
        session_id: str,
        detection_data: Optional[dict] = None
    ) -> str:
        """
        Start recording for a session.
        
        Args:
            session_id: Session ID
            detection_data: Optional detection information
            
        Returns:
            Path to recording file
        """
        # Check if already recording
        if session_id in self.active_recordings:
            # Update last detection time
            self.last_detection_times[session_id] = datetime.utcnow()
            return self.active_recordings[session_id].output_path
        
        # Create recording filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{session_id}_{timestamp}.mp4"
        output_path = str(self.recordings_dir / filename)
        
        try:
            # Create video recorder
            recorder = VideoRecorder(output_path, fps=15, resolution=(640, 640))
            self.active_recordings[session_id] = recorder
            self.last_detection_times[session_id] = datetime.utcnow()
            
            logger.info(f"Recording started for session {session_id}: {output_path}")
            
            # Save metadata
            self._save_metadata(session_id, detection_data)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to start recording for session {session_id}: {e}")
            raise
    
    def add_frame(self, session_id: str, frame_bytes: bytes) -> bool:
        """
        Add a frame to active recording.
        
        Args:
            session_id: Session ID
            frame_bytes: JPEG frame data
            
        Returns:
            True if frame added, False if not recording
        """
        recorder = self.active_recordings.get(session_id)
        if recorder and recorder.is_recording:
            return recorder.add_frame(frame_bytes)
        return False
    
    def update_detection(self, session_id: str):
        """
        Update last detection time for a session.
        
        Resets the grace period timer.
        
        Args:
            session_id: Session ID
        """
        if session_id in self.active_recordings:
            self.last_detection_times[session_id] = datetime.utcnow()
    
    def should_stop_recording(self, session_id: str) -> bool:
        """
        Check if recording should stop due to grace period expiry.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if grace period has expired
        """
        if session_id not in self.last_detection_times:
            return False
        
        last_detection = self.last_detection_times[session_id]
        elapsed = (datetime.utcnow() - last_detection).total_seconds()
        
        return elapsed > self.grace_period_seconds
    
    def stop_recording(self, session_id: str) -> Optional[str]:
        """
        Stop recording for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Path to saved recording file, or None if not recording
        """
        recorder = self.active_recordings.pop(session_id, None)
        self.last_detection_times.pop(session_id, None)
        
        if recorder:
            output_path = recorder.output_path
            recorder.stop()
            logger.info(f"Recording stopped for session {session_id}")
            return output_path
        
        return None
    
    def is_recording(self, session_id: str) -> bool:
        """Check if session is currently recording."""
        return session_id in self.active_recordings
    
    def get_recording_path(self, session_id: str) -> Optional[str]:
        """Get path to active recording."""
        recorder = self.active_recordings.get(session_id)
        return recorder.output_path if recorder else None
    
    def _save_metadata(self, session_id: str, detection_data: Optional[dict]):
        """Save detection metadata alongside recording."""
        if detection_data:
            recorder = self.active_recordings.get(session_id)
            if recorder:
                metadata_path = recorder.output_path.replace('.mp4', '_metadata.json')
                try:
                    import json
                    with open(metadata_path, 'w') as f:
                        json.dump({
                            'session_id': session_id,
                            'start_time': recorder.start_time.isoformat(),
                            'detection_data': detection_data
                        }, f, indent=2)
                except Exception as e:
                    logger.error(f"Failed to save metadata: {e}")
    
    async def cleanup_old_recordings(self):
        """
        Delete recordings older than retention period.
        
        Runs as a background task.
        """
        logger.info("Starting recording cleanup task")
        
        while True:
            try:
                # Check every hour
                await asyncio.sleep(3600)
                
                cutoff_time = datetime.utcnow() - timedelta(days=self.retention_days)
                deleted_count = 0
                
                # Scan recordings directory
                for file_path in self.recordings_dir.glob("*.mp4"):
                    try:
                        # Check file modification time
                        mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        
                        if mtime < cutoff_time:
                            # Delete old recording
                            file_size = file_path.stat().st_size / (1024 * 1024)
                            file_path.unlink()
                            deleted_count += 1
                            
                            # Also delete metadata if exists
                            metadata_path = file_path.with_suffix('.json')
                            if metadata_path.exists():
                                metadata_path.unlink()
                            
                            logger.info(
                                f"Deleted old recording: {file_path.name} "
                                f"({file_size:.2f}MB, age: {(datetime.utcnow() - mtime).days} days)"
                            )
                    
                    except Exception as e:
                        logger.error(f"Error deleting {file_path}: {e}")
                
                if deleted_count > 0:
                    logger.info(f"Cleanup complete: {deleted_count} recordings deleted")
                
            except Exception as e:
                logger.error(f"Cleanup task error: {e}", exc_info=True)


# Global recording manager instance
_recording_manager: Optional[RecordingManager] = None


def get_recording_manager() -> RecordingManager:
    """Get or create the global recording manager instance."""
    global _recording_manager
    if _recording_manager is None:
        _recording_manager = RecordingManager()
        
        # Start cleanup task
        asyncio.create_task(_recording_manager.cleanup_old_recordings())
    
    return _recording_manager

