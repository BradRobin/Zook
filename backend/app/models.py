"""
SQLAlchemy database models for users and sessions.
"""
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Integer, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from .database import Base


class User(Base):
    """User account model."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="user", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    stream_sessions = relationship("StreamSession", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"


class Session(Base):
    """User authentication session model for tracking active login sessions."""
    
    __tablename__ = "sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_token = Column(String(500), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Extended tracking fields
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    user_agent = Column(Text, nullable=True)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    device_info = Column(Text, nullable=True)
    
    # Relationship to user
    user = relationship("User", back_populates="sessions")
    
    def __repr__(self):
        return f"<Session(id={self.id}, user_id={self.user_id}, is_active={self.is_active})>"


class StreamSession(Base):
    """Video streaming session model for tracking WebSocket connections and detections."""
    
    __tablename__ = "stream_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    
    # Frame statistics
    total_frames = Column(Integer, default=0, nullable=False)
    processed_frames = Column(Integer, default=0, nullable=False)
    dropped_frames = Column(Integer, default=0, nullable=False)
    
    # Detection statistics
    total_detections = Column(Integer, default=0, nullable=False)
    
    # Session metadata
    termination_reason = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="stream_sessions")
    clips = relationship("Clip", back_populates="stream_session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<StreamSession(id={self.id}, user_id={self.user_id}, detections={self.total_detections})>"


class Clip(Base):
    """Video clip model for tracking recorded threat detection clips."""
    
    __tablename__ = "clips"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    stream_session_id = Column(UUID(as_uuid=True), ForeignKey("stream_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # File information
    file_path = Column(String(512), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    file_size_mb = Column(Float, nullable=True)
    frame_count = Column(Integer, default=0, nullable=False)
    
    # Validation information
    yolo_confidence = Column(Float, nullable=True)  # Initial YOLO detection confidence
    clip_confidence = Column(Float, nullable=True)  # Secondary CLIP validation confidence
    is_validated = Column(Boolean, default=False, nullable=False, index=True)
    validation_attempted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Soft delete
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    stream_session = relationship("StreamSession", back_populates="clips")
    
    def __repr__(self):
        return f"<Clip(id={self.id}, session_id={self.stream_session_id}, validated={self.is_validated})>"


class RefreshToken(Base):
    """Refresh token model for JWT token refresh functionality."""
    
    __tablename__ = "refresh_tokens"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Token hash (never store raw refresh tokens)
    token_hash = Column(String(256), unique=True, nullable=False, index=True)
    
    # Token metadata
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Device tracking for security
    device_info = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    user_agent = Column(Text, nullable=True)
    
    # Relationship to user
    user = relationship("User", back_populates="refresh_tokens")
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        from datetime import datetime
        return datetime.utcnow() > self.expires_at.replace(tzinfo=None)
    
    @property
    def is_revoked(self) -> bool:
        """Check if token is revoked."""
        return self.revoked_at is not None
    
    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not expired and not revoked)."""
        return not self.is_expired and not self.is_revoked
    
    def __repr__(self):
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, valid={self.is_valid})>"


