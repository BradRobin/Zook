"""
Redis client for rate limiting, token blacklist, and caching.

Provides async Redis connection with graceful fallback for development.
"""
import logging
from typing import Optional, Any
from contextlib import asynccontextmanager
import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool

from .config import settings

logger = logging.getLogger(__name__)

# Global Redis connection pool
_redis_pool: Optional[ConnectionPool] = None
_redis_client: Optional[redis.Redis] = None

# In-memory fallback for development without Redis
_memory_store: dict = {}


class RedisClient:
    """
    Async Redis client wrapper with fallback to in-memory storage.
    
    Provides a unified interface for Redis operations with graceful
    degradation when Redis is unavailable.
    """
    
    def __init__(self):
        self._client: Optional[redis.Redis] = None
        self._connected: bool = False
        self._use_memory_fallback: bool = False
    
    async def connect(self) -> bool:
        """
        Establish connection to Redis server.
        
        Returns:
            True if connected successfully, False if using fallback
        """
        if not settings.REDIS_ENABLED:
            logger.info("Redis disabled in settings, using in-memory fallback")
            self._use_memory_fallback = True
            return False
        
        try:
            self._client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            await self._client.ping()
            self._connected = True
            logger.info(f"✓ Connected to Redis at {settings.REDIS_URL}")
            return True
            
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            logger.warning("Using in-memory fallback (not suitable for production)")
            self._use_memory_fallback = True
            self._connected = False
            return False
    
    async def disconnect(self):
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._connected = False
            logger.info("Redis connection closed")
    
    async def ping(self) -> bool:
        """Check if Redis is responsive."""
        if self._use_memory_fallback:
            return True
        
        try:
            if self._client:
                await self._client.ping()
                return True
        except Exception:
            pass
        return False
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis or memory store."""
        if self._use_memory_fallback:
            return _memory_store.get(key)
        
        try:
            return await self._client.get(key)
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return _memory_store.get(key)
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ex: Optional[int] = None,
        px: Optional[int] = None,
        nx: bool = False
    ) -> bool:
        """
        Set value in Redis or memory store.
        
        Args:
            key: Key to set
            value: Value to store
            ex: Expiry in seconds
            px: Expiry in milliseconds
            nx: Only set if key doesn't exist
            
        Returns:
            True if set successfully
        """
        if self._use_memory_fallback:
            if nx and key in _memory_store:
                return False
            _memory_store[key] = str(value)
            return True
        
        try:
            result = await self._client.set(key, value, ex=ex, px=px, nx=nx)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            _memory_store[key] = str(value)
            return True
    
    async def setex(self, key: str, seconds: int, value: Any) -> bool:
        """Set value with expiry in seconds."""
        return await self.set(key, value, ex=seconds)
    
    async def delete(self, *keys: str) -> int:
        """Delete one or more keys."""
        if self._use_memory_fallback:
            count = 0
            for key in keys:
                if key in _memory_store:
                    del _memory_store[key]
                    count += 1
            return count
        
        try:
            return await self._client.delete(*keys)
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
            count = 0
            for key in keys:
                if key in _memory_store:
                    del _memory_store[key]
                    count += 1
            return count
    
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        if self._use_memory_fallback:
            return key in _memory_store
        
        try:
            return bool(await self._client.exists(key))
        except Exception as e:
            logger.error(f"Redis EXISTS error: {e}")
            return key in _memory_store
    
    async def incr(self, key: str) -> int:
        """Increment key value."""
        if self._use_memory_fallback:
            current = int(_memory_store.get(key, 0))
            _memory_store[key] = str(current + 1)
            return current + 1
        
        try:
            return await self._client.incr(key)
        except Exception as e:
            logger.error(f"Redis INCR error: {e}")
            current = int(_memory_store.get(key, 0))
            _memory_store[key] = str(current + 1)
            return current + 1
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiry on existing key."""
        if self._use_memory_fallback:
            # Memory store doesn't support TTL, just return True
            return key in _memory_store
        
        try:
            return bool(await self._client.expire(key, seconds))
        except Exception as e:
            logger.error(f"Redis EXPIRE error: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """Get TTL of key in seconds."""
        if self._use_memory_fallback:
            return -1 if key in _memory_store else -2
        
        try:
            return await self._client.ttl(key)
        except Exception as e:
            logger.error(f"Redis TTL error: {e}")
            return -1
    
    async def keys(self, pattern: str) -> list:
        """Get keys matching pattern."""
        if self._use_memory_fallback:
            import fnmatch
            return [k for k in _memory_store.keys() if fnmatch.fnmatch(k, pattern)]
        
        try:
            return await self._client.keys(pattern)
        except Exception as e:
            logger.error(f"Redis KEYS error: {e}")
            return []
    
    @property
    def is_connected(self) -> bool:
        """Check if client is connected to Redis."""
        return self._connected and not self._use_memory_fallback
    
    @property
    def is_fallback(self) -> bool:
        """Check if using in-memory fallback."""
        return self._use_memory_fallback
    
    def get_client(self) -> Optional[redis.Redis]:
        """Get the underlying Redis client for advanced operations."""
        return self._client


# Global Redis client instance
redis_client = RedisClient()


async def init_redis() -> RedisClient:
    """Initialize Redis connection on application startup."""
    await redis_client.connect()
    return redis_client


async def close_redis():
    """Close Redis connection on application shutdown."""
    await redis_client.disconnect()


def get_redis() -> RedisClient:
    """Get the global Redis client instance."""
    return redis_client


# Health check function
async def redis_health_check() -> dict:
    """
    Check Redis health status.
    
    Returns:
        Dictionary with health status information
    """
    try:
        is_healthy = await redis_client.ping()
        return {
            "status": "healthy" if is_healthy else "degraded",
            "connected": redis_client.is_connected,
            "fallback_mode": redis_client.is_fallback,
            "url": settings.REDIS_URL if settings.REDIS_ENABLED else "disabled"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "connected": False,
            "fallback_mode": True,
            "error": str(e)
        }

