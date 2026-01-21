"""
Prometheus metrics definitions and instrumentation for Zook.

Provides custom metrics for monitoring detection performance, session health,
API latency, authentication events, and system status.
"""
import logging
import time
from typing import Callable, Optional
from functools import wraps

from prometheus_client import (
    Counter, Gauge, Histogram, Info, 
    REGISTRY, generate_latest, CONTENT_TYPE_LATEST
)
from prometheus_fastapi_instrumentator import Instrumentator, metrics
from prometheus_fastapi_instrumentator.metrics import Info as MetricInfo
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .config import settings

logger = logging.getLogger(__name__)

# ============================================================================
# Metric Prefix
# ============================================================================
PREFIX = settings.METRICS_PREFIX if hasattr(settings, 'METRICS_PREFIX') else "zook"

# ============================================================================
# Detection Metrics
# ============================================================================

# YOLO detection latency - histogram with buckets optimized for <30ms target
YOLO_DETECTION_LATENCY = Histogram(
    f"{PREFIX}_yolo_detection_latency_seconds",
    "Time spent on YOLO detection inference",
    buckets=[0.005, 0.01, 0.015, 0.02, 0.025, 0.03, 0.04, 0.05, 0.075, 0.1, 0.25, 0.5, 1.0]
)

# YOLO detection confidence distribution
YOLO_DETECTION_CONFIDENCE = Histogram(
    f"{PREFIX}_yolo_detection_confidence",
    "Distribution of YOLO detection confidence scores",
    buckets=[0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.92, 0.94, 0.96, 0.98, 0.99, 1.0]
)

# Total detections by threat type
DETECTIONS_TOTAL = Counter(
    f"{PREFIX}_detections_total",
    "Total number of threat detections",
    ["threat_type"]
)

# Frame processing counters
FRAMES_PROCESSED = Counter(
    f"{PREFIX}_frames_processed_total",
    "Total frames processed for detection"
)

FRAMES_DROPPED = Counter(
    f"{PREFIX}_frames_dropped_total",
    "Total frames dropped due to queue overflow"
)

# Detection FPS gauge
DETECTION_FPS = Gauge(
    f"{PREFIX}_detection_fps",
    "Current detection frames per second"
)

# Slow detection counter (>30ms)
SLOW_DETECTIONS = Counter(
    f"{PREFIX}_slow_detections_total",
    "Number of detections exceeding 30ms threshold"
)

# ============================================================================
# Session Metrics
# ============================================================================

# Active WebSocket sessions
ACTIVE_SESSIONS = Gauge(
    f"{PREFIX}_active_sessions",
    "Number of active WebSocket streaming sessions"
)

# Total sessions created
SESSIONS_CREATED = Counter(
    f"{PREFIX}_sessions_created_total",
    "Total number of streaming sessions created"
)

# Session duration histogram
SESSION_DURATION = Histogram(
    f"{PREFIX}_session_duration_seconds",
    "Duration of streaming sessions",
    buckets=[60, 120, 300, 600, 900, 1800, 3600, 7200]  # 1min to 2hr
)

# Session termination reasons
SESSION_TERMINATIONS = Counter(
    f"{PREFIX}_session_terminations_total",
    "Session terminations by reason",
    ["reason"]  # idle_timeout, client_disconnect, error
)

# WebSocket connections
WEBSOCKET_CONNECTIONS = Gauge(
    f"{PREFIX}_websocket_connections",
    "Current number of WebSocket connections"
)

# ============================================================================
# Storage Metrics
# ============================================================================

# Recordings storage size
RECORDINGS_STORAGE_BYTES = Gauge(
    f"{PREFIX}_recordings_storage_bytes",
    "Total size of recordings directory in bytes"
)

# Clips counters
CLIPS_TOTAL = Counter(
    f"{PREFIX}_clips_total",
    "Total number of clips recorded"
)

CLIPS_DELETED = Counter(
    f"{PREFIX}_clips_deleted_total",
    "Total number of clips deleted",
    ["reason"]  # false_positive, expired, manual
)

# CLIP validation latency
CLIP_VALIDATION_LATENCY = Histogram(
    f"{PREFIX}_clip_validation_latency_seconds",
    "Time spent on CLIP validation",
    buckets=[0.5, 1.0, 2.0, 3.0, 5.0, 7.5, 10.0, 15.0, 30.0]
)

# False positive rate gauge
FALSE_POSITIVE_RATE = Gauge(
    f"{PREFIX}_false_positive_rate",
    "Rate of clips identified as false positives"
)

# ============================================================================
# Authentication Metrics
# ============================================================================

# Login attempts
LOGIN_ATTEMPTS = Counter(
    f"{PREFIX}_login_attempts_total",
    "Total login attempts",
    ["status"]  # success, failure
)

# Token operations
TOKEN_REFRESH = Counter(
    f"{PREFIX}_token_refresh_total",
    "Total token refresh operations",
    ["status"]  # success, failure
)

# Rate limit hits
RATE_LIMIT_HITS = Counter(
    f"{PREFIX}_rate_limit_hits_total",
    "Total rate limit violations",
    ["endpoint"]
)

# Blocked IPs
BLOCKED_IPS = Gauge(
    f"{PREFIX}_blocked_ips",
    "Number of currently blocked IP addresses"
)

# Failed login tracking
FAILED_LOGINS = Counter(
    f"{PREFIX}_failed_logins_total",
    "Total failed login attempts"
)

# ============================================================================
# System Metrics
# ============================================================================

# Redis connection status
REDIS_CONNECTED = Gauge(
    f"{PREFIX}_redis_connected",
    "Redis connection status (1=connected, 0=disconnected)"
)

# Database pool metrics
DB_POOL_SIZE = Gauge(
    f"{PREFIX}_database_pool_size",
    "Database connection pool size"
)

DB_POOL_ACTIVE = Gauge(
    f"{PREFIX}_database_pool_active",
    "Active database connections"
)

# Model status
MODEL_LOADED = Gauge(
    f"{PREFIX}_model_loaded",
    "Model load status",
    ["model_type"]  # yolo, clip
)

# Application uptime
APP_START_TIME = Gauge(
    f"{PREFIX}_app_start_time_seconds",
    "Application start timestamp"
)

# Application info
APP_INFO = Info(
    f"{PREFIX}_app_info",
    "Application version and configuration"
)

# ============================================================================
# Instrumentation Helpers
# ============================================================================

def time_detection(func: Callable) -> Callable:
    """
    Decorator to measure and record YOLO detection latency.
    
    Records latency to histogram and counts slow detections.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        duration = time.perf_counter() - start_time
        
        # Record to histogram
        YOLO_DETECTION_LATENCY.observe(duration)
        
        # Count slow detections (>30ms)
        if duration > 0.030:
            SLOW_DETECTIONS.inc()
        
        return result
    
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = await func(*args, **kwargs)
        duration = time.perf_counter() - start_time
        
        # Record to histogram
        YOLO_DETECTION_LATENCY.observe(duration)
        
        # Count slow detections (>30ms)
        if duration > 0.030:
            SLOW_DETECTIONS.inc()
        
        return result
    
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return wrapper


def record_detection(confidence: float, threat_type: str = "knife"):
    """Record a successful detection with confidence score."""
    YOLO_DETECTION_CONFIDENCE.observe(confidence)
    DETECTIONS_TOTAL.labels(threat_type=threat_type).inc()


def record_frame_processed():
    """Record a processed frame."""
    FRAMES_PROCESSED.inc()


def record_frame_dropped():
    """Record a dropped frame."""
    FRAMES_DROPPED.inc()


def record_session_start():
    """Record a new session starting."""
    SESSIONS_CREATED.inc()
    ACTIVE_SESSIONS.inc()


def record_session_end(duration_seconds: float, reason: str = "client_disconnect"):
    """Record a session ending."""
    ACTIVE_SESSIONS.dec()
    SESSION_DURATION.observe(duration_seconds)
    SESSION_TERMINATIONS.labels(reason=reason).inc()


def record_login(success: bool):
    """Record a login attempt."""
    status = "success" if success else "failure"
    LOGIN_ATTEMPTS.labels(status=status).inc()
    if not success:
        FAILED_LOGINS.inc()


def record_token_refresh(success: bool):
    """Record a refresh token attempt."""
    status = "success" if success else "failure"
    TOKEN_REFRESH.labels(status=status).inc()


def record_rate_limit_hit(endpoint: str):
    """Record a rate limit violation."""
    RATE_LIMIT_HITS.labels(endpoint=endpoint).inc()


def record_clip_created():
    """Record a new clip being created."""
    CLIPS_TOTAL.inc()


def record_clip_deleted(reason: str = "false_positive"):
    """Record a clip being deleted."""
    CLIPS_DELETED.labels(reason=reason).inc()


def update_storage_size(size_bytes: int):
    """Update the recordings storage size metric."""
    RECORDINGS_STORAGE_BYTES.set(size_bytes)


def update_redis_status(connected: bool):
    """Update Redis connection status."""
    REDIS_CONNECTED.set(1 if connected else 0)


def update_model_status(model_type: str, loaded: bool):
    """Update model load status."""
    MODEL_LOADED.labels(model_type=model_type).set(1 if loaded else 0)


def update_blocked_ips_count(count: int):
    """Update blocked IPs gauge."""
    BLOCKED_IPS.set(count)


def update_detection_fps(fps: float):
    """Update detection FPS gauge."""
    DETECTION_FPS.set(fps)


# ============================================================================
# FastAPI Instrumentator Setup
# ============================================================================

def create_instrumentator() -> Instrumentator:
    """
    Create and configure the Prometheus FastAPI Instrumentator.
    
    Returns:
        Configured Instrumentator instance
    """
    instrumentator = Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/metrics", "/health"],
        env_var_name="ENABLE_METRICS",
        inprogress_name=f"{PREFIX}_http_requests_inprogress",
        inprogress_labels=True,
    )
    
    # Add default metrics
    instrumentator.add(
        metrics.default(
            metric_namespace=PREFIX,
            metric_subsystem="http",
        )
    )
    
    # Add latency histogram
    instrumentator.add(
        metrics.latency(
            metric_namespace=PREFIX,
            metric_subsystem="http",
            buckets=[0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
        )
    )
    
    # Add request size
    instrumentator.add(
        metrics.request_size(
            metric_namespace=PREFIX,
            metric_subsystem="http",
        )
    )
    
    # Add response size
    instrumentator.add(
        metrics.response_size(
            metric_namespace=PREFIX,
            metric_subsystem="http",
        )
    )
    
    return instrumentator


def setup_metrics(app: FastAPI) -> None:
    """
    Set up Prometheus metrics for a FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    if not getattr(settings, 'METRICS_ENABLED', True):
        logger.info("Metrics disabled in settings")
        return
    
    # Create and instrument
    instrumentator = create_instrumentator()
    instrumentator.instrument(app)
    
    # Set app start time
    APP_START_TIME.set(time.time())
    
    # Set app info
    APP_INFO.info({
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "metrics_prefix": PREFIX
    })
    
    logger.info(f"✓ Prometheus metrics enabled (prefix: {PREFIX})")


# ============================================================================
# Metrics Endpoint (Manual Alternative)
# ============================================================================

async def metrics_endpoint(request: Request) -> Response:
    """
    Manual metrics endpoint for Prometheus scraping.
    
    Use this if you prefer not to use the instrumentator's expose method.
    """
    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST
    )

