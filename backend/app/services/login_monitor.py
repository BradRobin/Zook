"""
Login monitoring service for security alerting and analytics.

Tracks login patterns, failed attempts, and suspicious activity
for security monitoring and alerting.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from dataclasses import dataclass

from ..redis_client import get_redis
from ..config import settings

logger = logging.getLogger(__name__)

# Redis key prefixes
LOGIN_HISTORY_PREFIX = "login:history:"
LOGIN_STATS_PREFIX = "login:stats:"
SUSPICIOUS_IP_PREFIX = "login:suspicious:"


@dataclass
class LoginEvent:
    """Represents a login event for tracking."""
    username: str
    ip_address: str
    timestamp: datetime
    success: bool
    user_agent: str = ""
    failure_reason: Optional[str] = None


class LoginMonitor:
    """
    Service for monitoring and analyzing login activity.
    
    Provides:
    - Login event tracking
    - Failed login alerts
    - Suspicious IP detection
    - Login statistics
    """
    
    def __init__(self):
        self._redis = None
        self.alert_threshold = 5  # Failed attempts before alert
        self.suspicious_threshold = 10  # Failed attempts before marking IP suspicious
        self.history_ttl = 3600 * 24  # 24 hours
    
    @property
    def redis(self):
        """Get Redis client lazily."""
        if self._redis is None:
            self._redis = get_redis()
        return self._redis
    
    async def record_login(
        self,
        username: str,
        ip_address: str,
        success: bool,
        user_agent: str = "",
        failure_reason: Optional[str] = None
    ) -> None:
        """
        Record a login attempt for monitoring.
        
        Args:
            username: Username attempted
            ip_address: Client IP address
            success: Whether login was successful
            user_agent: Client user agent
            failure_reason: Reason for failure (if applicable)
        """
        event = LoginEvent(
            username=username,
            ip_address=ip_address,
            timestamp=datetime.utcnow(),
            success=success,
            user_agent=user_agent,
            failure_reason=failure_reason
        )
        
        # Log the event
        if success:
            logger.info(
                f"Login success: user={username}, ip={ip_address}"
            )
        else:
            logger.warning(
                f"Login failed: user={username}, ip={ip_address}, "
                f"reason={failure_reason}"
            )
        
        # Store event in Redis
        await self._store_event(event)
        
        # Update statistics
        await self._update_stats(event)
        
        # Check for alerts
        if not success:
            await self._check_alerts(event)
    
    async def _store_event(self, event: LoginEvent) -> None:
        """Store login event in Redis."""
        try:
            key = f"{LOGIN_HISTORY_PREFIX}{event.ip_address}:{event.timestamp.timestamp()}"
            value = (
                f"{event.username}|"
                f"{'success' if event.success else 'failed'}|"
                f"{event.failure_reason or ''}|"
                f"{event.user_agent[:100]}"
            )
            await self.redis.setex(key, self.history_ttl, value)
        except Exception as e:
            logger.error(f"Failed to store login event: {e}")
    
    async def _update_stats(self, event: LoginEvent) -> None:
        """Update login statistics."""
        try:
            # Daily stats key
            date_key = event.timestamp.strftime("%Y-%m-%d")
            stats_key = f"{LOGIN_STATS_PREFIX}{date_key}"
            
            # Increment counters
            if event.success:
                await self.redis.incr(f"{stats_key}:success")
            else:
                await self.redis.incr(f"{stats_key}:failed")
            
            # Set TTL for stats (7 days)
            await self.redis.expire(f"{stats_key}:success", 3600 * 24 * 7)
            await self.redis.expire(f"{stats_key}:failed", 3600 * 24 * 7)
            
        except Exception as e:
            logger.error(f"Failed to update login stats: {e}")
    
    async def _check_alerts(self, event: LoginEvent) -> None:
        """Check if alert thresholds are met."""
        try:
            # Count recent failures for this IP
            failed_key = f"login:failed_count:{event.ip_address}"
            count = await self.redis.incr(failed_key)
            
            if count == 1:
                # Set 5-minute window for counting
                await self.redis.expire(failed_key, 300)
            
            # Check alert threshold
            if count == self.alert_threshold:
                await self._send_alert(
                    f"Multiple failed login attempts from IP {event.ip_address}: "
                    f"{count} attempts in 5 minutes"
                )
            
            # Check suspicious threshold
            if count >= self.suspicious_threshold:
                await self._mark_suspicious_ip(event.ip_address)
                
        except Exception as e:
            logger.error(f"Failed to check login alerts: {e}")
    
    async def _send_alert(self, message: str) -> None:
        """
        Send security alert.
        
        Currently logs to warning level. Can be extended to send
        email, Slack, or other notifications.
        """
        logger.warning(f"🚨 SECURITY ALERT: {message}")
        
        # TODO: Implement email/webhook notifications
        # await send_email_alert(message)
        # await send_slack_alert(message)
    
    async def _mark_suspicious_ip(self, ip_address: str) -> None:
        """Mark an IP as suspicious for enhanced monitoring."""
        try:
            key = f"{SUSPICIOUS_IP_PREFIX}{ip_address}"
            await self.redis.setex(key, 3600 * 24, datetime.utcnow().isoformat())
            logger.warning(f"IP marked as suspicious: {ip_address}")
        except Exception as e:
            logger.error(f"Failed to mark suspicious IP: {e}")
    
    async def is_ip_suspicious(self, ip_address: str) -> bool:
        """Check if an IP is marked as suspicious."""
        try:
            key = f"{SUSPICIOUS_IP_PREFIX}{ip_address}"
            return await self.redis.exists(key)
        except Exception as e:
            logger.error(f"Failed to check suspicious IP: {e}")
            return False
    
    async def get_daily_stats(self, date: Optional[datetime] = None) -> Dict:
        """
        Get login statistics for a specific day.
        
        Args:
            date: Date to get stats for (defaults to today)
            
        Returns:
            Dictionary with success and failure counts
        """
        if date is None:
            date = datetime.utcnow()
        
        date_key = date.strftime("%Y-%m-%d")
        stats_key = f"{LOGIN_STATS_PREFIX}{date_key}"
        
        try:
            success = await self.redis.get(f"{stats_key}:success")
            failed = await self.redis.get(f"{stats_key}:failed")
            
            return {
                "date": date_key,
                "successful_logins": int(success) if success else 0,
                "failed_logins": int(failed) if failed else 0
            }
        except Exception as e:
            logger.error(f"Failed to get login stats: {e}")
            return {
                "date": date_key,
                "successful_logins": 0,
                "failed_logins": 0,
                "error": str(e)
            }
    
    async def get_suspicious_ips(self) -> List[str]:
        """Get list of currently suspicious IPs."""
        try:
            pattern = f"{SUSPICIOUS_IP_PREFIX}*"
            keys = await self.redis.keys(pattern)
            
            # Extract IP addresses from keys
            ips = [key.replace(SUSPICIOUS_IP_PREFIX, "") for key in keys]
            return ips
        except Exception as e:
            logger.error(f"Failed to get suspicious IPs: {e}")
            return []


# Global instance
login_monitor = LoginMonitor()


def get_login_monitor() -> LoginMonitor:
    """Get the global login monitor instance."""
    return login_monitor

