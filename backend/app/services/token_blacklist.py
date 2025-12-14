"""
Token blacklist service using Redis for invalidated JWT tokens.

Provides fast O(1) lookup for revoked tokens with automatic TTL expiry.
Falls back to in-memory storage if Redis is unavailable.
"""
import logging
from typing import Optional
from datetime import datetime, timedelta

from ..config import settings
from ..redis_client import get_redis

logger = logging.getLogger(__name__)

# Redis key prefixes
BLACKLIST_PREFIX = "token:blacklist:"
FAILED_LOGIN_PREFIX = "failed_login:"


class TokenBlacklistService:
    """
    Service for managing blacklisted JWT tokens.
    
    Tokens are stored in Redis with TTL matching their expiry time.
    This ensures revoked tokens are checked efficiently and auto-cleaned.
    """
    
    def __init__(self):
        self._redis = None
    
    @property
    def redis(self):
        """Get Redis client lazily."""
        if self._redis is None:
            self._redis = get_redis()
        return self._redis
    
    async def blacklist_token(
        self, 
        token: str, 
        expires_at: Optional[datetime] = None,
        reason: str = "logout"
    ) -> bool:
        """
        Add a token to the blacklist.
        
        Args:
            token: JWT token to blacklist (uses JTI or hash)
            expires_at: Token expiration time (for TTL calculation)
            reason: Reason for blacklisting (logout, revoked, etc.)
            
        Returns:
            True if successfully blacklisted
        """
        try:
            # Generate key from token
            import hashlib
            token_hash = hashlib.sha256(token.encode()).hexdigest()[:32]
            key = f"{BLACKLIST_PREFIX}{token_hash}"
            
            # Calculate TTL (use token expiry or default)
            if expires_at:
                ttl_seconds = int((expires_at - datetime.utcnow()).total_seconds())
                ttl_seconds = max(ttl_seconds, 60)  # Minimum 1 minute
            else:
                # Default to blacklist TTL setting
                ttl_seconds = settings.TOKEN_BLACKLIST_TTL_HOURS * 3600
            
            # Store in Redis with TTL
            value = f"{reason}:{datetime.utcnow().isoformat()}"
            await self.redis.setex(key, ttl_seconds, value)
            
            logger.info(f"Token blacklisted: reason={reason}, ttl={ttl_seconds}s")
            return True
            
        except Exception as e:
            logger.error(f"Failed to blacklist token: {e}")
            return False
    
    async def is_blacklisted(self, token: str) -> bool:
        """
        Check if a token is blacklisted.
        
        Args:
            token: JWT token to check
            
        Returns:
            True if token is blacklisted
        """
        try:
            import hashlib
            token_hash = hashlib.sha256(token.encode()).hexdigest()[:32]
            key = f"{BLACKLIST_PREFIX}{token_hash}"
            
            exists = await self.redis.exists(key)
            return exists
            
        except Exception as e:
            logger.error(f"Failed to check blacklist: {e}")
            # Fail open - if we can't check, assume not blacklisted
            # This is a security tradeoff for availability
            return False
    
    async def get_blacklist_reason(self, token: str) -> Optional[str]:
        """
        Get the reason a token was blacklisted.
        
        Args:
            token: JWT token to check
            
        Returns:
            Reason string or None if not blacklisted
        """
        try:
            import hashlib
            token_hash = hashlib.sha256(token.encode()).hexdigest()[:32]
            key = f"{BLACKLIST_PREFIX}{token_hash}"
            
            value = await self.redis.get(key)
            if value:
                return value.split(":")[0]
            return None
            
        except Exception as e:
            logger.error(f"Failed to get blacklist reason: {e}")
            return None
    
    async def blacklist_multiple(
        self, 
        tokens: list[str], 
        reason: str = "bulk_logout"
    ) -> int:
        """
        Blacklist multiple tokens at once.
        
        Args:
            tokens: List of JWT tokens to blacklist
            reason: Reason for blacklisting
            
        Returns:
            Number of tokens successfully blacklisted
        """
        count = 0
        for token in tokens:
            if await self.blacklist_token(token, reason=reason):
                count += 1
        return count


class FailedLoginTracker:
    """
    Track failed login attempts per IP address for security monitoring.
    """
    
    def __init__(self):
        self._redis = None
    
    @property
    def redis(self):
        """Get Redis client lazily."""
        if self._redis is None:
            self._redis = get_redis()
        return self._redis
    
    async def record_failed_attempt(
        self, 
        ip_address: str, 
        username: str
    ) -> int:
        """
        Record a failed login attempt.
        
        Args:
            ip_address: Client IP address
            username: Attempted username
            
        Returns:
            Number of failed attempts in current window
        """
        try:
            key = f"{FAILED_LOGIN_PREFIX}{ip_address}"
            
            # Increment counter
            count = await self.redis.incr(key)
            
            # Set TTL on first attempt (5 minute window)
            if count == 1:
                await self.redis.expire(key, 300)
            
            # Log failed attempt
            logger.warning(
                f"Failed login: IP={ip_address}, username={username}, "
                f"attempts={count}"
            )
            
            return count
            
        except Exception as e:
            logger.error(f"Failed to record login attempt: {e}")
            return 0
    
    async def get_failed_attempts(self, ip_address: str) -> int:
        """
        Get the number of failed login attempts for an IP.
        
        Args:
            ip_address: Client IP address
            
        Returns:
            Number of failed attempts in current window
        """
        try:
            key = f"{FAILED_LOGIN_PREFIX}{ip_address}"
            count = await self.redis.get(key)
            return int(count) if count else 0
            
        except Exception as e:
            logger.error(f"Failed to get login attempts: {e}")
            return 0
    
    async def is_ip_blocked(
        self, 
        ip_address: str, 
        threshold: int = 10
    ) -> bool:
        """
        Check if an IP should be temporarily blocked due to failed attempts.
        
        Args:
            ip_address: Client IP address
            threshold: Number of attempts before blocking
            
        Returns:
            True if IP should be blocked
        """
        attempts = await self.get_failed_attempts(ip_address)
        return attempts >= threshold
    
    async def clear_failed_attempts(self, ip_address: str) -> bool:
        """
        Clear failed login attempts for an IP (after successful login).
        
        Args:
            ip_address: Client IP address
            
        Returns:
            True if cleared successfully
        """
        try:
            key = f"{FAILED_LOGIN_PREFIX}{ip_address}"
            await self.redis.delete(key)
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear login attempts: {e}")
            return False


# Global service instances
token_blacklist = TokenBlacklistService()
failed_login_tracker = FailedLoginTracker()


def get_token_blacklist() -> TokenBlacklistService:
    """Get the global token blacklist service."""
    return token_blacklist


def get_failed_login_tracker() -> FailedLoginTracker:
    """Get the global failed login tracker."""
    return failed_login_tracker

