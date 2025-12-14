"""
Metrics Collector Service for application-specific Prometheus metrics.

Collects and exposes metrics for:
- Detection performance (latency, accuracy, FPS)
- Session management (active, duration, timeouts)
- Storage utilization (clips, disk space)
- Authentication events (logins, rate limits)
- System health (Redis, database, models)
"""
import asyncio
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import dataclass

from ..config import settings
from ..metrics import (
    ACTIVE_SESSIONS, FRAMES_PROCESSED, FRAMES_DROPPED,
    RECORDINGS_STORAGE_BYTES, CLIPS_TOTAL, CLIPS_DELETED,
    REDIS_CONNECTED, DB_POOL_ACTIVE, MODEL_LOADED,
    BLOCKED_IPS, DETECTION_FPS, FALSE_POSITIVE_RATE,
    update_storage_size, update_redis_status, update_blocked_ips_count
)

logger = logging.getLogger(__name__)


@dataclass
class HealthMetrics:
    """Container for health check metrics."""
    active_sessions: int = 0
    detection_latency_p95_ms: float = 0.0
    frames_per_second: float = 0.0
    storage_used_bytes: int = 0
    clips_total: int = 0
    false_positive_rate: float = 0.0


class MetricsCollector:
    """
    Centralized metrics collection service.
    
    Provides methods for collecting and updating various application metrics.
    Uses sampling for high-frequency metrics to reduce overhead.
    """
    
    def __init__(self):
        self._active_sessions: Dict[str, dict] = {}
        self._frame_count = 0
        self._last_fps_time = time.time()
        self._last_fps_count = 0
        self._sample_counter = 0
        self._detection_latencies: list = []
        self._max_latencies = 1000  # Keep last 1000 for percentiles
    
    # ========================================================================
    # Session Metrics
    # ========================================================================
    
    def register_session(self, session_id: str, user_id: str) -> None:
        """Register a new streaming session."""
        self._active_sessions[session_id] = {
            "user_id": user_id,
            "start_time": time.time(),
            "frames_processed": 0,
            "detections": 0
        }
        ACTIVE_SESSIONS.set(len(self._active_sessions))
        logger.debug(f"Session registered: {session_id} (total: {len(self._active_sessions)})")
    
    def unregister_session(self, session_id: str, reason: str = "disconnect") -> Optional[float]:
        """
        Unregister a streaming session.
        
        Returns:
            Session duration in seconds, or None if session not found
        """
        session_data = self._active_sessions.pop(session_id, None)
        ACTIVE_SESSIONS.set(len(self._active_sessions))
        
        if session_data:
            duration = time.time() - session_data["start_time"]
            logger.debug(
                f"Session ended: {session_id} "
                f"(duration: {duration:.1f}s, reason: {reason})"
            )
            return duration
        return None
    
    def get_active_session_count(self) -> int:
        """Get the number of active sessions."""
        return len(self._active_sessions)
    
    def record_session_frame(self, session_id: str) -> None:
        """Record a frame processed for a session."""
        if session_id in self._active_sessions:
            self._active_sessions[session_id]["frames_processed"] += 1
    
    def record_session_detection(self, session_id: str) -> None:
        """Record a detection for a session."""
        if session_id in self._active_sessions:
            self._active_sessions[session_id]["detections"] += 1
    
    # ========================================================================
    # Frame Processing Metrics
    # ========================================================================
    
    def record_frame_processed(self, sampled: bool = True) -> None:
        """
        Record a processed frame.
        
        Args:
            sampled: If True, only records 10% of frames to reduce overhead
        """
        self._frame_count += 1
        
        if sampled:
            self._sample_counter += 1
            if self._sample_counter % 10 == 0:  # 10% sampling
                FRAMES_PROCESSED.inc(10)  # Increment by 10 to account for sampling
        else:
            FRAMES_PROCESSED.inc()
        
        # Update FPS every second
        now = time.time()
        if now - self._last_fps_time >= 1.0:
            fps = (self._frame_count - self._last_fps_count) / (now - self._last_fps_time)
            DETECTION_FPS.set(fps)
            self._last_fps_time = now
            self._last_fps_count = self._frame_count
    
    def record_frame_dropped(self) -> None:
        """Record a dropped frame."""
        FRAMES_DROPPED.inc()
    
    # ========================================================================
    # Detection Metrics
    # ========================================================================
    
    def record_detection_latency(self, latency_seconds: float) -> None:
        """Record detection latency for percentile calculation."""
        self._detection_latencies.append(latency_seconds)
        
        # Keep only recent samples
        if len(self._detection_latencies) > self._max_latencies:
            self._detection_latencies = self._detection_latencies[-self._max_latencies:]
    
    def get_detection_latency_p95(self) -> float:
        """Get the 95th percentile detection latency in milliseconds."""
        if not self._detection_latencies:
            return 0.0
        
        sorted_latencies = sorted(self._detection_latencies)
        idx = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[min(idx, len(sorted_latencies) - 1)] * 1000
    
    # ========================================================================
    # Storage Metrics
    # ========================================================================
    
    async def update_storage_metrics(self, recordings_path: str = "recordings") -> Dict[str, Any]:
        """
        Update storage-related metrics.
        
        Args:
            recordings_path: Path to recordings directory
            
        Returns:
            Dictionary with storage statistics
        """
        total_size = 0
        file_count = 0
        
        try:
            path = Path(recordings_path)
            if path.exists():
                for f in path.rglob("*"):
                    if f.is_file():
                        total_size += f.stat().st_size
                        file_count += 1
            
            RECORDINGS_STORAGE_BYTES.set(total_size)
            update_storage_size(total_size)
            
            return {
                "total_bytes": total_size,
                "total_mb": total_size / (1024 * 1024),
                "file_count": file_count
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate storage metrics: {e}")
            return {"total_bytes": 0, "file_count": 0, "error": str(e)}
    
    def record_clip_created(self) -> None:
        """Record a new clip being created."""
        CLIPS_TOTAL.inc()
    
    def record_clip_deleted(self, reason: str = "false_positive") -> None:
        """Record a clip being deleted."""
        CLIPS_DELETED.labels(reason=reason).inc()
    
    def update_false_positive_rate(self, rate: float) -> None:
        """Update the false positive rate gauge."""
        FALSE_POSITIVE_RATE.set(rate)
    
    # ========================================================================
    # System Health Metrics
    # ========================================================================
    
    async def check_database_health(self, db_session_factory) -> Dict[str, Any]:
        """
        Check database connectivity and pool status.
        
        Args:
            db_session_factory: Database session factory
            
        Returns:
            Dictionary with database health status
        """
        try:
            start = time.time()
            async with db_session_factory() as db:
                # Simple query to test connection
                from sqlalchemy import text
                await db.execute(text("SELECT 1"))
            
            latency_ms = (time.time() - start) * 1000
            
            return {
                "status": "up",
                "latency_ms": round(latency_ms, 2)
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "down",
                "error": str(e)
            }
    
    async def check_redis_health(self) -> Dict[str, Any]:
        """Check Redis connectivity."""
        from ..redis_client import redis_client
        
        try:
            start = time.time()
            connected = await redis_client.ping()
            latency_ms = (time.time() - start) * 1000
            
            update_redis_status(connected)
            REDIS_CONNECTED.set(1 if connected else 0)
            
            return {
                "status": "up" if connected else "degraded",
                "latency_ms": round(latency_ms, 2),
                "fallback_mode": redis_client.is_fallback
            }
            
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            REDIS_CONNECTED.set(0)
            return {
                "status": "down",
                "error": str(e)
            }
    
    def update_model_status(self, model_type: str, loaded: bool) -> None:
        """Update model load status."""
        MODEL_LOADED.labels(model_type=model_type).set(1 if loaded else 0)
    
    async def update_blocked_ips(self) -> int:
        """
        Update the count of blocked IPs.
        
        Returns:
            Number of blocked IPs
        """
        try:
            from ..services.token_blacklist import get_failed_login_tracker
            from ..redis_client import redis_client
            
            # Count IPs with high failure counts
            # This is a simplified check - production might need more sophisticated tracking
            pattern = "failed_login:*"
            keys = await redis_client.keys(pattern)
            
            blocked_count = 0
            for key in keys:
                count = await redis_client.get(key)
                if count and int(count) >= 10:  # Threshold for blocking
                    blocked_count += 1
            
            BLOCKED_IPS.set(blocked_count)
            update_blocked_ips_count(blocked_count)
            return blocked_count
            
        except Exception as e:
            logger.error(f"Failed to count blocked IPs: {e}")
            return 0
    
    # ========================================================================
    # Aggregated Health Metrics
    # ========================================================================
    
    async def collect_all_metrics(self) -> Dict[str, Any]:
        """
        Collect all metrics for health reporting.
        
        Returns:
            Comprehensive metrics dictionary
        """
        storage_metrics = await self.update_storage_metrics()
        blocked_ips = await self.update_blocked_ips()
        
        return {
            "sessions": {
                "active": self.get_active_session_count(),
                "details": dict(self._active_sessions)
            },
            "detection": {
                "latency_p95_ms": self.get_detection_latency_p95(),
                "total_frames": self._frame_count
            },
            "storage": storage_metrics,
            "security": {
                "blocked_ips": blocked_ips
            }
        }


# Global collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create the global metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


async def get_health_metrics() -> Dict[str, Any]:
    """
    Get health metrics for the /health endpoint.
    
    Returns:
        Dictionary with health-related metrics
    """
    collector = get_metrics_collector()
    
    metrics = {
        "active_sessions": collector.get_active_session_count(),
        "detection_latency_p95_ms": collector.get_detection_latency_p95(),
    }
    
    # Check model status
    try:
        from ..services import get_detector
        detector = get_detector()
        model_info = detector.get_model_info()
        metrics["yolo_model"] = {
            "status": "loaded",
            "type": model_info.get("model_type", "unknown")
        }
    except Exception:
        metrics["yolo_model"] = {"status": "not_loaded"}
    
    try:
        from ..services.clip_validator import get_clip_validator
        validator = get_clip_validator()
        validator_info = validator.get_validator_info()
        metrics["clip_model"] = {
            "status": "loaded",
            "name": validator_info.get("model_name", "unknown")
        }
    except Exception:
        metrics["clip_model"] = {"status": "not_loaded"}
    
    return metrics


# ============================================================================
# Background Metrics Collection Task
# ============================================================================

async def periodic_metrics_collection(interval_seconds: int = 60):
    """
    Background task for periodic metrics collection.
    
    Runs every `interval_seconds` to update slow-changing metrics.
    
    Args:
        interval_seconds: Collection interval in seconds
    """
    collector = get_metrics_collector()
    
    while True:
        try:
            await asyncio.sleep(interval_seconds)
            
            # Update storage metrics
            await collector.update_storage_metrics()
            
            # Update blocked IPs count
            await collector.update_blocked_ips()
            
            # Check Redis health
            await collector.check_redis_health()
            
            logger.debug("Periodic metrics collection completed")
            
        except asyncio.CancelledError:
            logger.info("Periodic metrics collection stopped")
            break
        except Exception as e:
            logger.error(f"Error in periodic metrics collection: {e}")

