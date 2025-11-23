"""
Pytest configuration and shared fixtures for E2E tests.

This file contains shared fixtures and configuration that are
available to all test files in the tests/ directory.
"""
import pytest
import requests
import time
from pathlib import Path

BASE_URL = "http://localhost:8000"


@pytest.fixture(scope="session")
def base_url():
    """Base URL for API."""
    return BASE_URL


@pytest.fixture(scope="session")
def test_user():
    """Test user credentials."""
    return {
        "username": f"test_e2e_{int(time.time())}",
        "password": "TestPass123!@#"
    }


@pytest.fixture(scope="session")
def test_user_token(test_user, base_url):
    """Register user and get JWT token."""
    # Register
    response = requests.post(
        f"{base_url}/api/auth",
        json=test_user
    )
    assert response.status_code in [201, 400]  # 400 if already exists
    
    # Login
    response = requests.post(
        f"{base_url}/api/login",
        json=test_user
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture(scope="session")
def test_fixtures_dir():
    """Path to test fixtures directory."""
    path = Path(__file__).parent / "fixtures"
    path.mkdir(exist_ok=True)
    return path


@pytest.fixture(scope="session", autouse=True)
def check_backend_running(base_url):
    """Ensure backend is running before tests."""
    try:
        response = requests.get(f"{base_url}/detect/health", timeout=5)
        assert response.status_code == 200
        print(f"\n✓ Backend is running at {base_url}")
    except Exception as e:
        pytest.exit(f"Backend not running at {base_url}. Start it first: {e}")


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )

