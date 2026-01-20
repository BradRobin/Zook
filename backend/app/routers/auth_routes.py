"""
Authentication routes for user registration and login.

Includes rate limiting for security and JWT refresh token support.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
import uuid
import logging

from ..database import get_db
from ..models import User, Session, RefreshToken
from ..schemas import (
    UserCreate, UserLogin, Token, TokenPair, MessageResponse, UserResponse,
    RefreshTokenRequest, RefreshTokenResponse
)
from ..security import hash_password, verify_password
from ..auth import (
    create_access_token, get_current_user, create_token_pair,
    decode_refresh_token, store_refresh_token, verify_refresh_token_db,
    revoke_refresh_token, revoke_all_user_refresh_tokens
)
from ..config import settings
from ..rate_limiter import limiter
from ..services.token_blacklist import (
    get_token_blacklist, get_failed_login_tracker
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["authentication"])


@router.post("/auth", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_REGISTER)
async def register_user(
    request: Request,
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user account.
    
    **Rate Limited:** 3 requests per minute per IP
    
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

    # Assign admin role to the first registered user
    count_result = await db.execute(select(func.count(User.id)))
    user_count = count_result.scalar_one() or 0
    role = "admin" if user_count == 0 else "user"
    
    # Create new user
    new_user = User(
        id=uuid.uuid4(),
        username=user_data.username,
        password_hash=hashed_password,
        role=role,
        created_at=datetime.utcnow()
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return MessageResponse(message="User registered successfully")


@router.post("/login", response_model=TokenPair)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
async def login_user(
    request: Request,
    user_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and create session with token pair.
    
    **Rate Limited:** 5 requests per minute per IP
    
    - Validates credentials
    - Generates JWT access token (15 min) and refresh token (7 days)
    - Creates session record with device tracking
    - Tracks failed login attempts for security monitoring
    - Returns token pair and session information
    """
    # Extract client information
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    
    # Get failed login tracker
    login_tracker = get_failed_login_tracker()
    
    # Check if IP is temporarily blocked
    if await login_tracker.is_ip_blocked(client_ip, threshold=10):
        logger.warning(f"Blocked login attempt from {client_ip} (too many failures)")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please try again later."
        )
    
    # Find user by username
    result = await db.execute(
        select(User).where(User.username == user_data.username)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Record failed attempt
        await login_tracker.record_failed_attempt(client_ip, user_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Verify password
    if not verify_password(user_data.password, user.password_hash):
        # Record failed attempt
        await login_tracker.record_failed_attempt(client_ip, user_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Clear failed attempts on successful login
    await login_tracker.clear_failed_attempts(client_ip)
    
    # Create token pair (access + refresh)
    access_token, refresh_token = create_token_pair(
        user_id=str(user.id),
        username=user.username
    )
    
    # Store refresh token in database
    await store_refresh_token(
        db=db,
        user_id=user.id,
        token=refresh_token,
        ip_address=client_ip,
        user_agent=user_agent,
        device_info=f"IP: {client_ip}"
    )
    
    # Create session record
    session_id = uuid.uuid4()
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
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
    
    logger.info(f"User {user.username} logged in from {client_ip}")
    
    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        session_id=session_id,
        username=user.username,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_expires_in=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
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
        role=current_user.role,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )


@router.post("/refresh", response_model=RefreshTokenResponse)
@limiter.limit(settings.RATE_LIMIT_REFRESH)
async def refresh_token(
    request: Request,
    token_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using a valid refresh token.
    
    **Rate Limited:** 10 requests per minute per IP
    
    - Validates refresh token (JWT + database)
    - Checks token is not blacklisted or revoked
    - Issues new short-lived access token (15 min)
    - Does NOT rotate refresh token (for simplicity)
    
    **Request Body:**
    ```json
    {
        "refresh_token": "eyJ..."
    }
    ```
    
    **Response:**
    ```json
    {
        "access_token": "eyJ...",
        "token_type": "bearer",
        "expires_in": 900
    }
    ```
    """
    # Check if refresh token is blacklisted
    blacklist = get_token_blacklist()
    if await blacklist.is_blacklisted(token_data.refresh_token):
        logger.warning("Attempted to use blacklisted refresh token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked"
        )
    
    # Decode and validate JWT
    try:
        decoded = decode_refresh_token(token_data.refresh_token)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Verify token exists in database and is not revoked
    db_token = await verify_refresh_token_db(db, token_data.refresh_token)
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found or revoked"
        )
    
    # Verify user still exists
    result = await db.execute(
        select(User).where(User.id == decoded.user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Create new access token
    access_token = create_access_token(
        data={"user_id": str(user.id), "username": user.username},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    logger.info(f"Refreshed access token for user {user.username}")
    
    return RefreshTokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout", response_model=MessageResponse)
@limiter.limit("5/minute")
async def logout_user(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout user by deactivating their active sessions.
    
    - Deactivates all active sessions for the user
    - Revokes current refresh token if provided
    - Blacklists current access token
    """
    # Deactivate all active sessions for this user
    result = await db.execute(
        select(Session).where(
            Session.user_id == current_user.id,
            Session.is_active == True
        )
    )
    active_sessions = result.scalars().all()
    
    # Blacklist access tokens and deactivate sessions
    blacklist = get_token_blacklist()
    for session in active_sessions:
        session.is_active = False
        await blacklist.blacklist_token(
            session.session_token,
            expires_at=session.expires_at,
            reason="logout"
        )
    
    await db.commit()
    
    logger.info(f"User {current_user.username} logged out")
    return MessageResponse(message="Logged out successfully")


@router.post("/logout-all", response_model=MessageResponse)
@limiter.limit("3/minute")
async def logout_all_devices(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout user from all devices.
    
    - Revokes all refresh tokens for the user
    - Deactivates all active sessions
    - Blacklists all access tokens
    - Forces re-login on all devices
    """
    # Deactivate all active sessions
    result = await db.execute(
        select(Session).where(
            Session.user_id == current_user.id,
            Session.is_active == True
        )
    )
    active_sessions = result.scalars().all()
    
    # Blacklist all access tokens
    blacklist = get_token_blacklist()
    for session in active_sessions:
        session.is_active = False
        await blacklist.blacklist_token(
            session.session_token,
            expires_at=session.expires_at,
            reason="logout_all"
        )
    
    # Revoke all refresh tokens
    revoked_count = await revoke_all_user_refresh_tokens(db, current_user.id)
    
    await db.commit()
    
    logger.info(
        f"User {current_user.username} logged out from all devices "
        f"({len(active_sessions)} sessions, {revoked_count} refresh tokens)"
    )
    
    return MessageResponse(
        message=f"Logged out from all devices. {revoked_count} refresh tokens revoked."
    )


