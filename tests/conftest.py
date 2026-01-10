"""Test configuration"""
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Add parent directory to path so we can import main
sys.path.insert(0, str(Path(__file__).parent.parent))
from main import app

client = TestClient(app)


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
