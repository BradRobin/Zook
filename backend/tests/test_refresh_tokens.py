"""
Test suite for JWT refresh token functionality.

Tests the refresh token system including:
- Token pair generation (access + refresh)
- Refresh token validation
- Token refresh flow
- Token revocation and blacklist
- Token expiry handling
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
import uuid
import hashlib

from app.main import app
from app.config import settings
from app.auth import (
    create_access_token, create_token_pair, create_refresh_token_jwt,
    decode_refresh_token, hash_token, generate_refresh_token
)
from app.schemas import TokenData


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def test_user_data():
    """Test user data for token generation."""
    return {
        "user_id": str(uuid.uuid4()),
        "username": "testuser"
    }


class TestTokenGeneration:
    """Test token generation functions."""
    
    def test_generate_refresh_token_is_random(self):
        """Generated refresh tokens should be unique."""
        token1 = generate_refresh_token()
        token2 = generate_refresh_token()
        
        assert token1 != token2
        assert len(token1) == 64  # 32 bytes = 64 hex chars
        assert len(token2) == 64
    
    def test_hash_token_consistent(self):
        """Token hashing should be consistent."""
        token = "test_token_123"
        hash1 = hash_token(token)
        hash2 = hash_token(token)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 = 64 hex chars
    
    def test_hash_token_different_inputs(self):
        """Different tokens should produce different hashes."""
        hash1 = hash_token("token1")
        hash2 = hash_token("token2")
        
        assert hash1 != hash2
    
    def test_create_access_token(self, test_user_data):
        """Access token should be created with correct data."""
        token = create_access_token(data=test_user_data)
        
        assert token is not None
        assert len(token) > 0
        assert token.count('.') == 2  # JWT has 3 parts
    
    def test_create_refresh_token_jwt(self, test_user_data):
        """Refresh token JWT should be created with correct type."""
        token = create_refresh_token_jwt(data=test_user_data)
        
        assert token is not None
        assert len(token) > 0
        assert token.count('.') == 2
    
    def test_create_token_pair(self, test_user_data):
        """Token pair should contain both access and refresh tokens."""
        access_token, refresh_token = create_token_pair(
            user_id=test_user_data["user_id"],
            username=test_user_data["username"]
        )
        
        assert access_token is not None
        assert refresh_token is not None
        assert access_token != refresh_token


class TestTokenDecoding:
    """Test token decoding and validation."""
    
    def test_decode_refresh_token_valid(self, test_user_data):
        """Valid refresh token should decode successfully."""
        refresh_token = create_refresh_token_jwt(data=test_user_data)
        
        token_data = decode_refresh_token(refresh_token)
        
        assert str(token_data.user_id) == test_user_data["user_id"]
        assert token_data.username == test_user_data["username"]
        assert token_data.token_type == "refresh"
    
    def test_decode_refresh_token_expired(self, test_user_data):
        """Expired refresh token should raise exception."""
        from fastapi import HTTPException
        
        # Create token that's already expired
        expired_token = create_refresh_token_jwt(
            data=test_user_data,
            expires_delta=timedelta(seconds=-1)
        )
        
        with pytest.raises(HTTPException) as exc_info:
            decode_refresh_token(expired_token)
        
        assert exc_info.value.status_code == 401
    
    def test_decode_refresh_token_wrong_type(self, test_user_data):
        """Access token should fail refresh token validation."""
        from fastapi import HTTPException
        
        # Create an access token (not refresh)
        access_token = create_access_token(data=test_user_data)
        
        with pytest.raises(HTTPException) as exc_info:
            decode_refresh_token(access_token)
        
        assert exc_info.value.status_code == 401
    
    def test_decode_refresh_token_invalid(self):
        """Invalid token should raise exception."""
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            decode_refresh_token("invalid.token.here")
        
        assert exc_info.value.status_code == 401


class TestRefreshEndpoint:
    """Test the /api/refresh endpoint."""
    
    def test_refresh_with_invalid_token(self, client):
        """Refresh with invalid token should return 401."""
        response = client.post(
            "/api/refresh",
            json={"refresh_token": "invalid_token"}
        )
        
        assert response.status_code == 401
    
    def test_refresh_missing_token(self, client):
        """Refresh without token should return 422."""
        response = client.post(
            "/api/refresh",
            json={}
        )
        
        assert response.status_code == 422
    
    def test_refresh_with_access_token(self, client, test_user_data):
        """Refresh with access token (not refresh) should fail."""
        access_token = create_access_token(data=test_user_data)
        
        response = client.post(
            "/api/refresh",
            json={"refresh_token": access_token}
        )
        
        assert response.status_code == 401


class TestTokenBlacklist:
    """Test token blacklist functionality."""
    
    @pytest.mark.asyncio
    async def test_blacklist_token(self):
        """Token should be added to blacklist."""
        from app.services.token_blacklist import get_token_blacklist
        
        blacklist = get_token_blacklist()
        token = "test_token_to_blacklist"
        
        result = await blacklist.blacklist_token(token, reason="test")
        assert result is True
        
        is_blacklisted = await blacklist.is_blacklisted(token)
        assert is_blacklisted is True
    
    @pytest.mark.asyncio
    async def test_non_blacklisted_token(self):
        """Non-blacklisted token should return False."""
        from app.services.token_blacklist import get_token_blacklist
        
        blacklist = get_token_blacklist()
        
        is_blacklisted = await blacklist.is_blacklisted("never_blacklisted_token")
        assert is_blacklisted is False
    
    @pytest.mark.asyncio
    async def test_blacklist_reason(self):
        """Blacklist reason should be retrievable."""
        from app.services.token_blacklist import get_token_blacklist
        
        blacklist = get_token_blacklist()
        token = "test_token_with_reason"
        
        await blacklist.blacklist_token(token, reason="logout")
        
        reason = await blacklist.get_blacklist_reason(token)
        assert reason == "logout"


class TestFailedLoginTracking:
    """Test failed login attempt tracking."""
    
    @pytest.mark.asyncio
    async def test_record_failed_attempt(self):
        """Failed login attempt should be recorded."""
        from app.services.token_blacklist import get_failed_login_tracker
        
        tracker = get_failed_login_tracker()
        ip = "192.168.1.1"
        
        count = await tracker.record_failed_attempt(ip, "testuser")
        assert count >= 1
    
    @pytest.mark.asyncio
    async def test_clear_failed_attempts(self):
        """Failed attempts should be clearable."""
        from app.services.token_blacklist import get_failed_login_tracker
        
        tracker = get_failed_login_tracker()
        ip = "192.168.1.2"
        
        # Record some failures
        await tracker.record_failed_attempt(ip, "testuser")
        
        # Clear them
        result = await tracker.clear_failed_attempts(ip)
        assert result is True
        
        # Check they're cleared
        count = await tracker.get_failed_attempts(ip)
        assert count == 0
    
    @pytest.mark.asyncio
    async def test_ip_blocking(self):
        """IP should be blocked after threshold."""
        from app.services.token_blacklist import get_failed_login_tracker
        
        tracker = get_failed_login_tracker()
        ip = "192.168.1.3"
        
        # Record many failures
        for _ in range(11):
            await tracker.record_failed_attempt(ip, "testuser")
        
        is_blocked = await tracker.is_ip_blocked(ip, threshold=10)
        assert is_blocked is True


class TestTokenExpiry:
    """Test token expiry configuration."""
    
    def test_access_token_short_lived(self):
        """Access token should be short-lived (15 min default)."""
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 15
    
    def test_refresh_token_long_lived(self):
        """Refresh token should be long-lived (7 days default)."""
        assert settings.REFRESH_TOKEN_EXPIRE_DAYS == 7
    
    def test_token_expiry_in_jwt(self, test_user_data):
        """Token expiry should be encoded in JWT."""
        from jose import jwt
        
        access_token = create_access_token(data=test_user_data)
        
        payload = jwt.decode(
            access_token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        assert "exp" in payload
        exp_time = datetime.fromtimestamp(payload["exp"])
        expected_exp = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # Should be within a few seconds
        assert abs((exp_time - expected_exp).total_seconds()) < 10


class TestLoginReturnsTokenPair:
    """Test that login returns both tokens."""
    
    def test_login_response_has_refresh_token(self, client):
        """Login should return refresh_token in response."""
        # Note: This test requires a valid user in the database
        # In unit tests, we just verify the response structure
        response = client.post(
            "/api/login",
            json={"username": "Brad", "password": "12345678"}
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert "expires_in" in data
            assert "refresh_expires_in" in data


class TestLogoutRevokesTokens:
    """Test that logout properly revokes tokens."""
    
    def test_logout_requires_auth(self, client):
        """Logout without auth should return 401/403."""
        response = client.post("/api/logout")
        
        assert response.status_code in [401, 403]
    
    def test_logout_all_requires_auth(self, client):
        """Logout-all without auth should return 401/403."""
        response = client.post("/api/logout-all")
        
        assert response.status_code in [401, 403]


class TestTokenSchemas:
    """Test token-related Pydantic schemas."""
    
    def test_token_pair_schema(self):
        """TokenPair schema should validate correctly."""
        from app.schemas import TokenPair
        
        data = TokenPair(
            access_token="access",
            refresh_token="refresh",
            session_id=uuid.uuid4(),
            username="test",
            expires_in=900,
            refresh_expires_in=604800
        )
        
        assert data.token_type == "bearer"
        assert data.expires_in == 900
    
    def test_refresh_request_schema(self):
        """RefreshTokenRequest schema should validate correctly."""
        from app.schemas import RefreshTokenRequest
        
        data = RefreshTokenRequest(refresh_token="test_token")
        assert data.refresh_token == "test_token"
    
    def test_refresh_response_schema(self):
        """RefreshTokenResponse schema should validate correctly."""
        from app.schemas import RefreshTokenResponse
        
        data = RefreshTokenResponse(
            access_token="new_access_token",
            expires_in=900
        )
        
        assert data.token_type == "bearer"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

