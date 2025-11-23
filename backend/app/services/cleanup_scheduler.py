"""
Cleanup Scheduler for automated session and clip validation.

Uses APScheduler to run periodic tasks:
- Validate old clips with CLIP model
- Delete unharmful clips (<90% confidence)
- Clean up empty sessions
- Remove old recordings
"""
import logging
import os
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

logger = logging.getLogger(__name__)


class CleanupScheduler:
    """
    Scheduled cleanup tasks for sessions and clips.
    
    Runs periodic jobs to:
    1. Validate clips with CLIP model (>24h old)
    2. Delete false positives (<90% confidence)
    3. Delete empty sessions (no clips)
    4. Clean up orphaned files
    """
    
    def __init__(
        self,
        db_session_factory,
        validation_age_hours: int = 24,
        cleanup_interval_hours: int = 6,
        batch_size: int = 100
    ):
        """
        Initialize cleanup scheduler.
        
        Args:
            db_session_factory: Factory function to create DB sessions
            validation_age_hours: Age in hours before validating clips
            cleanup_interval_hours: Hours between cleanup runs
            batch_size: Number of records to process per batch
        """
        self.db_session_factory = db_session_factory
        self.validation_age_hours = validation_age_hours
        self.cleanup_interval_hours = cleanup_interval_hours
        self.batch_size = batch_size
        
        self.scheduler = AsyncIOScheduler()
        self._initialized = False
        
        logger.info(
            f"CleanupScheduler initialized: "
            f"validation_age={validation_age_hours}h, "
            f"interval={cleanup_interval_hours}h, "
            f"batch_size={batch_size}"
        )
    
    def start(self):
        """Start the scheduler."""
        if self._initialized:
            logger.warning("Scheduler already started")
            return
        
        # Add cleanup job
        self.scheduler.add_job(
            self.run_cleanup,
            trigger=IntervalTrigger(hours=self.cleanup_interval_hours),
            id='cleanup_sessions_clips',
            name='Cleanup old sessions and validate clips',
            replace_existing=True,
            max_instances=1  # Prevent overlapping runs
        )
        
        # Run immediately on startup (after 1 minute delay)
        self.scheduler.add_job(
            self.run_cleanup,
            trigger='date',
            run_date=datetime.now() + timedelta(minutes=1),
            id='cleanup_initial',
            name='Initial cleanup run'
        )
        
        self.scheduler.start()
        self._initialized = True
        logger.info("CleanupScheduler started")
    
    def stop(self):
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("CleanupScheduler stopped")
    
    async def run_cleanup(self):
        """
        Main cleanup task.
        
        Processes old sessions in batches:
        1. Find unvalidated clips older than threshold
        2. Run CLIP validation
        3. Delete false positives
        4. Delete empty sessions
        """
        logger.info("=" * 60)
        logger.info("Starting scheduled cleanup task")
        logger.info("=" * 60)
        
        start_time = datetime.utcnow()
        stats = {
            'clips_validated': 0,
            'clips_deleted': 0,
            'sessions_deleted': 0,
            'files_deleted': 0,
            'disk_freed_mb': 0.0
        }
        
        try:
            # Create DB session
            async with self.db_session_factory() as db:
                # Step 1: Validate old unvalidated clips
                await self._validate_old_clips(db, stats)
                
                # Step 2: Delete sessions with no valid clips
                await self._cleanup_empty_sessions(db, stats)
                
                # Step 3: Clean up orphaned files
                await self._cleanup_orphaned_files(stats)
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info("=" * 60)
            logger.info("Cleanup task completed")
            logger.info(f"Duration: {duration:.1f}s")
            logger.info(f"Clips validated: {stats['clips_validated']}")
            logger.info(f"Clips deleted (false positives): {stats['clips_deleted']}")
            logger.info(f"Sessions deleted: {stats['sessions_deleted']}")
            logger.info(f"Files deleted: {stats['files_deleted']}")
            logger.info(f"Disk space freed: {stats['disk_freed_mb']:.2f} MB")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Cleanup task failed: {e}", exc_info=True)
    
    async def _validate_old_clips(self, db: AsyncSession, stats: dict):
        """
        Validate old clips using CLIP model.
        
        Finds clips that are:
        - Older than validation_age_hours
        - Not yet validated
        - Not deleted
        
        Validates them and marks false positives for deletion.
        """
        from ..models import Clip
        from ..services.clip_validator import get_clip_validator
        
        cutoff_time = datetime.utcnow() - timedelta(hours=self.validation_age_hours)
        
        logger.info(f"Finding clips older than {cutoff_time}")
        
        # Query unvalidated clips older than threshold
        result = await db.execute(
            select(Clip)
            .where(
                and_(
                    Clip.created_at < cutoff_time,
                    Clip.is_validated == False,
                    Clip.deleted_at.is_(None)
                )
            )
            .limit(self.batch_size)
        )
        clips = result.scalars().all()
        
        if not clips:
            logger.info("No clips to validate")
            return
        
        logger.info(f"Validating {len(clips)} clip(s)")
        
        # Get CLIP validator
        validator = get_clip_validator(device='cpu')
        
        # Validate each clip
        for clip in clips:
            try:
                if not os.path.exists(clip.file_path):
                    logger.warning(f"Clip file not found: {clip.file_path}, marking as validated")
                    clip.is_validated = True
                    clip.validation_attempted_at = datetime.utcnow()
                    clip.deleted_at = datetime.utcnow()
                    stats['clips_deleted'] += 1
                    continue
                
                # Run CLIP validation
                avg_confidence, threat_count, total_frames = await validator.validate_video_async(
                    clip.file_path,
                    num_frames=10
                )
                
                # Update clip with validation results
                clip.clip_confidence = avg_confidence
                clip.is_validated = True
                clip.validation_attempted_at = datetime.utcnow()
                stats['clips_validated'] += 1
                
                # If confidence < 90%, mark as false positive and delete
                if avg_confidence < 0.90:
                    logger.info(
                        f"False positive detected: Clip {clip.id} "
                        f"(YOLO: {clip.yolo_confidence:.2%}, CLIP: {avg_confidence:.2%})"
                    )
                    
                    # Soft delete in database
                    clip.deleted_at = datetime.utcnow()
                    stats['clips_deleted'] += 1
                    
                    # Delete physical file
                    try:
                        file_size = os.path.getsize(clip.file_path) / (1024 * 1024)
                        os.remove(clip.file_path)
                        stats['files_deleted'] += 1
                        stats['disk_freed_mb'] += file_size
                        
                        # Also delete metadata file if exists
                        metadata_path = clip.file_path.replace('.mp4', '_metadata.json')
                        if os.path.exists(metadata_path):
                            os.remove(metadata_path)
                            stats['files_deleted'] += 1
                        
                        logger.info(f"Deleted false positive file: {clip.file_path} ({file_size:.2f} MB)")
                    except Exception as e:
                        logger.error(f"Failed to delete file {clip.file_path}: {e}")
                else:
                    logger.info(
                        f"Valid threat confirmed: Clip {clip.id} "
                        f"(YOLO: {clip.yolo_confidence:.2%}, CLIP: {avg_confidence:.2%})"
                    )
                
            except Exception as e:
                logger.error(f"Error validating clip {clip.id}: {e}", exc_info=True)
                clip.validation_attempted_at = datetime.utcnow()
        
        # Commit all updates
        await db.commit()
        logger.info(f"Validated {stats['clips_validated']} clips, deleted {stats['clips_deleted']} false positives")
    
    async def _cleanup_empty_sessions(self, db: AsyncSession, stats: dict):
        """
        Delete sessions that have no valid clips.
        
        Finds sessions where:
        - All clips are deleted/false positives
        - Or no clips exist
        """
        from ..models import StreamSession, Clip
        
        logger.info("Checking for empty sessions to delete")
        
        # Query all sessions
        result = await db.execute(
            select(StreamSession)
            .limit(self.batch_size)
        )
        sessions = result.scalars().all()
        
        for session in sessions:
            # Count valid (non-deleted) clips
            clip_result = await db.execute(
                select(Clip)
                .where(
                    and_(
                        Clip.stream_session_id == session.id,
                        Clip.deleted_at.is_(None)
                    )
                )
            )
            valid_clips = clip_result.scalars().all()
            
            # If no valid clips, delete session
            if not valid_clips:
                logger.info(f"Deleting empty session: {session.id}")
                await db.delete(session)
                stats['sessions_deleted'] += 1
        
        await db.commit()
        
        if stats['sessions_deleted'] > 0:
            logger.info(f"Deleted {stats['sessions_deleted']} empty session(s)")
    
    async def _cleanup_orphaned_files(self, stats: dict):
        """
        Clean up orphaned video files that have no DB record.
        
        Scans recordings directory and removes files older than retention period
        that aren't tracked in the database.
        """
        logger.info("Checking for orphaned files")
        
        recordings_dir = Path("./recordings")
        if not recordings_dir.exists():
            return
        
        # This is a simple age-based cleanup
        # More sophisticated logic could check DB for each file
        cutoff_time = datetime.utcnow() - timedelta(days=7)
        
        for file_path in recordings_dir.glob("*.mp4"):
            try:
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                if mtime < cutoff_time:
                    file_size = file_path.stat().st_size / (1024 * 1024)
                    file_path.unlink()
                    stats['files_deleted'] += 1
                    stats['disk_freed_mb'] += file_size
                    
                    # Also delete metadata
                    metadata_path = file_path.with_suffix('.json')
                    if metadata_path.exists():
                        metadata_path.unlink()
                        stats['files_deleted'] += 1
                    
                    logger.info(f"Deleted old file: {file_path.name} ({file_size:.2f} MB)")
            
            except Exception as e:
                logger.error(f"Error cleaning up {file_path}: {e}")


# Global scheduler instance
_scheduler_instance: Optional[CleanupScheduler] = None


def get_cleanup_scheduler(db_session_factory) -> CleanupScheduler:
    """
    Get or create the global cleanup scheduler instance.
    
    Args:
        db_session_factory: Factory function to create DB sessions
        
    Returns:
        CleanupScheduler instance
    """
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = CleanupScheduler(db_session_factory)
    return _scheduler_instance

