"""
Stream Frame Processor for real-time video detection.

Handles frame downsampling, async processing queue, and detection coordination.
"""
import asyncio
import logging
import time
from typing import Optional, Callable
from datetime import datetime

from .session_manager import StreamSession
from .detector import get_detector

logger = logging.getLogger(__name__)


class FrameDownsampler:
    """
    Intelligently downsample video frames to target FPS.
    
    Frontend may send 30fps, we downsample to 15fps to reduce processing load
    while maintaining real-time detection capability.
    """
    
    def __init__(self, target_fps: int = 15):
        """
        Initialize downsampler.
        
        Args:
            target_fps: Target frames per second to process
        """
        self.target_fps = target_fps
        self.frame_interval = 1.0 / target_fps  # seconds between frames
        self.last_frame_time = 0.0
        self.total_frames_received = 0
        self.frames_processed = 0
        self.frames_skipped = 0
        
        logger.info(f"FrameDownsampler initialized: target {target_fps} FPS ({self.frame_interval*1000:.1f}ms interval)")
    
    def should_process(self, current_time: Optional[float] = None) -> bool:
        """
        Determine if current frame should be processed based on target FPS.
        
        Args:
            current_time: Current time in seconds (uses time.time() if None)
            
        Returns:
            True if frame should be processed, False if should skip
        """
        if current_time is None:
            current_time = time.time()
        
        self.total_frames_received += 1
        
        # Check if enough time has passed since last frame
        time_since_last = current_time - self.last_frame_time
        
        if time_since_last >= self.frame_interval or self.last_frame_time == 0:
            self.last_frame_time = current_time
            self.frames_processed += 1
            return True
        else:
            self.frames_skipped += 1
            return False
    
    def get_actual_fps(self) -> float:
        """Calculate actual processing FPS."""
        if self.last_frame_time == 0:
            return 0.0
        elapsed = time.time() - (self.last_frame_time - (self.frames_processed * self.frame_interval))
        if elapsed > 0:
            return self.frames_processed / elapsed
        return 0.0
    
    def get_stats(self) -> dict:
        """Get downsampler statistics."""
        return {
            'target_fps': self.target_fps,
            'actual_fps': round(self.get_actual_fps(), 2),
            'total_received': self.total_frames_received,
            'processed': self.frames_processed,
            'skipped': self.frames_skipped,
            'skip_rate': round(self.frames_skipped / max(1, self.total_frames_received) * 100, 1)
        }


class StreamProcessor:
    """
    Processes frames from a streaming session.
    
    Handles downsampling, detection, and result delivery via WebSocket.
    Runs as an async background task per session.
    """
    
    def __init__(
        self,
        session: StreamSession,
        target_fps: int = 15,
        on_detection: Optional[Callable] = None
    ):
        """
        Initialize stream processor.
        
        Args:
            session: StreamSession to process
            target_fps: Target processing FPS
            on_detection: Optional callback when detection occurs
        """
        self.session = session
        self.downsampler = FrameDownsampler(target_fps)
        self.on_detection = on_detection
        self.detector = get_detector()
        self.is_running = False
        self._process_task: Optional[asyncio.Task] = None
        
        logger.info(f"StreamProcessor created for session {session.session_id}")
    
    async def start(self):
        """Start the frame processing loop."""
        if self.is_running:
            logger.warning(f"StreamProcessor already running for session {self.session.session_id}")
            return
        
        self.is_running = True
        self._process_task = asyncio.create_task(self._process_loop())
        logger.info(f"StreamProcessor started for session {self.session.session_id}")
    
    async def stop(self):
        """Stop the frame processing loop."""
        self.is_running = False
        
        if self._process_task and not self._process_task.done():
            self._process_task.cancel()
            try:
                await self._process_task
            except asyncio.CancelledError:
                pass
        
        logger.info(f"StreamProcessor stopped for session {self.session.session_id}")
    
    async def _process_loop(self):
        """
        Main processing loop.
        
        Continuously gets frames from session queue, downsamples, runs detection,
        and sends results back via WebSocket.
        """
        logger.info(f"Processing loop started for session {self.session.session_id}")
        
        while self.is_running and self.session.is_active:
            try:
                # Get next frame from queue (with timeout)
                frame_data = await self.session.get_frame(timeout=1.0)
                
                if frame_data is None:
                    # Timeout - no frame available
                    continue
                
                # Check if we should process this frame (downsampling)
                if not self.downsampler.should_process():
                    # Skip this frame to maintain target FPS
                    continue
                
                # Process frame
                await self._process_frame(frame_data)
                
            except asyncio.CancelledError:
                logger.info(f"Processing loop cancelled for session {self.session.session_id}")
                break
            except Exception as e:
                logger.error(f"Error in processing loop: {e}", exc_info=True)
                # Continue processing despite errors
                await asyncio.sleep(0.1)
        
        logger.info(f"Processing loop ended for session {self.session.session_id}")
    
    async def _process_frame(self, frame_data: dict):
        """
        Process a single frame.
        
        Args:
            frame_data: Frame data dict with 'bytes', 'timestamp', 'frame_number'
        """
        start_time = time.time()
        
        try:
            # Run detection in thread pool (CPU-bound operation)
            loop = asyncio.get_event_loop()
            threats = await loop.run_in_executor(
                None,  # Use default thread pool
                self.detector.detect_threats,
                frame_data['bytes']
            )
            
            processing_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Register detection if threats found
            if threats:
                self.session.register_detection(len(threats))
                
                # Call detection callback if provided
                if self.on_detection:
                    try:
                        await self.on_detection(self.session, threats)
                    except Exception as e:
                        logger.error(f"Detection callback error: {e}")
            
            # Send results back via WebSocket
            await self._send_result({
                'threats': [t.to_dict() for t in threats],
                'processing_time_ms': round(processing_time, 2),
                'session_id': self.session.session_id,
                'recording': self.session.is_recording,
                'fps': self.downsampler.get_actual_fps(),
                'queue_size': self.session.frame_queue.qsize(),
                'idle_minutes': round(self.session.get_idle_minutes(), 2),
                'frame_number': frame_data['frame_number'],
                'timestamp': frame_data['timestamp'].isoformat()
            })
            
            # Log periodic stats
            if frame_data['frame_number'] % 100 == 0:
                logger.info(
                    f"Session {self.session.session_id}: "
                    f"Frame #{frame_data['frame_number']}, "
                    f"FPS: {self.downsampler.get_actual_fps():.1f}, "
                    f"Detections: {self.session.total_detections}, "
                    f"Processing: {processing_time:.1f}ms"
                )
            
        except Exception as e:
            logger.error(f"Frame processing error: {e}", exc_info=True)
            
            # Send error message to client
            await self._send_error(f"Processing error: {str(e)}")
    
    async def _send_result(self, result: dict):
        """
        Send detection result to client via WebSocket.
        
        Args:
            result: Result dictionary to send as JSON
        """
        try:
            await self.session.websocket.send_json(result)
        except Exception as e:
            logger.error(f"Failed to send result: {e}")
            # WebSocket may be closed - session should be cleaned up
            self.session.is_active = False
    
    async def _send_error(self, error_message: str):
        """
        Send error message to client.
        
        Args:
            error_message: Error description
        """
        try:
            await self.session.websocket.send_json({
                'error': error_message,
                'session_id': self.session.session_id,
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"Failed to send error: {e}")
    
    def get_stats(self) -> dict:
        """Get processor statistics."""
        return {
            'session_id': self.session.session_id,
            'is_running': self.is_running,
            'downsampler': self.downsampler.get_stats(),
            'session': self.session.get_session_info()
        }


async def process_stream(
    session: StreamSession,
    target_fps: int = 15,
    on_detection: Optional[Callable] = None
) -> StreamProcessor:
    """
    Create and start a stream processor for a session.
    
    Args:
        session: StreamSession to process
        target_fps: Target processing FPS
        on_detection: Optional callback for detections
        
    Returns:
        Started StreamProcessor instance
    """
    processor = StreamProcessor(session, target_fps, on_detection)
    await processor.start()
    return processor

