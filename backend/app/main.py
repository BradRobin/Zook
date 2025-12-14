"""
FastAPI application entry point for Zook authentication server.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from .config import settings
from .database import init_db, AsyncSessionLocal
from .routers import auth_routes, stream_routes, detection_routes, stream_ws_routes, query_routes
from .services import get_detector
from .services.cleanup_scheduler import get_cleanup_scheduler
from .redis_client import init_redis, close_redis, redis_client
from .rate_limiter import limiter, rate_limit_exceeded_handler
from .metrics import setup_metrics, update_redis_status, update_model_status, APP_START_TIME
from slowapi.errors import RateLimitExceeded
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.
    Initialize database, Redis, AI detection model, and cleanup scheduler on startup.
    """
    logger.info("Starting up Zook Auth Server...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    # Initialize Redis connection
    try:
        await init_redis()
        if redis_client.is_connected:
            logger.info("✓ Redis connected successfully")
            update_redis_status(True)
        else:
            logger.warning("⚠ Redis using in-memory fallback (not suitable for production)")
            update_redis_status(False)
    except Exception as e:
        logger.error(f"Redis initialization failed: {e}")
        logger.warning("Rate limiting and token blacklist will use in-memory storage")
        update_redis_status(False)
    
    # Initialize database tables
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        # Don't crash, allow app to start (manual migration might be needed)
    
    # Initialize YOLOv11 detection model
    try:
        logger.info("Initializing YOLOv11 threat detection model...")
        
        # Check for custom model if enabled
        custom_model_path = None
        if settings.USE_CUSTOM_MODEL and settings.CUSTOM_MODEL_PATH:
            from pathlib import Path
            model_path = Path(settings.CUSTOM_MODEL_PATH)
            if model_path.exists():
                custom_model_path = str(model_path)
                logger.info(f"Custom model found: {custom_model_path}")
            else:
                logger.warning(f"Custom model not found at {model_path}, using COCO pretrained")
        
        # Initialize detector with configuration
        detector = get_detector(
            confidence_threshold=settings.DETECTION_CONFIDENCE_THRESHOLD,
            custom_model_path=custom_model_path,
            device=settings.DETECTION_DEVICE
        )
        
        logger.info("Detection model initialized and ready")
        model_info = detector.get_model_info()
        logger.info(f"Model info: {model_info}")
        
        if model_info['model_type'] == 'custom':
            logger.info("✓ Using custom-trained knife detection model")
            update_model_status("yolo", True)
        else:
            logger.info("✓ Using COCO pre-trained model (consider training custom model for >90% accuracy)")
            update_model_status("yolo", True)
            
    except Exception as e:
        logger.error(f"Detection model initialization failed: {e}")
        logger.warning("Server will start but detection endpoint may not work")
        update_model_status("yolo", False)
    
    # Initialize CLIP validator
    try:
        logger.info("Initializing CLIP validation model...")
        from .services.clip_validator import get_clip_validator
        
        validator = get_clip_validator(device=settings.DETECTION_DEVICE)
        logger.info("CLIP validator initialized successfully")
        validator_info = validator.get_validator_info()
        logger.info(f"CLIP model: {validator_info['model_name']}")
        update_model_status("clip", True)
        
    except Exception as e:
        logger.error(f"CLIP validator initialization failed: {e}")
        logger.warning("Clip validation may not work properly")
        update_model_status("clip", False)
    
    # Initialize and start cleanup scheduler
    cleanup_scheduler = None
    try:
        logger.info("Initializing cleanup scheduler...")
        
        # Create DB session factory for scheduler
        async def db_session_factory():
            return AsyncSessionLocal()
        
        cleanup_scheduler = get_cleanup_scheduler(db_session_factory)
        cleanup_scheduler.start()
        logger.info("✓ Cleanup scheduler started (runs every 6 hours)")
        
    except Exception as e:
        logger.error(f"Cleanup scheduler initialization failed: {e}")
        logger.warning("Automated cleanup will not run")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Zook Auth Server...")
    
    # Stop cleanup scheduler
    if cleanup_scheduler:
        try:
            cleanup_scheduler.stop()
            logger.info("Cleanup scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping cleanup scheduler: {e}")
    
    # Close Redis connection
    try:
        await close_redis()
        logger.info("Redis connection closed")
    except Exception as e:
        logger.error(f"Error closing Redis: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Authentication and session management server for Zook AI surveillance platform",
    lifespan=lifespan
)

# Add rate limiter state to app
app.state.limiter = limiter

# Register rate limit exceeded exception handler
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Setup Prometheus metrics
if settings.METRICS_ENABLED:
    setup_metrics(app)
    logger.info("✓ Prometheus metrics enabled")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# HTTPS redirect middleware (production only)
@app.middleware("http")
async def https_redirect_middleware(request: Request, call_next):
    """
    Redirect HTTP to HTTPS in production environment.
    Supports Cloudflare Tunnel with X-Forwarded-Proto header.
    """
    # Check if HTTPS enforcement is enabled
    if settings.ENFORCE_HTTPS_REDIRECT and settings.USE_HTTPS:
        # Check X-Forwarded-Proto header (set by Cloudflare/reverse proxies)
        forwarded_proto = request.headers.get("X-Forwarded-Proto", "")
        
        # Determine actual protocol (handle Cloudflare Tunnel scenarios)
        is_https = (
            request.url.scheme == "https" or 
            forwarded_proto == "https"
        )
        
        # Redirect HTTP to HTTPS
        if not is_https:
            # Preserve query parameters and path
            url = request.url.replace(scheme="https")
            logger.info(f"Redirecting HTTP → HTTPS: {request.url} → {url}")
            return JSONResponse(
                status_code=301,
                content={"detail": "Redirecting to HTTPS"},
                headers={"Location": str(url)}
            )
    
    response = await call_next(request)
    return response


# Security headers middleware
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """
    Add security headers when HTTPS is enabled.
    Includes HSTS, content security policy, and other hardening headers.
    """
    response = await call_next(request)
    
    # Only add security headers when HTTPS is enabled
    if settings.USE_HTTPS:
        # HTTP Strict Transport Security (HSTS)
        # Tells browsers to only use HTTPS for 1 year
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking attacks
        response.headers["X-Frame-Options"] = "DENY"
        
        # Content Security Policy (CSP)
        # Allow same-origin and WebSocket connections
        csp_policy = (
            "default-src 'self'; "
            "connect-src 'self' ws: wss:; "
            "img-src 'self' data: blob:; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self' 'unsafe-inline'"
        )
        response.headers["Content-Security-Policy"] = csp_policy
        
        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions policy (formerly Feature-Policy)
        response.headers["Permissions-Policy"] = "camera=*, microphone=*, geolocation=()"
        
    return response


# Include routers
app.include_router(auth_routes.router)
app.include_router(stream_routes.router)
app.include_router(detection_routes.router)
app.include_router(stream_ws_routes.router)
app.include_router(query_routes.router)


# Root endpoint
@app.get("/")
async def root():
    """
    Health check and API information.
    """
    return {
        "status": "ok",
        "message": "Zook Auth Server Running",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "redoc": "/redoc"
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint with component status and metrics.
    
    Returns detailed status for:
    - Database connectivity
    - Redis connectivity  
    - YOLO model status
    - CLIP model status
    - Active sessions
    - Uptime
    """
    from .redis_client import redis_health_check
    from .services.metrics_collector import get_health_metrics
    
    # Get component health
    redis_status = await redis_health_check()
    
    # Get health metrics
    try:
        health_metrics = await get_health_metrics()
    except Exception:
        health_metrics = {}
    
    # Calculate uptime
    uptime_seconds = time.time() - APP_START_TIME._value._value if APP_START_TIME._value._value else 0
    
    # Build detailed response
    components = {
        "redis": {
            "status": "up" if redis_status.get("connected") else "degraded",
            "fallback_mode": redis_status.get("fallback_mode", False)
        }
    }
    
    # Add database status if available
    if "database" in health_metrics:
        components["database"] = health_metrics["database"]
    
    # Add model status if available
    if "yolo_model" in health_metrics:
        components["yolo_model"] = health_metrics["yolo_model"]
    if "clip_model" in health_metrics:
        components["clip_model"] = health_metrics["clip_model"]
    
    # Overall status
    overall_status = "healthy"
    if not redis_status.get("connected") and not redis_status.get("fallback_mode"):
        overall_status = "degraded"
    
    return {
        "status": overall_status,
        "service": "zook-auth-server",
        "environment": settings.ENVIRONMENT,
        "components": components,
        "metrics": {
            "active_sessions": health_metrics.get("active_sessions", 0),
            "uptime_seconds": int(uptime_seconds),
            "rate_limiting_enabled": settings.RATE_LIMIT_ENABLED,
            "metrics_enabled": settings.METRICS_ENABLED
        }
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch-all exception handler for unhandled errors.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": str(exc) if settings.ENVIRONMENT == "development" else "An error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.ENVIRONMENT == "development" else False
    )


