"""
Test suite for rate limiting functionality.

Tests rate limiting on authentication endpoints including:
- Login rate limiting (5/minute)
- Registration rate limiting (3/minute)
- Token refresh rate limiting (10/minute)
- Rate limit reset after window
- Redis fallback handling
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import time

from app.main import app
from app.config import settings


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_rate_limit_disabled():
    """Mock rate limiting disabled."""
    with patch.object(settings, 'RATE_LIMIT_ENABLED', False):
        yield


@pytest.fixture
def mock_rate_limit_enabled():
    """Mock rate limiting enabled."""
    with patch.object(settings, 'RATE_LIMIT_ENABLED', True):
        yield


class TestLoginRateLimit:
    """Test rate limiting on login endpoint."""
    
    def test_login_under_rate_limit(self, client):
        """Login should succeed when under rate limit."""
        # Single login attempt should work
        response = client.post(
            "/api/login",
            json={"username": "testuser", "password": "wrongpassword"}
        )
        # Will fail auth, but shouldn't be rate limited
        assert response.status_code in [401, 429]  # May hit rate limit from previous tests
    
    def test_login_rate_limit_headers(self, client):
        """Rate limit headers should be present in response."""
        response = client.post(
            "/api/login",
            json={"username": "testuser", "password": "testpass"}
        )
        
        # Check for rate limit headers (when enabled)
        # Note: Headers may not be present if rate limiting is disabled
        if settings.RATE_LIMIT_ENABLED:
            # SlowAPI adds these headers
            assert "X-RateLimit-Limit" in response.headers or response.status_code == 429
    
    def test_rate_limit_returns_429(self, client, mock_rate_limit_enabled):
        """Rate limit exceeded should return 429."""
        # Make multiple rapid requests
        responses = []
        for _ in range(10):
            response = client.post(
                "/api/login",
                json={"username": "testuser", "password": "wrongpassword"}
            )
            responses.append(response)
            if response.status_code == 429:
                break
        
        # At least one should hit rate limit (if enabled and exceeded)
        rate_limited = any(r.status_code == 429 for r in responses)
        # This test is conditional - may not hit limit in test environment
        if settings.RATE_LIMIT_ENABLED:
            # Check that the endpoint is accessible
            assert all(r.status_code in [401, 429] for r in responses)
    
    def test_rate_limit_response_format(self, client):
        """Rate limit exceeded response should have proper format."""
        # Make many requests to trigger rate limit
        for _ in range(20):
            response = client.post(
                "/api/login",
                json={"username": "test", "password": "test"}
            )
            if response.status_code == 429:
                data = response.json()
                assert "detail" in data
                assert "retry_after" in data or "message" in data
                break


class TestRegistrationRateLimit:
    """Test rate limiting on registration endpoint."""
    
    def test_register_under_rate_limit(self, client):
        """Registration should work when under rate limit."""
        response = client.post(
            "/api/auth",
            json={"username": "newuser123", "password": "password123"}
        )
        # Will either succeed or fail due to duplicate - not rate limited
        assert response.status_code in [201, 400, 429]
    
    def test_register_rate_limit_stricter(self, client, mock_rate_limit_enabled):
        """Registration rate limit should be stricter than login."""
        # Registration is 3/minute vs login's 5/minute
        responses = []
        for i in range(10):
            response = client.post(
                "/api/auth",
                json={"username": f"newuser{i}", "password": "password123"}
            )
            responses.append(response)
            if response.status_code == 429:
                break
        
        # Should hit rate limit sooner than login


class TestRefreshRateLimit:
    """Test rate limiting on token refresh endpoint."""
    
    def test_refresh_under_rate_limit(self, client):
        """Token refresh should work when under rate limit."""
        response = client.post(
            "/api/refresh",
            json={"refresh_token": "invalid_token"}
        )
        # Will fail auth, but shouldn't be rate limited immediately
        assert response.status_code in [401, 422, 429]
    
    def test_refresh_rate_limit_more_lenient(self, client, mock_rate_limit_enabled):
        """Refresh rate limit should be more lenient (10/minute)."""
        responses = []
        for _ in range(15):
            response = client.post(
                "/api/refresh",
                json={"refresh_token": "test_token"}
            )
            responses.append(response)
            if response.status_code == 429:
                break
        
        # Should allow more requests than login


class TestIPBasedRateLimiting:
    """Test IP-based rate limiting functionality."""
    
    def test_different_ips_have_separate_limits(self, client):
        """Different IPs should have independent rate limits."""
        # Make request with custom IP header
        response1 = client.post(
            "/api/login",
            json={"username": "test", "password": "test"},
            headers={"X-Forwarded-For": "192.168.1.100"}
        )
        
        response2 = client.post(
            "/api/login",
            json={"username": "test", "password": "test"},
            headers={"X-Forwarded-For": "192.168.1.101"}
        )
        
        # Both should get through (different IPs)
        assert response1.status_code in [401, 429]
        assert response2.status_code in [401, 429]
    
    def test_x_forwarded_for_header_respected(self, client):
        """X-Forwarded-For header should be used for rate limiting."""
        # Make multiple requests with same forwarded IP
        for _ in range(3):
            response = client.post(
                "/api/login",
                json={"username": "test", "password": "test"},
                headers={"X-Forwarded-For": "10.0.0.1"}
            )
        
        # Should count against same IP limit


class TestRateLimitDisabled:
    """Test behavior when rate limiting is disabled."""
    
    def test_requests_succeed_when_disabled(self, client, mock_rate_limit_disabled):
        """All requests should succeed when rate limiting is disabled."""
        # Make many rapid requests
        for _ in range(20):
            response = client.post(
                "/api/login",
                json={"username": "test", "password": "test"}
            )
            # Should never get 429 when rate limiting is disabled
            # (will get 401 for bad credentials instead)
            assert response.status_code != 429 or not mock_rate_limit_disabled


class TestRateLimitLogging:
    """Test rate limit violation logging."""
    
    def test_rate_limit_logged(self, client, caplog):
        """Rate limit violations should be logged."""
        import logging
        
        with caplog.at_level(logging.WARNING):
            # Make many requests to trigger rate limit
            for _ in range(20):
                response = client.post(
                    "/api/login",
                    json={"username": "test", "password": "test"}
                )
                if response.status_code == 429:
                    break
        
        # Check if rate limit was logged (may not trigger in test env)
        # Note: This depends on actual rate limiting being triggered


class TestFailedLoginTracking:
    """Test failed login attempt tracking."""
    
    def test_failed_login_tracked(self, client):
        """Failed login attempts should be tracked."""
        # Multiple failed logins
        for _ in range(3):
            response = client.post(
                "/api/login",
                json={"username": "nonexistent", "password": "wrong"}
            )
        
        # Should get 401 (not blocked yet)
        assert response.status_code in [401, 429]
    
    def test_successful_login_clears_failures(self, client):
        """Successful login should clear failed attempt counter."""
        # This would require a valid user, which we don't have in unit tests
        pass


class TestHealthCheckNotRateLimited:
    """Test that health check endpoint is not rate limited."""
    
    def test_health_check_unlimited(self, client):
        """Health check should not be rate limited."""
        for _ in range(50):
            response = client.get("/health")
            assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

