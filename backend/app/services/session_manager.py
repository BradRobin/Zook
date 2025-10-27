"""
Stream Session Manager for WebSocket connections.

Manages active video streaming sessions, handles timeouts, and coordinates
between WebSocket connections, frame processing, and recording.
"""
import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional
from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class StreamSession:
    """
    Represents an active video streaming session.
    
    Manages WebSocket connection, frame queue, detection state, and recording.
    Implements 5-minute idle timeout after last detection.
    """
    
    def __init__(
        self,
        session_id: str,
        user_id: str,
        websocket: WebSocket,
        db: AsyncSession,
        max_queue_size: int = 30,
        idle_timeout_seconds: int = 300  # 5 minutes
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.websocket = websocket
        self.db = db
        
        # Timing
        self.start_time = datetime.utcnow()
        self.last_activity_time = datetime.utcnow()
        self.last_detection_time: Optional[datetime] = None
        self.idle_timeout_seconds = idle_timeout_seconds
        
        # Frame processing
        self.frame_queue = asyncio.Queue(maxsize=max_queue_size)
        self.total_frames = 0
        self.processed_frames = 0
        self.dropped_frames = 0
        
        # Detection state
        self.total_detections = 0
        self.is_recording = False
        self.recording_path: Optional[str] = None
        self.recording_start_time: Optional[datetime] = None
        
        # Session state
        self.is_active = True
        self.termination_reason: Optional[str] = None
        
        logger.info(f"Session created: {session_id} for user {user_id}")
    
    async def add_frame(self, frame_bytes: bytes) -> bool:
        """
        Add a frame to the processing queue.
        
        Args:
            frame_bytes: Raw JPEG frame data
            
        Returns:
            True if frame was added, False if queue is full (frame dropped)
        """
        self.last_activity_time = datetime.utcnow()
        self.total_frames += 1
        
        try:
            # Try to add without blocking
            self.frame_queue.put_nowait({
                'bytes': frame_bytes,
                'timestamp': datetime.utcnow(),
                'frame_number': self.total_frames
            })
            return True
        except asyncio.QueueFull:
            # Queue full - drop frame to prevent memory overflow
            self.dropped_frames += 1
            if self.dropped_frames % 10 == 0:
                logger.warning(f"Session {self.session_id}: Dropped {self.dropped_frames} frames")
            return False
    
    async def get_frame(self, timeout: float = 1.0) -> Optional[Dict]:
        """
        Get next frame from queue with timeout.
        
        Args:
            timeout: Max wait time in seconds
            
        Returns:
            Frame data dict or None if timeout
        """
        try:
            frame_data = await asyncio.wait_for(
                self.frame_queue.get(),
                timeout=timeout
            )
            self.processed_frames += 1
            return frame_data
        except asyncio.TimeoutError:
            return None
    
    def register_detection(self, detection_count: int = 1):
        """
        Register that a detection occurred.
        
        Updates last detection time and resets idle timeout.
        """
        self.last_detection_time = datetime.utcnow()
        self.total_detections += detection_count
        logger.info(f"Session {self.session_id}: Detection #{self.total_detections}")
    
    def start_recording(self, recording_path: str):
        """Start recording video."""
        if not self.is_recording:
            self.is_recording = True
            self.recording_path = recording_path
            self.recording_start_time = datetime.utcnow()
            logger.info(f"Session {self.session_id}: Recording started -> {recording_path}")
    
    def stop_recording(self):
        """Stop recording video."""
        if self.is_recording:
            self.is_recording = False
            duration = (datetime.utcnow() - self.recording_start_time).total_seconds()
            logger.info(f"Session {self.session_id}: Recording stopped (duration: {duration:.1f}s)")
    
    def is_idle_timeout(self) -> bool:
        """
        Check if session has exceeded idle timeout.
        
        Returns:
            True if no detection for more than idle_timeout_seconds
        """
        if self.last_detection_time is None:
            # No detections yet - check from start time
            idle_time = (datetime.utcnow() - self.start_time).total_seconds()
        else:
            # Check from last detection
            idle_time = (datetime.utcnow() - self.last_detection_time).total_seconds()
        
        return idle_time > self.idle_timeout_seconds
    
    def get_idle_minutes(self) -> float:
        """Get minutes since last detection (or start if no detections)."""
        if self.last_detection_time is None:
            idle_time = (datetime.utcnow() - self.start_time).total_seconds()
        else:
            idle_time = (datetime.utcnow() - self.last_detection_time).total_seconds()
        
        return idle_time / 60.0
    
    def get_session_info(self) -> Dict:
        """Get session information for status messages."""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'start_time': self.start_time.isoformat(),
            'total_frames': self.total_frames,
            'processed_frames': self.processed_frames,
            'dropped_frames': self.dropped_frames,
            'total_detections': self.total_detections,
            'is_recording': self.is_recording,
            'recording_path': self.recording_path,
            'idle_minutes': round(self.get_idle_minutes(), 2),
            'queue_size': self.frame_queue.qsize(),
            'is_active': self.is_active
        }
    
    async def cleanup(self, reason: str = "normal"):
        """
        Cleanup session resources.
        
        Args:
            reason: Termination reason (timeout, disconnect, error, normal)
        """
        logger.info(f"Session {self.session_id}: Cleanup initiated (reason: {reason})")
        
        self.is_active = False
        self.termination_reason = reason
        
        # Stop recording if active
        if self.is_recording:
            self.stop_recording()
        
        # Clear frame queue
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        
        # Update database (if needed)
        # TODO: Save session to stream_sessions table
        
        logger.info(f"Session {self.session_id}: Cleanup complete")


class SessionManager:
    """
    Global manager for all active streaming sessions.
    
    Tracks sessions, monitors timeouts, and coordinates cleanup.
    """
    
    def __init__(self):
        self.sessions: Dict[str, StreamSession] = {}
        self.timeout_check_interval = 30  # Check every 30 seconds
        self._monitor_task: Optional[asyncio.Task] = None
        logger.info("SessionManager initialized")
    
    def create_session(
        self,
        user_id: str,
        websocket: WebSocket,
        db: AsyncSession
    ) -> StreamSession:
        """
        Create a new streaming session.
        
        Args:
            user_id: User ID from JWT token
            websocket: WebSocket connection
            db: Database session
            
        Returns:
            New StreamSession instance
        """
        session_id = str(uuid.uuid4())
        session = StreamSession(session_id, user_id, websocket, db)
        self.sessions[session_id] = session
        
        logger.info(f"Session created: {session_id} (total active: {len(self.sessions)})")
        
        # Start monitor if not running
        if self._monitor_task is None or self._monitor_task.done():
            self._monitor_task = asyncio.create_task(self._monitor_sessions())
        
        return session
    
    def get_session(self, session_id: str) -> Optional[StreamSession]:
        """Get session by ID."""
        return self.sessions.get(session_id)
    
    def get_user_sessions(self, user_id: str) -> list[StreamSession]:
        """Get all active sessions for a user."""
        return [s for s in self.sessions.values() if s.user_id == user_id]
    
    async def remove_session(self, session_id: str, reason: str = "normal"):
        """
        Remove and cleanup a session.
        
        Args:
            session_id: Session ID to remove
            reason: Termination reason
        """
        session = self.sessions.pop(session_id, None)
        if session:
            await session.cleanup(reason)
            logger.info(f"Session removed: {session_id} (remaining: {len(self.sessions)})")
    
    async def _monitor_sessions(self):
        """
        Background task to monitor sessions for idle timeout.
        
        Checks all sessions every 30 seconds and terminates idle ones.
        """
        logger.info("Session monitor started")
        
        while True:
            try:
                await asyncio.sleep(self.timeout_check_interval)
                
                # Check all sessions for idle timeout
                sessions_to_remove = []
                
                for session_id, session in self.sessions.items():
                    if not session.is_active:
                        sessions_to_remove.append((session_id, "inactive"))
                    elif session.is_idle_timeout():
                        logger.warning(
                            f"Session {session_id}: Idle timeout "
                            f"({session.get_idle_minutes():.1f} min without detection)"
                        )
                        sessions_to_remove.append((session_id, "timeout"))
                
                # Remove timed-out sessions
                for session_id, reason in sessions_to_remove:
                    await self.remove_session(session_id, reason)
                
                # Log status
                if len(self.sessions) > 0:
                    logger.info(f"Active sessions: {len(self.sessions)}")
                
            except Exception as e:
                logger.error(f"Session monitor error: {e}", exc_info=True)
    
    def get_stats(self) -> Dict:
        """Get statistics about all sessions."""
        total_frames = sum(s.total_frames for s in self.sessions.values())
        total_detections = sum(s.total_detections for s in self.sessions.values())
        recording_sessions = sum(1 for s in self.sessions.values() if s.is_recording)
        
        return {
            'active_sessions': len(self.sessions),
            'total_frames_received': total_frames,
            'total_detections': total_detections,
            'recording_sessions': recording_sessions
        }


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get or create the global session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager

