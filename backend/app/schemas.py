"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import uuid


# User schemas
class UserCreate(BaseModel):
    """Schema for user registration."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)
    
    @validator('username')
    def username_alphanumeric(cls, v):
        """Ensure username contains only alphanumeric characters and underscores."""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username must be alphanumeric (underscores and hyphens allowed)')
        return v


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str
    password: str


class UserResponse(BaseModel):
    """Schema for user response."""
    id: uuid.UUID
    username: str
    created_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True


# Token schemas
class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"
    session_id: uuid.UUID
    username: str
    expires_in: int  # seconds


class TokenData(BaseModel):
    """Schema for decoded JWT token data."""
    user_id: uuid.UUID
    username: str
    exp: datetime


# Session schemas
class SessionCreate(BaseModel):
    """Schema for creating a session."""
    user_id: uuid.UUID
    session_token: str
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_info: Optional[str] = None


class SessionResponse(BaseModel):
    """Schema for session response."""
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    expires_at: datetime
    is_active: bool
    ip_address: Optional[str]
    last_activity: datetime
    
    class Config:
        from_attributes = True


# MediaMTX stream validation
class StreamValidationRequest(BaseModel):
    """Schema for MediaMTX stream validation request."""
    action: str  # publish, read, playback
    protocol: str  # webrtc, rtsp, etc.
    path: Optional[str] = None  # stream path


class StreamValidationResponse(BaseModel):
    """Schema for stream validation response."""
    authorized: bool
    user_id: Optional[uuid.UUID] = None
    username: Optional[str] = None
    message: str


# Generic response
class MessageResponse(BaseModel):
    """Generic message response."""
    message: str


