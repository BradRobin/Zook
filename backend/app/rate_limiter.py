"""
Rate limiting configuration using SlowAPI with Redis backend.

Provides per-endpoint rate limiting for brute-force protection,
with logging integration for monitoring and alerting.
"""
import logging
from typing import Callable, Optional
from fastapi import Request, Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from .config import settings


def _redis_is_available(redis_url: str) -> bool:
    try:
        import redis
        client = redis.Redis.from_url(
            redis_url,
            socket_connect_timeout=1,
            socket_timeout=1
        )
        client.ping()
        return True
    except Exception as exc:
        logger.warning(f"Redis unavailable for rate limiting: {exc}")
        return False

logger = logging.getLogger(__name__)


def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request.
    
    Handles X-Forwarded-For header for proxy/Cloudflare scenarios.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Client IP address string
    """
    # Check X-Forwarded-For header (Cloudflare, nginx, etc.)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Get the first IP (original client)
        ip = forwarded_for.split(",")[0].strip()
        return ip
    
    # Check X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct client IP
    if request.client:
        return request.client.host
    
    return "unknown"


def rate_limit_key_func(request: Request) -> str:
    """
    Generate rate limit key from request.
    
    Uses client IP address as the key for rate limiting.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Rate limit key string
    """
    return get_client_ip(request)


def create_rate_limiter() -> Limiter:
    """
    Create and configure the rate limiter.
    
    Uses Redis storage if available, falls back to in-memory.
    
    Returns:
        Configured Limiter instance
    """
    # Determine storage backend
    storage_uri = None
    if settings.REDIS_ENABLED and settings.RATE_LIMIT_ENABLED:
        if _redis_is_available(settings.REDIS_URL):
            storage_uri = settings.REDIS_URL
            logger.info(f"Rate limiter using Redis storage: {settings.REDIS_URL}")
        else:
            logger.warning("Rate limiter falling back to in-memory storage")
    else:
        logger.info("Rate limiter using in-memory storage")
    
    # Create limiter with custom key function
    limiter = Limiter(
        key_func=rate_limit_key_func,
        default_limits=[settings.RATE_LIMIT_DEFAULT],
        storage_uri=storage_uri,
        strategy="fixed-window",  # or "moving-window" for stricter limiting
        headers_enabled=True,  # Add rate limit headers to responses
        enabled=settings.RATE_LIMIT_ENABLED
    )
    
    return limiter


# Global limiter instance
limiter = create_rate_limiter()


def log_rate_limit_exceeded(request: Request, limit: str):
    """
    Log rate limit violation for monitoring.
    
    Args:
        request: FastAPI request object
        limit: Rate limit that was exceeded
    """
    client_ip = get_client_ip(request)
    endpoint = request.url.path
    method = request.method
    user_agent = request.headers.get("User-Agent", "unknown")[:100]
    
    logger.warning(
        f"🚫 Rate limit exceeded: "
        f"IP={client_ip}, "
        f"endpoint={method} {endpoint}, "
        f"limit={limit}, "
        f"user_agent={user_agent}"
    )


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom handler for rate limit exceeded errors.
    
    Logs the violation and returns a proper JSON response.
    
    Args:
        request: FastAPI request object
        exc: RateLimitExceeded exception
        
    Returns:
        JSON response with rate limit error
    """
    from fastapi.responses import JSONResponse
    
    # Log the violation
    log_rate_limit_exceeded(request, str(exc.detail))

    # Record metrics
    try:
        from .metrics import record_rate_limit_hit
        record_rate_limit_hit(request.url.path)
    except Exception:
        logger.exception("Failed to record rate limit metrics")
    
    # Get retry-after header value
    retry_after = getattr(exc, 'retry_after', 60)
    
    response = JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded",
            "message": f"Too many requests. Please try again later.",
            "retry_after": retry_after
        },
        headers={
            "Retry-After": str(retry_after),
            "X-RateLimit-Limit": str(exc.detail) if exc.detail else "unknown"
        }
    )
    
    return response


# Decorator shortcuts for common rate limits
def limit_login(func: Callable) -> Callable:
    """Apply login rate limit (5/minute)."""
    return limiter.limit(settings.RATE_LIMIT_LOGIN)(func)


def limit_register(func: Callable) -> Callable:
    """Apply registration rate limit (3/minute)."""
    return limiter.limit(settings.RATE_LIMIT_REGISTER)(func)


def limit_refresh(func: Callable) -> Callable:
    """Apply token refresh rate limit (10/minute)."""
    return limiter.limit(settings.RATE_LIMIT_REFRESH)(func)


def limit_default(func: Callable) -> Callable:
    """Apply default rate limit (100/minute)."""
    return limiter.limit(settings.RATE_LIMIT_DEFAULT)(func)


# Rate limit information endpoint helper
async def get_rate_limit_info(request: Request) -> dict:
    """
    Get current rate limit status for the request.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Dictionary with rate limit information
    """
    client_ip = get_client_ip(request)
    
    return {
        "client_ip": client_ip,
        "rate_limit_enabled": settings.RATE_LIMIT_ENABLED,
        "limits": {
            "login": settings.RATE_LIMIT_LOGIN,
            "register": settings.RATE_LIMIT_REGISTER,
            "refresh": settings.RATE_LIMIT_REFRESH,
            "default": settings.RATE_LIMIT_DEFAULT
        }
    }

