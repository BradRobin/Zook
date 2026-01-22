"""
Stream validation routes for MediaMTX integration.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from ..database import get_db
from ..auth import verify_session, decode_token, user_has_role
from ..models import User
from ..schemas import StreamValidationRequest, StreamValidationResponse
from ..demo_mode import is_demo_mode_request, mask_username, mask_uuid

router = APIRouter(prefix="/api/stream", tags=["streaming"])


@router.post("/validate", response_model=StreamValidationResponse)
async def validate_stream_access(
    stream_request: StreamValidationRequest,
    request: Request,
    authorization: Optional[str] = Header(None),
    token: Optional[str] = None,  # Query parameter fallback
    db: AsyncSession = Depends(get_db)
):
    """
    Validate stream access for MediaMTX.
    
    Called by MediaMTX before allowing publish/read operations.
    Checks JWT token validity and session status.
    
    Token can be provided via:
    - Authorization header: "Bearer <token>"
    - Query parameter: ?token=<token>
    """
    # Extract token from Authorization header or query param
    jwt_token = None
    
    if authorization and authorization.startswith("Bearer "):
        jwt_token = authorization.replace("Bearer ", "")
    elif token:
        jwt_token = token
    
    if not jwt_token:
        return StreamValidationResponse(
            authorized=False,
            message="No authentication token provided"
        )
    
    # Verify session exists and is active
    session = await verify_session(jwt_token, db)
    
    if not session:
        return StreamValidationResponse(
            authorized=False,
            message="Invalid or expired session"
        )
    
    # Decode token to get user info
    try:
        token_data = decode_token(jwt_token)
    except HTTPException:
        return StreamValidationResponse(
            authorized=False,
            message="Invalid token"
        )
    
    # Load user to check role-based permissions
    result = await db.execute(
        select(User).where(User.id == token_data.user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        return StreamValidationResponse(
            authorized=False,
            message="User not found"
        )

    demo_mode = is_demo_mode_request(request)
    response_user_id = mask_uuid(token_data.user_id) if demo_mode else token_data.user_id
    response_username = mask_username(token_data.username) if demo_mode else token_data.username

    # Validate action permissions (basic validation)
    allowed_actions = ["publish", "read", "playback", "api", "metrics"]
    if stream_request.action not in allowed_actions:
        return StreamValidationResponse(
            authorized=False,
            user_id=response_user_id,
            username=response_username,
            message=f"Invalid action: {stream_request.action}"
        )

    # RBAC: only admins can publish streams
    if stream_request.action == "publish" and not user_has_role(user, {"admin"}):
        return StreamValidationResponse(
            authorized=False,
            user_id=response_user_id,
            username=response_username,
            message="Publish requires admin role"
        )
    
    # Validate protocol (basic validation)
    allowed_protocols = ["webrtc", "rtsp", "rtmp", "hls", "srt"]
    if stream_request.protocol not in allowed_protocols:
        return StreamValidationResponse(
            authorized=False,
            user_id=response_user_id,
            username=response_username,
            message=f"Invalid protocol: {stream_request.protocol}"
        )
    
    # All checks passed
    return StreamValidationResponse(
        authorized=True,
        user_id=response_user_id,
        username=response_username,
        message="Stream access granted"
    )


@router.get("/health")
async def stream_health():
    """Health check endpoint for stream service."""
    return {"status": "ok", "service": "stream_validation"}


