"""
JWT token generation and validation utilities.
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from .config import settings
from .database import get_db
from .models import User, Session
from .schemas import TokenData

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


