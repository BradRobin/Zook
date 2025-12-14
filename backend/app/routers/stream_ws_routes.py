"""
WebSocket routes for real-time video streaming and detection.

Provides WebSocket endpoint for continuous frame streaming from frontend,
processes frames at 15fps with YOLOv11, and returns detection results in real-time.
Includes post-session cleanup with CLIP validation for false positive removal.
Supports both WS and WSS (secure WebSocket) protocols.
"""
import logging
import asyncio
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..auth import decode_token
from ..services.session_manager import get_session_manager, StreamSession
from ..services.stream_processor import process_stream
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["streaming"])


async def validate_and_cleanup_clips(session: StreamSession, db: AsyncSession):
    """
    Post-session validation and cleanup of clips using CLIP model.
    
    Runs asynchronously after session ends to validate recorded clips
    and delete false positives (<90% confidence).
    
    Args:
        session: StreamSession that just ended
        db: Database session
    """
    try:
        from ..models import Clip
        from ..services.clip_validator import get_clip_validator
        import os
        
        if not session.db_stream_session_id:
            logger.warning("Session has no DB ID, skipping clip validation")
            return
        
        # Get all clips for this session
        result = await db.execute(
            select(Clip).where(
                Clip.stream_session_id == session.db_stream_session_id,
                Clip.deleted_at.is_(None)
            )
        )
        clips = result.scalars().all()
        
        if not clips:
            logger.info(f"No clips to validate for session {session.session_id}")
            return
        
        logger.info(f"Starting CLIP validation for {len(clips)} clip(s)")
        
        # Get CLIP validator
        validator = get_clip_validator(device='cpu')
        
        # Validate each clip
        for clip in clips:
            try:
                if not os.path.exists(clip.file_path):
                    logger.warning(f"Clip file not found: {clip.file_path}")
                    continue
                
                # Run CLIP validation
                avg_confidence, threat_count, total_frames = await validator.validate_video_async(
                    clip.file_path,
                    num_frames=10
                )
                
                # Update clip with validation results
                clip.clip_confidence = avg_confidence
                clip.is_validated = True
                clip.validation_attempted_at = datetime.utcnow()
                
                # If confidence < 90%, mark as false positive and delete
                if avg_confidence < 0.90:
                    logger.info(
                        f"False positive detected: Clip {clip.id} "
                        f"(CLIP confidence: {avg_confidence:.2%})"
                    )
                    
                    # Soft delete in database
                    clip.deleted_at = datetime.utcnow()
                    
                    # Delete physical file
                    try:
                        os.remove(clip.file_path)
                        logger.info(f"Deleted false positive file: {clip.file_path}")
                        
                        # Also delete metadata file if exists
                        metadata_path = clip.file_path.replace('.mp4', '_metadata.json')
                        if os.path.exists(metadata_path):
                            os.remove(metadata_path)
                    except Exception as e:
                        logger.error(f"Failed to delete file {clip.file_path}: {e}")
                else:
                    logger.info(
                        f"Valid threat confirmed: Clip {clip.id} "
                        f"(CLIP confidence: {avg_confidence:.2%})"
                    )
                
            except Exception as e:
                logger.error(f"Error validating clip {clip.id}: {e}", exc_info=True)
                clip.validation_attempted_at = datetime.utcnow()
        
        # Commit all updates
        await db.commit()
        logger.info(f"CLIP validation complete for session {session.session_id}")
        
    except Exception as e:
        logger.error(f"Error in validate_and_cleanup_clips: {e}", exc_info=True)
        await db.rollback()


async def verify_websocket_token(token: str, db: AsyncSession) -> tuple[str, str]:
    """
    Verify JWT token for WebSocket authentication.
    
    Args:
        token: JWT token from query parameter
        db: Database session
        
    Returns:
        Tuple of (user_id, username)
        
    Raises:
        Exception if token invalid
    """
    try:
        token_data = decode_token(token)
        return str(token_data.user_id), token_data.username
    except Exception as e:
        logger.error(f"WebSocket token verification failed: {e}")
        raise


def validate_websocket_origin(websocket: WebSocket) -> bool:
    """
    Validate WebSocket Origin header for security.
    
    Checks that the Origin header matches allowed CORS origins.
    Protects against unauthorized cross-origin WebSocket connections.
    
    Args:
        websocket: WebSocket connection object
        
    Returns:
        True if origin is valid, False otherwise
    """
    # Get Origin header
    origin = websocket.headers.get("origin", "")
    
    # In development without HTTPS, allow any localhost origin
    if settings.ENVIRONMENT == "development":
        if "localhost" in origin or "127.0.0.1" in origin:
            logger.debug(f"Development mode: Allowing origin {origin}")
            return True
    
    # Check against allowed CORS origins
    allowed_origins = settings.CORS_ORIGINS
    
    if origin in allowed_origins:
        logger.debug(f"Valid origin: {origin}")
        return True
    
    # If PRODUCTION_URL is set, allow it
    if settings.PRODUCTION_URL and origin == settings.PRODUCTION_URL:
        logger.debug(f"Valid production origin: {origin}")
        return True
    
    logger.warning(f"Invalid WebSocket origin: {origin}")
    return False


def log_websocket_connection_info(websocket: WebSocket):
    """
    Log WebSocket connection details for debugging and security monitoring.
    
    Args:
        websocket: WebSocket connection object
    """
    # Determine protocol (WS vs WSS)
    forwarded_proto = websocket.headers.get("x-forwarded-proto", "")
    is_secure = (
        forwarded_proto == "https" or 
        websocket.url.scheme == "wss"
    )
    protocol = "WSS (secure)" if is_secure else "WS (insecure)"
    
    # Get client info
    client_host = websocket.client.host if websocket.client else "unknown"
    origin = websocket.headers.get("origin", "none")
    user_agent = websocket.headers.get("user-agent", "unknown")
    
    logger.info(
        f"WebSocket connection: protocol={protocol}, "
        f"client={client_host}, origin={origin}, "
        f"user-agent={user_agent[:50]}..."
    )
    
    # Warn if using insecure WS in production
    if settings.ENVIRONMENT == "production" and not is_secure:
        logger.warning(
            "⚠️  Insecure WebSocket (WS) connection in production! "
            "Should use WSS. Check Cloudflare Tunnel or reverse proxy config."
        )


@router.websocket("/ws/stream")
async def stream_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT authentication token"),
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint for real-time video streaming and detection.
    
    **Connection:**
    ```
    ws://localhost:8000/ws/stream?token=YOUR_JWT_TOKEN   # Development
    wss://yourdomain.com/ws/stream?token=YOUR_JWT_TOKEN  # Production
    ```
    
    **Security:**
    - Supports both WS (development) and WSS (production) protocols
    - JWT authentication required
    - Origin validation against CORS_ORIGINS
    - X-Forwarded-Proto header support for Cloudflare Tunnel
    
    **Client → Server:**
    - Binary frames (JPEG format)
    - Sent continuously at 30fps (frontend capture rate)
    - Server downsamples to 15fps for processing
    
    **Server → Client:**
    - JSON detection results
    - Includes threats, processing time, recording status, FPS
    - Sent after each processed frame (~15 times per second)
    
    **Features:**
    - JWT authentication required
    - Real-time threat detection (<100ms latency)
    - Automatic downsampling (30fps → 15fps)
    - Session management with 5-minute idle timeout
    - Frame buffering (max 30 frames / ~2 seconds)
    - Graceful disconnect handling
    
    **Lifecycle:**
    1. Client connects with JWT token
    2. Server validates token and origin
    3. Server creates session and logs connection protocol (WS/WSS)
    4. Client streams frames continuously
    5. Server processes at 15fps, returns results
    6. After 5 min without detection → auto-disconnect
    7. Client can reconnect as needed
    
    **Example Response:**
    ```json
    {
        "threats": [{
            "type": "knife",
            "confidence": 0.95,
            "bbox": {"x1": 120, "y1": 200, "x2": 250, "y2": 400}
        }],
        "processing_time_ms": 35.2,
        "session_id": "uuid-here",
        "recording": true,
        "fps": 15.2,
        "queue_size": 3,
        "idle_minutes": 0.5,
        "frame_number": 450,
        "timestamp": "2025-10-25T10:30:45.123Z"
    }
    ```
    
    **Error Handling:**
    - Invalid token → Close with code 4001
    - Invalid origin → Close with code 4003  
    - Server error → Close with code 1011
    - Idle timeout → Close with code 1000 (normal)
    - Client disconnect → Cleanup automatically
    """
    session_manager = get_session_manager()
    session: StreamSession | None = None
    processor = None
    
    try:
        # Log connection details (protocol, client, origin)
        log_websocket_connection_info(websocket)
        
        # Validate Origin header
        if not validate_websocket_origin(websocket):
            logger.warning(
                f"WebSocket rejected: Invalid origin "
                f"{websocket.headers.get('origin', 'none')}"
            )
            await websocket.close(code=4003)  # Custom code for forbidden origin
            return
        
        # Verify JWT token
        logger.info("WebSocket connection attempt")
        try:
            user_id, username = await verify_websocket_token(token, db)
            logger.info(f"WebSocket authenticated: user {username} ({user_id})")
        except Exception as e:
            logger.warning(f"WebSocket authentication failed: {e}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Accept WebSocket connection
        await websocket.accept()
        logger.info(f"WebSocket accepted for user {username}")
        
        # Create streaming session
        session = session_manager.create_session(user_id, websocket, db)
        
        # Start frame processor
        processor = await process_stream(session, target_fps=15)
        
        # Send welcome message with protocol info
        forwarded_proto = websocket.headers.get("x-forwarded-proto", "")
        is_secure = forwarded_proto == "https" or websocket.url.scheme == "wss"
        
        await websocket.send_json({
            'type': 'connected',
            'session_id': session.session_id,
            'message': 'Stream connected successfully',
            'target_fps': 15,
            'idle_timeout_minutes': session.idle_timeout_seconds / 60,
            'secure_connection': is_secure,
            'protocol': 'WSS' if is_secure else 'WS'
        })
        
        # Main loop - receive frames from client
        while session.is_active:
            try:
                # Receive frame data (binary JPEG)
                frame_bytes = await websocket.receive_bytes()
                
                # Add frame to processing queue
                added = await session.add_frame(frame_bytes)
                
                if not added:
                    # Queue full - frame was dropped
                    # This is normal under high load, downsampler will skip anyway
                    pass
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected: session {session.session_id}")
                break
            except Exception as e:
                logger.error(f"Error receiving frame: {e}", exc_info=True)
                break
        
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except:
            pass
    
    finally:
        # Cleanup
        logger.info("WebSocket cleanup started")
        
        # Stop processor
        if processor:
            try:
                await processor.stop()
            except Exception as e:
                logger.error(f"Error stopping processor: {e}")
        
        # Remove session and trigger post-session cleanup
        if session:
            try:
                # Trigger async CLIP validation (don't wait for it)
                asyncio.create_task(validate_and_cleanup_clips(session, db))
                
                # Remove session from manager
                await session_manager.remove_session(
                    session.session_id,
                    reason="disconnect"
                )
            except Exception as e:
                logger.error(f"Error removing session: {e}")
        
        logger.info("WebSocket cleanup complete")


@router.get("/stream/health")
async def stream_health():
    """
    Health check endpoint for streaming service.
    
    Returns information about active streaming sessions.
    """
    session_manager = get_session_manager()
    stats = session_manager.get_stats()
    
    return {
        "status": "healthy",
        "service": "realtime_streaming",
        "websocket_endpoint": "/ws/stream",
        "stats": stats
    }


@router.get("/stream/sessions")
async def list_sessions():
    """
    List all active streaming sessions (admin endpoint).
    
    Returns summary of active sessions for monitoring.
    """
    session_manager = get_session_manager()
    
    sessions_info = [
        {
            'session_id': session.session_id,
            'user_id': session.user_id,
            'start_time': session.start_time.isoformat(),
            'total_frames': session.total_frames,
            'total_detections': session.total_detections,
            'is_recording': session.is_recording,
            'idle_minutes': round(session.get_idle_minutes(), 2),
            'queue_size': session.frame_queue.qsize()
        }
        for session in session_manager.sessions.values()
    ]
    
    return {
        'active_sessions': len(sessions_info),
        'sessions': sessions_info,
        'stats': session_manager.get_stats()
    }

