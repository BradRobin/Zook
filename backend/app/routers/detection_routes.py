"""
Detection routes for YOLOv11-based threat detection.

This module provides the /detect endpoint for real-time knife detection
from video frames captured by the frontend. Requires JWT authentication
and processes JPEG images for threat detection.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import time

from ..database import get_db
from ..auth import verify_session
from ..schemas import DetectionResponse, ThreatDetection as ThreatDetectionSchema, BoundingBox
from ..services import get_detector
from ..demo_mode import is_demo_mode_request, mask_uuid_str
from ..logging_utils import format_log

logger = logging.getLogger(__name__)

router = APIRouter(tags=["detection"])
security = HTTPBearer()


@router.post("/detect", response_model=DetectionResponse)
async def detect_threats(
    request: Request,
    image: UploadFile = File(..., description="JPEG image frame from video stream"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """
    Detect knife threats in a video frame.
    
    This endpoint accepts JPEG images (typically 640x640px frames from the frontend
    canvas capture) and uses YOLOv11 to detect knife objects with high confidence.
    
    **Authentication**: Requires valid JWT token in Authorization header.
    
    **Input Format**:
    - Content-Type: multipart/form-data
    - Field name: 'image'
    - Image format: JPEG
    - Recommended size: 640x640px (will be resized if different)
    
    **Detection Criteria**:
    - Object class: 'knife' (COCO class ID 43)
    - Minimum confidence: 90% (0.90)
    - Returns all detections above threshold
    
    **Performance**:
    - Target latency: <30ms per frame on mid-tier GPU
    - Fallback to CPU if GPU unavailable (slower, ~100-200ms)
    
    **Response**:
    - Empty threats array if no knives detected
    - Non-empty threats array if knife(s) detected with >90% confidence
    - Each threat includes type, confidence, and optional bounding box
    
    **Error Codes**:
    - 401: Invalid or expired JWT token / session
    - 400: Invalid image format or corrupted data
    - 500: Model inference error
    
    **Example Request**:
    ```bash
    curl -X POST "http://localhost:8000/detect" \\
         -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
         -F "image=@frame.jpg"
    ```
    
    **Example Response (threat detected)**:
    ```json
    {
        "threats": [
            {
                "type": "knife",
                "confidence": 0.95,
                "bbox": {
                    "x1": 120.5,
                    "y1": 200.3,
                    "x2": 250.8,
                    "y2": 400.1
                }
            }
        ],
        "processing_time_ms": 25.3
    }
    ```
    
    **Example Response (no threats)**:
    ```json
    {
        "threats": [],
        "processing_time_ms": 18.7
    }
    ```
    """
    start_time = time.time()
    
    # Extract and verify JWT token
    token = credentials.credentials
    
    # Verify session is active
    session = await verify_session(token, db)
    if not session:
        client_ip = request.client.host if request.client else "unknown"
        logger.warning(format_log(
            "Detection rejected: invalid session",
            event="detection.request",
            status="unauthorized",
            ip=client_ip
        ))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    demo_mode = is_demo_mode_request(request)
    log_user_id = mask_uuid_str(session.user_id) if demo_mode else str(session.user_id)
    log_session_id = mask_uuid_str(session.id) if demo_mode else str(session.id)
    client_ip = request.client.host if request.client else "unknown"
    logger.info(format_log(
        "Detection request received",
        event="detection.request",
        status="accepted",
        ip=client_ip,
        user_id=log_user_id,
        session_id=log_session_id
    ))
    
    # Validate image file
    if not image.content_type or not image.content_type.startswith('image/'):
        logger.warning(format_log(
            "Detection rejected: invalid content type",
            event="detection.request",
            status="invalid",
            content_type=image.content_type
        ))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Expected image file (JPEG recommended)."
        )
    
    # Read image bytes
    try:
        image_bytes = await image.read()
        
        if len(image_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty image file"
            )
        
        if len(image_bytes) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image file too large (max 10MB)"
            )
        
        logger.debug(format_log(
            "Detection image received",
            event="detection.request",
            size_bytes=len(image_bytes),
            content_type=image.content_type
        ))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(format_log(
            "Detection failed to read image",
            event="detection.request",
            status="error",
            error=str(e)
        ))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read image file"
        )
    
    # Get detector instance
    try:
        detector = get_detector()
    except Exception as e:
        logger.error(format_log(
            "Detection service unavailable",
            event="detection.request",
            status="error",
            error=str(e)
        ), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Detection service unavailable"
        )
    
    # Run threat detection
    try:
        threats = detector.detect_threats(image_bytes, return_bbox=True)
        
        # Convert to Pydantic schemas
        threat_schemas = []
        for threat in threats:
            bbox = None
            if threat.bbox:
                bbox = BoundingBox(
                    x1=threat.bbox[0],
                    y1=threat.bbox[1],
                    x2=threat.bbox[2],
                    y2=threat.bbox[3]
                )
            
            threat_schema = ThreatDetectionSchema(
                type=threat.type,
                confidence=threat.confidence,
                bbox=bbox
            )
            threat_schemas.append(threat_schema)
        
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        
        response = DetectionResponse(
            threats=threat_schemas,
            processing_time_ms=round(processing_time, 2)
        )
        
        if threats:
            logger.warning(format_log(
                "Threat detected",
                event="detection.result",
                status="threat",
                threat_count=len(threats),
                processing_time_ms=round(processing_time, 2),
                user_id=log_user_id,
                session_id=log_session_id
            ))
        else:
            logger.debug(format_log(
                "No threats detected",
                event="detection.result",
                status="clear",
                processing_time_ms=round(processing_time, 2),
                user_id=log_user_id,
                session_id=log_session_id
            ))
        
        return response
        
    except ValueError as e:
        # Image processing errors
        logger.error(format_log(
            "Image processing error",
            event="detection.result",
            status="error",
            error=str(e)
        ))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image data: {str(e)}"
        )
    except RuntimeError as e:
        # Model inference errors
        logger.error(format_log(
            "Model inference error",
            event="detection.result",
            status="error",
            error=str(e)
        ), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Detection failed. Please try again."
        )
    except Exception as e:
        # Unexpected errors
        logger.error(format_log(
            "Unexpected detection error",
            event="detection.result",
            status="error",
            error=str(e)
        ), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.get("/detect/health")
async def detection_health():
    """
    Health check endpoint for detection service.
    
    Returns model information and service status.
    """
    try:
        detector = get_detector()
        model_info = detector.get_model_info()
        
        return {
            "status": "healthy",
            "service": "threat_detection",
            "model_info": model_info
        }
    except Exception as e:
        logger.error(format_log(
            "Detection health check failed",
            event="detection.health",
            status="error",
            error=str(e)
        ))
        return {
            "status": "unhealthy",
            "service": "threat_detection",
            "error": str(e)
        }


@router.post("/detect/threshold")
async def update_detection_threshold(
    request: Request,
    threshold: float,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """
    Update the detection confidence threshold dynamically.
    
    **Authentication**: Requires valid JWT token.
    
    Args:
        threshold: New confidence threshold (0.0 to 1.0)
    
    Returns:
        Success message with new threshold
    """
    # Verify session
    token = credentials.credentials
    session = await verify_session(token, db)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )
    
    # Validate threshold
    if not 0.0 <= threshold <= 1.0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Threshold must be between 0.0 and 1.0"
        )
    
    # Update detector threshold
    try:
        detector = get_detector()
        detector.update_threshold(threshold)
        
        demo_mode = is_demo_mode_request(request)
        log_user_id = mask_uuid_str(session.user_id) if demo_mode else str(session.user_id)
        logger.info(format_log(
            "Detection threshold updated",
            event="detection.threshold",
            status="success",
            user_id=log_user_id,
            threshold=threshold
        ))
        
        return {
            "message": "Threshold updated successfully",
            "new_threshold": threshold
        }
    except Exception as e:
        logger.error(format_log(
            "Failed to update detection threshold",
            event="detection.threshold",
            status="error",
            threshold=threshold,
            error=str(e)
        ))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update threshold"
        )

