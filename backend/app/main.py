"""
FastAPI application entry point for Zook authentication server.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from .config import settings
from .database import init_db
from .routers import auth_routes, stream_routes, detection_routes, stream_ws_routes
from .services import get_detector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.
    Initialize database and AI detection model on startup.
    """
    logger.info("Starting up Zook Auth Server...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
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
        else:
            logger.info("✓ Using COCO pre-trained model (consider training custom model for >90% accuracy)")
            
    except Exception as e:
        logger.error(f"Detection model initialization failed: {e}")
        logger.warning("Server will start but detection endpoint may not work")
    
    yield
    
    logger.info("Shutting down Zook Auth Server...")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Authentication and session management server for Zook AI surveillance platform",
    lifespan=lifespan
)


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
    """
    if settings.ENVIRONMENT == "production":
        if request.url.scheme == "http":
            url = request.url.replace(scheme="https")
            return JSONResponse(
                status_code=301,
                content={"detail": "Redirecting to HTTPS"},
                headers={"Location": str(url)}
            )
    
    response = await call_next(request)
    return response


# Include routers
app.include_router(auth_routes.router)
app.include_router(stream_routes.router)
app.include_router(detection_routes.router)
app.include_router(stream_ws_routes.router)


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
    Simple health check endpoint.
    """
    return {
        "status": "healthy",
        "service": "zook-auth-server"
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


