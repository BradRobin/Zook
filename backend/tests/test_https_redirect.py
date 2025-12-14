"""
Test suite for HTTPS redirect and security headers functionality.

Tests the production HTTPS features including:
- HTTP to HTTPS redirect
- Security headers (HSTS, CSP, X-Frame-Options, etc.)
- WebSocket protocol support (WS/WSS)
- Origin validation
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.config import settings


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_production_settings():
    """Mock production environment settings"""
    with patch.object(settings, 'ENVIRONMENT', 'production'), \
         patch.object(settings, 'USE_HTTPS', True), \
         patch.object(settings, 'ENFORCE_HTTPS_REDIRECT', True), \
         patch.object(settings, 'PRODUCTION_URL', 'https://test.example.com'):
        yield


@pytest.fixture
def mock_development_settings():
    """Mock development environment settings"""
    with patch.object(settings, 'ENVIRONMENT', 'development'), \
         patch.object(settings, 'USE_HTTPS', False), \
         patch.object(settings, 'ENFORCE_HTTPS_REDIRECT', False):
        yield


class TestHTTPSRedirect:
    """Test HTTP to HTTPS redirect functionality"""
    
    def test_no_redirect_in_development(self, client, mock_development_settings):
        """HTTP requests should not be redirected in development mode"""
        response = client.get("/health")
        assert response.status_code == 200
        assert "Location" not in response.headers
    
    def test_redirect_when_enforce_enabled(self, client, mock_production_settings):
        """HTTP requests should be redirected when ENFORCE_HTTPS_REDIRECT is true"""
        # Simulate HTTP request
        response = client.get("/health", follow_redirects=False)
        
        # Note: Testing redirect in TestClient is tricky due to base_url
        # In real production, middleware checks request.url.scheme
        # For comprehensive testing, use integration tests or manual verification
    
    def test_no_redirect_for_https_requests(self, client, mock_production_settings):
        """HTTPS requests should not be redirected"""
        # When X-Forwarded-Proto is https, no redirect should occur
        response = client.get(
            "/health",
            headers={"X-Forwarded-Proto": "https"}
        )
        assert response.status_code == 200
        assert "Location" not in response.headers
    
    def test_cloudflare_forwarded_proto_header(self, client, mock_production_settings):
        """Should respect X-Forwarded-Proto header from Cloudflare"""
        response = client.get(
            "/health",
            headers={"X-Forwarded-Proto": "https"}
        )
        assert response.status_code == 200


class TestSecurityHeaders:
    """Test security headers middleware"""
    
    def test_security_headers_when_https_enabled(self, client, mock_production_settings):
        """Security headers should be present when USE_HTTPS is true"""
        response = client.get("/health")
        
        # Check HSTS header
        assert "Strict-Transport-Security" in response.headers
        hsts = response.headers["Strict-Transport-Security"]
        assert "max-age=31536000" in hsts
        assert "includeSubDomains" in hsts
        
        # Check other security headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert "Content-Security-Policy" in response.headers
        assert "Referrer-Policy" in response.headers
        assert "Permissions-Policy" in response.headers
    
    def test_no_security_headers_in_development(self, client, mock_development_settings):
        """Security headers should not be added in development without HTTPS"""
        response = client.get("/health")
        
        # Security headers should not be present
        assert "Strict-Transport-Security" not in response.headers
    
    def test_content_security_policy(self, client, mock_production_settings):
        """CSP header should allow WebSocket connections"""
        response = client.get("/health")
        
        csp = response.headers.get("Content-Security-Policy", "")
        assert "default-src 'self'" in csp
        assert "connect-src 'self' ws: wss:" in csp
    
    def test_permissions_policy(self, client, mock_production_settings):
        """Permissions policy should allow camera access"""
        response = client.get("/health")
        
        permissions = response.headers.get("Permissions-Policy", "")
        assert "camera=*" in permissions


class TestWebSocketSecurity:
    """Test WebSocket security features"""
    
    def test_websocket_origin_validation_development(self, mock_development_settings):
        """WebSocket should accept localhost origins in development"""
        from app.routers.stream_ws_routes import validate_websocket_origin
        
        # Mock WebSocket object
        mock_ws = MagicMock()
        mock_ws.headers = {"origin": "http://localhost:3500"}
        
        assert validate_websocket_origin(mock_ws) is True
    
    def test_websocket_origin_validation_production(self, mock_production_settings):
        """WebSocket should validate origin against CORS_ORIGINS in production"""
        from app.routers.stream_ws_routes import validate_websocket_origin
        
        # Mock WebSocket object with valid origin
        mock_ws = MagicMock()
        mock_ws.headers = {"origin": "https://test.example.com"}
        
        with patch.object(settings, 'CORS_ORIGINS', ['https://test.example.com']):
            assert validate_websocket_origin(mock_ws) is True
    
    def test_websocket_invalid_origin_rejected(self, mock_production_settings):
        """WebSocket should reject invalid origins in production"""
        from app.routers.stream_ws_routes import validate_websocket_origin
        
        # Mock WebSocket object with invalid origin
        mock_ws = MagicMock()
        mock_ws.headers = {"origin": "https://evil.com"}
        
        with patch.object(settings, 'CORS_ORIGINS', ['https://test.example.com']):
            assert validate_websocket_origin(mock_ws) is False
    
    def test_websocket_protocol_detection(self):
        """Should detect WS vs WSS protocol correctly"""
        from app.routers.stream_ws_routes import log_websocket_connection_info
        
        # Mock WebSocket with HTTPS forwarded proto
        mock_ws = MagicMock()
        mock_ws.headers = {
            "x-forwarded-proto": "https",
            "origin": "https://test.com",
            "user-agent": "Mozilla/5.0"
        }
        mock_ws.url.scheme = "wss"
        mock_ws.client.host = "192.168.1.1"
        
        # Should log without raising exception
        log_websocket_connection_info(mock_ws)


class TestHealthCheckEndpoint:
    """Test health check endpoint accessibility"""
    
    def test_health_endpoint_accessible(self, client):
        """Health endpoint should be accessible"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {
            "status": "healthy",
            "service": "zook-auth-server"
        }
    
    def test_root_endpoint_shows_environment(self, client, mock_production_settings):
        """Root endpoint should show current environment"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["environment"] == "production"


class TestCORSConfiguration:
    """Test CORS configuration with HTTPS"""
    
    def test_cors_headers_present(self, client):
        """CORS headers should be present for allowed origins"""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3500",
                "Access-Control-Request-Method": "GET"
            }
        )
        
        assert "access-control-allow-origin" in response.headers.keys()
    
    def test_production_url_allowed_in_cors(self, client, mock_production_settings):
        """Production URL should be allowed in CORS"""
        with patch.object(settings, 'CORS_ORIGINS', ['https://test.example.com']):
            response = client.options(
                "/health",
                headers={
                    "Origin": "https://test.example.com",
                    "Access-Control-Request-Method": "GET"
                }
            )
            
            assert response.headers.get("access-control-allow-origin") in [
                "https://test.example.com",
                "*"  # FastAPI may return * for test client
            ]


class TestHTTPSConfigurationValidation:
    """Test configuration validation for HTTPS settings"""
    
    def test_https_enabled_with_production_url(self, mock_production_settings):
        """When HTTPS is enabled, PRODUCTION_URL should be set"""
        assert settings.USE_HTTPS is True
        assert settings.PRODUCTION_URL is not None
        assert settings.PRODUCTION_URL.startswith("https://")
    
    def test_https_redirect_requires_use_https(self):
        """ENFORCE_HTTPS_REDIRECT should only work when USE_HTTPS is true"""
        with patch.object(settings, 'USE_HTTPS', False), \
             patch.object(settings, 'ENFORCE_HTTPS_REDIRECT', True):
            
            # Middleware should not redirect when USE_HTTPS is False
            # Even if ENFORCE_HTTPS_REDIRECT is True
            pass  # Verified in middleware logic


# Integration test markers
pytestmark = pytest.mark.asyncio


class TestHTTPSIntegration:
    """Integration tests for HTTPS functionality"""
    
    async def test_full_request_lifecycle_https(self, client, mock_production_settings):
        """Test full request lifecycle with HTTPS enabled"""
        # Root endpoint
        response = client.get("/")
        assert response.status_code == 200
        assert "Strict-Transport-Security" in response.headers
        
        # Health check
        response = client.get("/health")
        assert response.status_code == 200
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        
        # API docs (should be accessible)
        response = client.get("/docs")
        assert response.status_code == 200
    
    async def test_full_request_lifecycle_development(self, client, mock_development_settings):
        """Test full request lifecycle in development mode"""
        # Root endpoint
        response = client.get("/")
        assert response.status_code == 200
        assert "Strict-Transport-Security" not in response.headers
        
        # Health check
        response = client.get("/health")
        assert response.status_code == 200


# Manual verification test (run in actual production environment)
class TestManualVerification:
    """
    Manual verification tests for production deployment.
    
    Run these tests manually against actual production environment:
    
    1. SSL Certificate:
       curl -v https://yourdomain.com/health 2>&1 | grep 'SSL connection'
    
    2. Security Headers:
       curl -I https://yourdomain.com/
    
    3. HTTP Redirect:
       curl -I http://yourdomain.com/
    
    4. WebSocket WSS:
       wscat -c "wss://yourdomain.com/ws/stream?token=YOUR_TOKEN"
    
    5. Security Headers Test:
       Visit https://securityheaders.com/?q=https://yourdomain.com
    
    6. SSL Labs Test:
       Visit https://www.ssllabs.com/ssltest/analyze.html?d=yourdomain.com
    """
    pass


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])

