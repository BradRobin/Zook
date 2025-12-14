"""
Storage Metrics Service for monitoring disk usage and clip statistics.

Provides background collection of:
- Recordings directory size
- Clip counts (total, validated, false positives)
- Retention statistics
- Cleanup operation tracking
"""
import asyncio
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..config import settings
from ..metrics import (
    RECORDINGS_STORAGE_BYTES, CLIPS_TOTAL, CLIPS_DELETED,
    FALSE_POSITIVE_RATE, CLIP_VALIDATION_LATENCY,
    update_storage_size, record_clip_created, record_clip_deleted
)

logger = logging.getLogger(__name__)


@dataclass
class StorageStats:
    """Container for storage statistics."""
    total_bytes: int = 0
    total_mb: float = 0.0
    file_count: int = 0
    clips_total: int = 0
    clips_validated: int = 0
    clips_false_positive: int = 0
    false_positive_rate: float = 0.0
    oldest_clip_date: Optional[datetime] = None


class StorageMetricsCollector:
    """
    Collects and exposes storage-related metrics.
    
    Runs periodic scans of the recordings directory and queries
    database for clip statistics.
    """
    
    def __init__(
        self,
        recordings_path: str = "recordings",
        collection_interval: int = 300  # 5 minutes
    ):
        self.recordings_path = Path(recordings_path)
        self.collection_interval = collection_interval
        self._last_stats: Optional[StorageStats] = None
        self._is_running = False
        self._collection_task: Optional[asyncio.Task] = None
        
        logger.info(f"StorageMetricsCollector initialized (path: {recordings_path})")
    
    def scan_directory(self) -> Dict[str, Any]:
        """
        Scan the recordings directory for size and file count.
        
        Returns:
            Dictionary with storage statistics
        """
        total_size = 0
        file_count = 0
        oldest_file_time: Optional[datetime] = None
        newest_file_time: Optional[datetime] = None
        
        try:
            if self.recordings_path.exists():
                for f in self.recordings_path.rglob("*"):
                    if f.is_file():
                        stat = f.stat()
                        total_size += stat.st_size
                        file_count += 1
                        
                        # Track file age
                        mtime = datetime.fromtimestamp(stat.st_mtime)
                        if oldest_file_time is None or mtime < oldest_file_time:
                            oldest_file_time = mtime
                        if newest_file_time is None or mtime > newest_file_time:
                            newest_file_time = mtime
            
            # Update Prometheus gauge
            RECORDINGS_STORAGE_BYTES.set(total_size)
            update_storage_size(total_size)
            
            return {
                "total_bytes": total_size,
                "total_mb": round(total_size / (1024 * 1024), 2),
                "total_gb": round(total_size / (1024 * 1024 * 1024), 3),
                "file_count": file_count,
                "oldest_file": oldest_file_time.isoformat() if oldest_file_time else None,
                "newest_file": newest_file_time.isoformat() if newest_file_time else None,
            }
            
        except Exception as e:
            logger.error(f"Failed to scan recordings directory: {e}")
            return {
                "total_bytes": 0,
                "error": str(e)
            }
    
    async def get_clip_statistics(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Query database for clip statistics.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with clip statistics
        """
        try:
            from ..models import Clip
            
            # Total clips
            total_result = await db.execute(
                select(func.count(Clip.id))
            )
            total_clips = total_result.scalar() or 0
            
            # Validated clips (has_threat = true)
            validated_result = await db.execute(
                select(func.count(Clip.id)).where(Clip.has_threat == True)
            )
            validated_clips = validated_result.scalar() or 0
            
            # False positives (has_threat = false)
            fp_result = await db.execute(
                select(func.count(Clip.id)).where(Clip.has_threat == False)
            )
            false_positive_clips = fp_result.scalar() or 0
            
            # Pending validation (has_threat = null)
            pending_result = await db.execute(
                select(func.count(Clip.id)).where(Clip.has_threat == None)
            )
            pending_clips = pending_result.scalar() or 0
            
            # Calculate false positive rate
            processed = validated_clips + false_positive_clips
            fp_rate = (false_positive_clips / processed * 100) if processed > 0 else 0.0
            
            # Update metrics
            FALSE_POSITIVE_RATE.set(fp_rate)
            
            # Oldest clip date
            oldest_result = await db.execute(
                select(func.min(Clip.created_at))
            )
            oldest_date = oldest_result.scalar()
            
            return {
                "total": total_clips,
                "validated_threats": validated_clips,
                "false_positives": false_positive_clips,
                "pending_validation": pending_clips,
                "false_positive_rate_percent": round(fp_rate, 2),
                "oldest_clip_date": oldest_date.isoformat() if oldest_date else None
            }
            
        except Exception as e:
            logger.error(f"Failed to query clip statistics: {e}")
            return {
                "error": str(e)
            }
    
    async def collect_all_metrics(self, db: Optional[AsyncSession] = None) -> StorageStats:
        """
        Collect all storage metrics.
        
        Args:
            db: Optional database session for clip stats
            
        Returns:
            StorageStats dataclass with all metrics
        """
        # Scan directory
        dir_stats = self.scan_directory()
        
        stats = StorageStats(
            total_bytes=dir_stats.get("total_bytes", 0),
            total_mb=dir_stats.get("total_mb", 0.0),
            file_count=dir_stats.get("file_count", 0)
        )
        
        # Get clip stats if DB available
        if db:
            clip_stats = await self.get_clip_statistics(db)
            stats.clips_total = clip_stats.get("total", 0)
            stats.clips_validated = clip_stats.get("validated_threats", 0)
            stats.clips_false_positive = clip_stats.get("false_positives", 0)
            stats.false_positive_rate = clip_stats.get("false_positive_rate_percent", 0.0)
        
        self._last_stats = stats
        return stats
    
    async def start_background_collection(self, db_session_factory):
        """
        Start background metrics collection task.
        
        Args:
            db_session_factory: Factory function for creating DB sessions
        """
        if self._is_running:
            logger.warning("Storage metrics collection already running")
            return
        
        self._is_running = True
        self._collection_task = asyncio.create_task(
            self._collection_loop(db_session_factory)
        )
        logger.info("Started storage metrics background collection")
    
    async def stop_background_collection(self):
        """Stop background metrics collection."""
        self._is_running = False
        
        if self._collection_task and not self._collection_task.done():
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped storage metrics background collection")
    
    async def _collection_loop(self, db_session_factory):
        """
        Background loop for periodic metrics collection.
        
        Args:
            db_session_factory: Factory function for creating DB sessions
        """
        while self._is_running:
            try:
                async with db_session_factory() as db:
                    stats = await self.collect_all_metrics(db)
                    
                    logger.debug(
                        f"Storage metrics collected: "
                        f"{stats.total_mb:.2f} MB, "
                        f"{stats.file_count} files, "
                        f"{stats.clips_total} clips"
                    )
                
                await asyncio.sleep(self.collection_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in storage metrics collection: {e}")
                await asyncio.sleep(60)  # Wait before retry
    
    def get_last_stats(self) -> Optional[StorageStats]:
        """Get the most recently collected statistics."""
        return self._last_stats
    
    def check_storage_alert(self, max_size_gb: float = 10.0) -> bool:
        """
        Check if storage is approaching limit.
        
        Args:
            max_size_gb: Maximum allowed storage in GB
            
        Returns:
            True if storage exceeds threshold
        """
        if self._last_stats:
            threshold_percent = getattr(settings, 'STORAGE_ALERT_THRESHOLD_PERCENT', 80)
            threshold_bytes = max_size_gb * 1024 * 1024 * 1024 * (threshold_percent / 100)
            
            if self._last_stats.total_bytes > threshold_bytes:
                logger.warning(
                    f"Storage alert: {self._last_stats.total_mb:.2f} MB exceeds "
                    f"{threshold_percent}% of {max_size_gb} GB limit"
                )
                return True
        
        return False


# Global instance
_storage_collector: Optional[StorageMetricsCollector] = None


def get_storage_collector() -> StorageMetricsCollector:
    """Get or create the global storage metrics collector."""
    global _storage_collector
    if _storage_collector is None:
        _storage_collector = StorageMetricsCollector()
    return _storage_collector


async def record_clip_validation(duration_seconds: float, is_threat: bool):
    """
    Record clip validation metrics.
    
    Args:
        duration_seconds: Time taken for CLIP validation
        is_threat: Whether the clip was validated as a threat
    """
    CLIP_VALIDATION_LATENCY.observe(duration_seconds)
    
    if is_threat:
        record_clip_created()
    else:
        record_clip_deleted("false_positive")

