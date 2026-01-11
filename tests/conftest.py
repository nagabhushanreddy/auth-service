"""Test configuration"""
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Add parent directory to path so we can import main
sys.path.insert(0, str(Path(__file__).parent.parent))
from main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_stores():
    """Reset all global in-memory stores before each test for proper isolation"""
    # Import stores after main is loaded
    from app.services.auth_service import _user_store
    from app.services.otp_service import _otp_store
    from app.services.api_key_service import _api_key_store
    from app.services.password_reset_service import _reset_token_store
    
    # Clear all stores before test
    _user_store.clear()
    _otp_store.clear()
    _api_key_store.clear()
    _reset_token_store.clear()
    
    yield  # Test runs here
    
    # Optional: cleanup after test (already cleared at start of next test)


@pytest.fixture
def test_client():
    """Test client fixture"""
    return client


@pytest.fixture
def test_user_data():
    """Test user data"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPassword123!",
        "phone": "1234567890"
    }
