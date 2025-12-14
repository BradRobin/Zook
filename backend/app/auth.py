"""
JWT token generation and validation utilities.

Supports both access tokens (short-lived, 15 min) and refresh tokens (long-lived, 7 days).
Includes token blacklist functionality via Redis.
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
import hashlib
import secrets
import logging

from .config import settings
from .database import get_db
from .models import User, Session, RefreshToken
from .schemas import TokenData

logger = logging.getLogger(__name__)

# HTTP Bearer token security
security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary containing user data (user_id, username)
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def decode_token(token: str) -> TokenData:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        TokenData object with user information
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        user_id: str = payload.get("user_id")
        username: str = payload.get("username")
        exp: int = payload.get("exp")
        
        if user_id is None or username is None:
            raise credentials_exception
        
        # Convert timestamp to datetime
        exp_datetime = datetime.fromtimestamp(exp)
        
        token_data = TokenData(
            user_id=uuid.UUID(user_id),
            username=username,
            exp=exp_datetime
        )
        
        return token_data
        
    except JWTError:
        raise credentials_exception


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Authorization credentials with bearer token
        db: Database session
        
    Returns:
        User object
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    token_data = decode_token(token)
    
    # Query user from database
    result = await db.execute(
        select(User).where(User.id == token_data.user_id)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def verify_session(
    token: str,
    db: AsyncSession
) -> Optional[Session]:
    """
    Verify that a session exists and is active for the given token.
    
    Args:
        token: JWT token string
        db: Database session
        
    Returns:
        Session object if valid and active, None otherwise
    """
    try:
        token_data = decode_token(token)
        
        # Query active session with this token
        result = await db.execute(
            select(Session).where(
                Session.session_token == token,
                Session.user_id == token_data.user_id,
                Session.is_active == True,
                Session.expires_at > datetime.utcnow()
            )
        )
        
        session = result.scalar_one_or_none()
        return session
        
    except HTTPException:
        return None


# ============================================================================
# Refresh Token Functions
# ============================================================================

def hash_token(token: str) -> str:
    """
    Hash a token using SHA256 for secure storage.
    
    Args:
        token: Raw token string
        
    Returns:
        Hashed token string
    """
    return hashlib.sha256(token.encode()).hexdigest()


def generate_refresh_token() -> str:
    """
    Generate a cryptographically secure refresh token.
    
    Returns:
        Random 64-character hex string
    """
    return secrets.token_hex(32)


def create_refresh_token_jwt(
    data: dict, 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        data: Dictionary containing user data (user_id, username)
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "token_type": "refresh",
        "jti": str(uuid.uuid4())  # JWT ID for revocation tracking
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def create_token_pair(
    user_id: str,
    username: str,
    access_expires: Optional[timedelta] = None,
    refresh_expires: Optional[timedelta] = None
) -> Tuple[str, str]:
    """
    Create both access and refresh tokens.
    
    Args:
        user_id: User's UUID as string
        username: User's username
        access_expires: Optional custom access token expiry
        refresh_expires: Optional custom refresh token expiry
        
    Returns:
        Tuple of (access_token, refresh_token)
    """
    # Create access token (short-lived)
    access_expires_delta = access_expires or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"user_id": user_id, "username": username},
        expires_delta=access_expires_delta
    )
    
    # Create refresh token (long-lived)
    refresh_expires_delta = refresh_expires or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token_jwt(
        data={"user_id": user_id, "username": username},
        expires_delta=refresh_expires_delta
    )
    
    return access_token, refresh_token


def decode_refresh_token(token: str) -> TokenData:
    """
    Decode and validate a JWT refresh token.
    
    Args:
        token: JWT refresh token string
        
    Returns:
        TokenData object with user information
        
    Raises:
        HTTPException: If token is invalid, expired, or not a refresh token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        user_id: str = payload.get("user_id")
        username: str = payload.get("username")
        exp: int = payload.get("exp")
        token_type: str = payload.get("token_type")
        
        if user_id is None or username is None:
            raise credentials_exception
        
        # Verify this is a refresh token
        if token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is not a refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Convert timestamp to datetime
        exp_datetime = datetime.fromtimestamp(exp)
        
        token_data = TokenData(
            user_id=uuid.UUID(user_id),
            username=username,
            exp=exp_datetime,
            token_type="refresh"
        )
        
        return token_data
        
    except JWTError as e:
        logger.warning(f"Refresh token decode failed: {e}")
        raise credentials_exception


async def store_refresh_token(
    db: AsyncSession,
    user_id: uuid.UUID,
    token: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    device_info: Optional[str] = None
) -> RefreshToken:
    """
    Store a refresh token in the database (hashed).
    
    Args:
        db: Database session
        user_id: User's UUID
        token: Raw refresh token
        ip_address: Client IP address
        user_agent: Client user agent
        device_info: Additional device information
        
    Returns:
        Created RefreshToken object
    """
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    refresh_token = RefreshToken(
        id=uuid.uuid4(),
        user_id=user_id,
        token_hash=hash_token(token),
        expires_at=expires_at,
        ip_address=ip_address,
        user_agent=user_agent[:500] if user_agent else None,
        device_info=device_info
    )
    
    db.add(refresh_token)
    await db.commit()
    await db.refresh(refresh_token)
    
    logger.info(f"Stored refresh token for user {user_id}")
    return refresh_token


async def verify_refresh_token_db(
    db: AsyncSession,
    token: str
) -> Optional[RefreshToken]:
    """
    Verify a refresh token exists in the database and is valid.
    
    Args:
        db: Database session
        token: Raw refresh token
        
    Returns:
        RefreshToken object if valid, None otherwise
    """
    token_hash = hash_token(token)
    
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > datetime.utcnow()
        )
    )
    
    return result.scalar_one_or_none()


async def revoke_refresh_token(
    db: AsyncSession,
    token: str
) -> bool:
    """
    Revoke a refresh token.
    
    Args:
        db: Database session
        token: Raw refresh token to revoke
        
    Returns:
        True if token was revoked, False if not found
    """
    token_hash = hash_token(token)
    
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    refresh_token = result.scalar_one_or_none()
    
    if refresh_token:
        refresh_token.revoked_at = datetime.utcnow()
        await db.commit()
        logger.info(f"Revoked refresh token for user {refresh_token.user_id}")
        return True
    
    return False


async def revoke_all_user_refresh_tokens(
    db: AsyncSession,
    user_id: uuid.UUID
) -> int:
    """
    Revoke all refresh tokens for a user (logout from all devices).
    
    Args:
        db: Database session
        user_id: User's UUID
        
    Returns:
        Number of tokens revoked
    """
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None)
        )
    )
    tokens = result.scalars().all()
    
    count = 0
    for token in tokens:
        token.revoked_at = datetime.utcnow()
        count += 1
    
    await db.commit()
    logger.info(f"Revoked {count} refresh tokens for user {user_id}")
    return count


