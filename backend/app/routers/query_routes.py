"""
Query routes for searching detection clips.

Provides natural language search interface for recorded clips.
Prepares for future DeepSeek RAG integration.
"""
import logging
import os
from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel

from ..database import get_db
from ..auth import get_current_user
from ..models import User, Clip, StreamSession
from ..demo_mode import is_demo_mode_request, mask_username

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["query"])
security = HTTPBearer()


class QueryRequest(BaseModel):
    prompt: str


class ClipResult(BaseModel):
    id: str
    start_time: datetime
    end_time: Optional[datetime]
    file_path: str
    yolo_confidence: Optional[float]
    clip_confidence: Optional[float]
    file_size_mb: Optional[float]


class QueryResponse(BaseModel):
    prompt: str
    results: list[ClipResult]
    total_count: int


@router.post("", response_model=QueryResponse)
async def query_clips(
    request: QueryRequest,
    http_request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Query detection clips using natural language prompt.
    
    Simple SQL LIKE search on metadata. Prepares for future RAG integration.
    
    Supported queries:
    - Time-based: "today", "yesterday", "this week", "last 24 hours"
    - Threat type: "knife", "weapon", "threat"
    - Confidence: "high confidence", "over 90%"
    """
    prompt = request.prompt.lower().strip()
    demo_mode = is_demo_mode_request(http_request)
    log_username = mask_username(current_user.username) if demo_mode else current_user.username
    logger.info(f"Query from user {log_username}: {prompt}")
    
    # Build query based on prompt keywords
    # Start with base query filtering by user's sessions only
    query = select(Clip).where(
        and_(
            Clip.deleted_at.is_(None),  # Only non-deleted clips
            # Filter by user's sessions
            Clip.stream_session_id.in_(
                select(StreamSession.id).where(StreamSession.user_id == current_user.id)
            )
        )
    )
    
    # Time-based filtering
    if "today" in prompt:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        query = query.where(Clip.start_time >= today_start)
    elif "yesterday" in prompt:
        yesterday_start = (datetime.utcnow() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_end = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        query = query.where(and_(
            Clip.start_time >= yesterday_start,
            Clip.start_time < yesterday_end
        ))
    elif "this week" in prompt or "week" in prompt:
        week_start = datetime.utcnow() - timedelta(days=7)
        query = query.where(Clip.start_time >= week_start)
    elif "24 hours" in prompt or "last day" in prompt:
        day_ago = datetime.utcnow() - timedelta(hours=24)
        query = query.where(Clip.start_time >= day_ago)
    
    # Confidence filtering
    if "high confidence" in prompt or "over 90" in prompt or ">90" in prompt:
        query = query.where(Clip.yolo_confidence >= 0.90)
    elif "validated" in prompt or "confirmed" in prompt:
        query = query.where(and_(
            Clip.is_validated == True,
            Clip.clip_confidence >= 0.90
        ))
    
    # Order by most recent first, limit to 10 results
    query = query.order_by(Clip.start_time.desc()).limit(10)
    
    # Execute query
    result = await db.execute(query)
    clips = result.scalars().all()
    
    # Convert to response format
    clip_results = [
        ClipResult(
            id=str(clip.id),
            start_time=clip.start_time,
            end_time=clip.end_time,
            file_path=clip.file_path,
            yolo_confidence=clip.yolo_confidence,
            clip_confidence=clip.clip_confidence,
            file_size_mb=clip.file_size_mb
        )
        for clip in clips
    ]
    
    logger.info(f"Found {len(clip_results)} clips for query: {prompt}")
    
    return QueryResponse(
        prompt=request.prompt,
        results=clip_results,
        total_count=len(clip_results)
    )


@router.get("/clips/{clip_id}")
async def serve_clip(
    clip_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Serve video clip file for playback.
    
    Verifies user owns the clip before serving.
    """
    try:
        # Convert clip_id to UUID
        from uuid import UUID
        clip_uuid = UUID(clip_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid clip ID format")
    
    # Find clip
    result = await db.execute(
        select(Clip).where(Clip.id == clip_uuid)
    )
    clip = result.scalar_one_or_none()
    
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    
    # Verify ownership
    session_result = await db.execute(
        select(StreamSession).where(StreamSession.id == clip.stream_session_id)
    )
    stream_session = session_result.scalar_one_or_none()
    
    if not stream_session or stream_session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check file exists
    if not os.path.exists(clip.file_path):
        logger.warning(f"Clip file not found: {clip.file_path}")
        raise HTTPException(status_code=404, detail="Clip file not found on disk")
    
    # Serve file
    return FileResponse(
        clip.file_path,
        media_type="video/mp4",
        filename=f"clip_{clip_id}.mp4"
    )

