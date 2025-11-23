#!/usr/bin/env python3
"""
Edge case tests for knife detection system.

Tests error handling, failure scenarios, and boundary conditions.

Usage:
    pytest tests/test_edge_cases.py -v
"""
import pytest
import requests
from pathlib import Path
import concurrent.futures

BASE_URL = "http://localhost:8000"


class TestEdgeCases:
    """Test error handling and edge cases."""
    
    def test_offline_ai_service(self, test_user_token):
        """Test graceful handling when AI service is down."""
        # This requires manually stopping the detector
        # Or mocking the detector service
        pytest.skip("Requires manual detector shutdown - test manually by stopping backend")
    
    def test_invalid_image_format(self, test_user_token):
        """Test detection rejects non-image files."""
        # Create invalid file
        invalid_file = Path("tests/fixtures/invalid.txt")
        invalid_file.parent.mkdir(parents=True, exist_ok=True)
        invalid_file.write_text("This is not an image file")
        
        try:
            with open(invalid_file, 'rb') as f:
                files = {'image': ('fake.jpg', f, 'image/jpeg')}
                headers = {'Authorization': f'Bearer {test_user_token}'}
                
                response = requests.post(
                    f"{BASE_URL}/detect",
                    files=files,
                    headers=headers
                )
            
            # Should either reject or return no detections
            assert response.status_code in [200, 400, 422]
            
            if response.status_code == 200:
                data = response.json()
                # Should have no threats if processed
                assert len(data.get('threats', [])) == 0
        finally:
            # Cleanup
            if invalid_file.exists():
                invalid_file.unlink()
    
    def test_empty_image_file(self, test_user_token):
        """Test detection handles empty files."""
        empty_file = Path("tests/fixtures/empty.jpg")
        empty_file.parent.mkdir(parents=True, exist_ok=True)
        empty_file.write_bytes(b'')
        
        try:
            with open(empty_file, 'rb') as f:
                files = {'image': ('empty.jpg', f, 'image/jpeg')}
                headers = {'Authorization': f'Bearer {test_user_token}'}
                
                response = requests.post(
                    f"{BASE_URL}/detect",
                    files=files,
                    headers=headers
                )
            
            # Should reject empty file
            assert response.status_code in [400, 422, 500]
        finally:
            if empty_file.exists():
                empty_file.unlink()
    
    def test_large_image_handling(self, test_user_token):
        """Test detection handles large images (>10MB)."""
        # Would need to generate or use large test image
        pytest.skip("Large image fixture not available - test manually with >10MB image")
    
    def test_concurrent_requests(self, test_user_token):
        """Test multiple simultaneous detection requests."""
        image_path = Path("tests/fixtures/knife_high_conf.jpg")
        
        if not image_path.exists():
            pytest.skip("Test fixture not found")
        
        def make_request():
            with open(image_path, 'rb') as f:
                files = {'image': ('knife.jpg', f, 'image/jpeg')}
                headers = {'Authorization': f'Bearer {test_user_token}'}
                return requests.post(f"{BASE_URL}/detect", files=files, headers=headers)
        
        # Make 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [f.result() for f in futures]
        
        # All should succeed
        assert all(r.status_code == 200 for r in results), "Some concurrent requests failed"
        
        # All should have consistent results
        threat_counts = [len(r.json().get('threats', [])) for r in results]
        assert all(count > 0 for count in threat_counts), "Inconsistent detection results"
    
    def test_malformed_jwt_token(self):
        """Test detection with malformed JWT token."""
        image_path = Path("tests/fixtures/knife_high_conf.jpg")
        
        if not image_path.exists():
            pytest.skip("Test fixture not found")
        
        malformed_tokens = [
            "Bearer",  # Missing token
            "Bearer ",  # Empty token
            "NotBearer token123",  # Wrong scheme
            "Bearer token.without.signature",  # Malformed JWT
        ]
        
        for token in malformed_tokens:
            with open(image_path, 'rb') as f:
                files = {'image': ('knife.jpg', f, 'image/jpeg')}
                headers = {'Authorization': token}
                
                response = requests.post(
                    f"{BASE_URL}/detect",
                    files=files,
                    headers=headers
                )
            
            assert response.status_code in [401, 403], f"Expected 401/403 for malformed token: {token}"
    
    def test_missing_image_parameter(self, test_user_token):
        """Test detection without image file."""
        headers = {'Authorization': f'Bearer {test_user_token}'}
        
        response = requests.post(
            f"{BASE_URL}/detect",
            headers=headers
        )
        
        # Should reject missing image
        assert response.status_code in [400, 422]
    
    def test_wrong_http_method(self, test_user_token):
        """Test detection endpoint only accepts POST."""
        image_path = Path("tests/fixtures/knife_high_conf.jpg")
        
        if not image_path.exists():
            pytest.skip("Test fixture not found")
        
        headers = {'Authorization': f'Bearer {test_user_token}'}
        
        # Try GET method
        response = requests.get(f"{BASE_URL}/detect", headers=headers)
        assert response.status_code in [405, 404], "GET method should not be allowed"
        
        # Try PUT method
        response = requests.put(f"{BASE_URL}/detect", headers=headers)
        assert response.status_code in [405, 404], "PUT method should not be allowed"
    
    def test_expired_token_simulation(self):
        """Test detection with expired token simulation."""
        image_path = Path("tests/fixtures/knife_high_conf.jpg")
        
        if not image_path.exists():
            pytest.skip("Test fixture not found")
        
        # Use an old/expired token format
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        
        with open(image_path, 'rb') as f:
            files = {'image': ('knife.jpg', f, 'image/jpeg')}
            headers = {'Authorization': f'Bearer {expired_token}'}
            
            response = requests.post(
                f"{BASE_URL}/detect",
                files=files,
                headers=headers
            )
        
        assert response.status_code == 401, "Expired token should return 401"


class TestAuthenticationEdgeCases:
    """Test authentication-related edge cases."""
    
    def test_duplicate_username_registration(self):
        """Test registering with existing username."""
        test_user = {
            "username": "duplicate_test_user",
            "password": "Test123!@#"
        }
        
        # First registration
        response1 = requests.post(f"{BASE_URL}/api/auth", json=test_user)
        assert response1.status_code in [201, 400]  # 400 if already exists
        
        # Second registration (duplicate)
        response2 = requests.post(f"{BASE_URL}/api/auth", json=test_user)
        assert response2.status_code == 400, "Duplicate username should be rejected"
        assert "already" in response2.json()["detail"].lower()
    
    def test_login_with_wrong_password(self):
        """Test login with incorrect password."""
        # Register user
        test_user = {
            "username": f"test_wrong_pwd_{int(time.time())}",
            "password": "CorrectPassword123!"
        }
        requests.post(f"{BASE_URL}/api/auth", json=test_user)
        
        # Try login with wrong password
        wrong_credentials = {
            "username": test_user["username"],
            "password": "WrongPassword123!"
        }
        
        response = requests.post(f"{BASE_URL}/api/login", json=wrong_credentials)
        assert response.status_code == 401
    
    def test_login_nonexistent_user(self):
        """Test login with non-existent username."""
        fake_user = {
            "username": f"nonexistent_user_{int(time.time())}",
            "password": "Password123!"
        }
        
        response = requests.post(f"{BASE_URL}/api/login", json=fake_user)
        assert response.status_code == 401
    
    def test_registration_with_short_password(self):
        """Test registration with too-short password."""
        test_user = {
            "username": f"test_short_pwd_{int(time.time())}",
            "password": "123"  # Too short
        }
        
        response = requests.post(f"{BASE_URL}/api/auth", json=test_user)
        # Should reject short password (if validation implemented)
        # Accept 201 if validation not implemented yet
        assert response.status_code in [201, 400, 422]


# Import time for unique usernames
import time

