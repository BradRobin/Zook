"""
Authentication routes for user registration and login.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
import uuid

from ..database import get_db
from ..models import User, Session
from ..schemas import (
    UserCreate, UserLogin, Token, MessageResponse, UserResponse
)
from ..security import hash_password, verify_password
from ..auth import create_access_token, get_current_user
from ..config import settings

router = APIRouter(prefix="/api", tags=["authentication"])


@router.post("/auth", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user account.
    
    - Validates username uniqueness
    - Hashes password with bcrypt
    - Creates user record in database
    """
    # Check if username already exists
    result = await db.execute(
        select(User).where(User.username == user_data.username)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Hash password
    hashed_password = hash_password(user_data.password)
    
    # Create new user
    new_user = User(
        id=uuid.uuid4(),
        username=user_data.username,
        password_hash=hashed_password,
        created_at=datetime.utcnow()
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return MessageResponse(message="User registered successfully")


@router.post("/login", response_model=Token)
async def login_user(
    user_data: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and create session.
    
    - Validates credentials
    - Generates JWT token
    - Creates session record with device tracking
    - Returns token and session information
    """
    # Find user by username
    result = await db.execute(
        select(User).where(User.username == user_data.username)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Verify password
    if not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Create JWT token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"user_id": str(user.id), "username": user.username},
        expires_delta=access_token_expires
    )
    
    # Extract client information
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")
    
    # Create session record
    session_id = uuid.uuid4()
    expires_at = datetime.utcnow() + access_token_expires
    
    new_session = Session(
        id=session_id,
        user_id=user.id,
        session_token=access_token,
        created_at=datetime.utcnow(),
        expires_at=expires_at,
        is_active=True,
        ip_address=client_ip,
        user_agent=user_agent,
        last_activity=datetime.utcnow(),
        device_info=f"IP: {client_ip}, UA: {user_agent[:100]}"
    )
    
    db.add(new_session)
    
    # Update user's last login
    user.last_login = datetime.utcnow()
    
    await db.commit()
    await db.refresh(new_session)
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        session_id=session_id,
        username=user.username,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/verify", response_model=UserResponse)
async def verify_token(
    current_user: User = Depends(get_current_user)
):
    """
    Verify JWT token and return user information.
    
    Used by frontend to check if stored token is still valid.
    """
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )


@router.post("/logout", response_model=MessageResponse)
async def logout_user(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout user by deactivating their active sessions.
    """
    # Deactivate all active sessions for this user
    result = await db.execute(
        select(Session).where(
            Session.user_id == current_user.id,
            Session.is_active == True
        )
    )
    active_sessions = result.scalars().all()
    
    for session in active_sessions:
        session.is_active = False
    
    await db.commit()
    
    return MessageResponse(message="Logged out successfully")


