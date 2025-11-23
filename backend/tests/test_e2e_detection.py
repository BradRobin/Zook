#!/usr/bin/env python3
"""
End-to-end tests for knife detection flow.

Tests the complete flow from user registration through threat detection,
including performance benchmarks and edge cases.

Usage:
    pytest tests/test_e2e_detection.py -v
    pytest tests/test_e2e_detection.py::TestKnifeDetectionE2E::test_04_knife_detection_high_confidence -v
"""
import pytest
import requests
import time
from pathlib import Path
from typing import Dict, Optional

# Test Configuration
BASE_URL = "http://localhost:8000"
TEST_USER = {"username": "test_user_e2e", "password": "Test123!@#"}
DETECTION_THRESHOLD = 0.90
MAX_LATENCY_MS = 1000


@pytest.fixture(scope="module")
def test_user_token():
    """Register user and get JWT token for all tests."""
    # Register
    response = requests.post(
        f"{BASE_URL}/api/auth",
        json=TEST_USER
    )
    assert response.status_code in [201, 400]  # 400 if already exists
    
    # Login
    response = requests.post(
        f"{BASE_URL}/api/login",
        json=TEST_USER
    )
    assert response.status_code == 200
    return response.json()["access_token"]


class TestKnifeDetectionE2E:
    """End-to-end tests for knife detection flow."""
    
    def test_01_user_registration(self):
        """Test user can register with valid credentials."""
        # Create unique test user
        test_user = {
            "username": f"test_{int(time.time())}",
            "password": "SecurePass123!"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/auth",
            json=test_user
        )
        
        assert response.status_code == 201
        assert "successfully" in response.json()["message"].lower()
    
    def test_02_user_login(self, test_user_token):
        """Test user can login and receive JWT token."""
        assert test_user_token is not None
        assert len(test_user_token) > 50  # JWT tokens are long
    
    def test_03_health_check(self):
        """Test detection service is online."""
        response = requests.get(f"{BASE_URL}/detect/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "yolo" in data["model_info"]["architecture"].lower()
    
    def test_04_knife_detection_high_confidence(self, test_user_token):
        """Test knife detection with >90% confidence triggers alert."""
        image_path = Path("tests/fixtures/knife_high_conf.jpg")
        
        if not image_path.exists():
            pytest.skip("Test fixture not found. Add knife_high_conf.jpg to tests/fixtures/")
        
        with open(image_path, 'rb') as f:
            files = {'image': ('knife.jpg', f, 'image/jpeg')}
            headers = {'Authorization': f'Bearer {test_user_token}'}
            
            start_time = time.time()
            response = requests.post(
                f"{BASE_URL}/detect",
                files=files,
                headers=headers
            )
            latency_ms = (time.time() - start_time) * 1000
        
        # Assert success
        assert response.status_code == 200
        data = response.json()
        
        # Assert performance
        assert latency_ms < MAX_LATENCY_MS, f"Latency {latency_ms}ms exceeds {MAX_LATENCY_MS}ms"
        
        # Assert detection
        threats = data.get('threats', [])
        assert len(threats) > 0, "No threats detected"
        
        knife_detected = any(
            'knife' in t['type'].lower() and t['confidence'] >= DETECTION_THRESHOLD
            for t in threats
        )
        assert knife_detected, f"No knife detected with >{DETECTION_THRESHOLD*100}% confidence"
        
        # Print for manual verification
        print(f"\n✓ Knife detected: {threats[0]['confidence']:.1%} confidence")
        print(f"✓ Latency: {latency_ms:.1f}ms")
    
    def test_05_low_confidence_no_alert(self, test_user_token):
        """Test low confidence detection (<90%) does not trigger alert."""
        image_path = Path("tests/fixtures/knife_low_conf.jpg")
        
        if not image_path.exists():
            pytest.skip("Low confidence test fixture not available")
        
        with open(image_path, 'rb') as f:
            files = {'image': ('ambiguous.jpg', f, 'image/jpeg')}
            headers = {'Authorization': f'Bearer {test_user_token}'}
            
            response = requests.post(
                f"{BASE_URL}/detect",
                files=files,
                headers=headers
            )
        
        assert response.status_code == 200
        data = response.json()
        
        threats = data.get('threats', [])
        high_conf_threats = [t for t in threats if t['confidence'] >= DETECTION_THRESHOLD]
        
        assert len(high_conf_threats) == 0, "Low confidence image should not trigger alert"
    
    def test_06_no_threat_image(self, test_user_token):
        """Test clean image with no weapons."""
        image_path = Path("tests/fixtures/no_threat.jpg")
        
        if not image_path.exists():
            pytest.skip("Test fixture not found. Add no_threat.jpg to tests/fixtures/")
        
        with open(image_path, 'rb') as f:
            files = {'image': ('clean.jpg', f, 'image/jpeg')}
            headers = {'Authorization': f'Bearer {test_user_token}'}
            
            response = requests.post(
                f"{BASE_URL}/detect",
                files=files,
                headers=headers
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get('threats', []) == []
    
    def test_07_invalid_token(self):
        """Test detection fails with invalid JWT token."""
        image_path = Path("tests/fixtures/knife_high_conf.jpg")
        
        if not image_path.exists():
            pytest.skip("Test fixture not found")
        
        with open(image_path, 'rb') as f:
            files = {'image': ('knife.jpg', f, 'image/jpeg')}
            headers = {'Authorization': 'Bearer invalid_token_here'}
            
            response = requests.post(
                f"{BASE_URL}/detect",
                files=files,
                headers=headers
            )
        
        assert response.status_code == 401
    
    def test_08_missing_authentication(self):
        """Test detection requires authentication."""
        image_path = Path("tests/fixtures/knife_high_conf.jpg")
        
        if not image_path.exists():
            pytest.skip("Test fixture not found")
        
        with open(image_path, 'rb') as f:
            files = {'image': ('knife.jpg', f, 'image/jpeg')}
            
            response = requests.post(
                f"{BASE_URL}/detect",
                files=files
            )
        
        assert response.status_code == 403


class TestPerformanceBenchmarks:
    """Performance and load testing."""
    
    def test_detection_latency_stats(self, test_user_token):
        """Benchmark detection latency over 10 requests."""
        image_path = Path("tests/fixtures/knife_high_conf.jpg")
        
        if not image_path.exists():
            pytest.skip("Test fixture not found")
        
        latencies = []
        
        for i in range(10):
            with open(image_path, 'rb') as f:
                files = {'image': ('knife.jpg', f, 'image/jpeg')}
                headers = {'Authorization': f'Bearer {test_user_token}'}
                
                start = time.time()
                response = requests.post(
                    f"{BASE_URL}/detect",
                    files=files,
                    headers=headers
                )
                latency = (time.time() - start) * 1000
                latencies.append(latency)
                
                assert response.status_code == 200
        
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        min_latency = min(latencies)
        
        print(f"\nPerformance Statistics (n={len(latencies)}):")
        print(f"  Average: {avg_latency:.1f}ms")
        print(f"  Min: {min_latency:.1f}ms")
        print(f"  Max: {max_latency:.1f}ms")
        
        assert avg_latency < MAX_LATENCY_MS, f"Average latency {avg_latency:.1f}ms exceeds {MAX_LATENCY_MS}ms"
        assert max_latency < MAX_LATENCY_MS * 1.5, f"Max latency {max_latency:.1f}ms exceeds threshold"  # Allow 50% overhead for worst case

