"""Test authentication endpoints"""
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from main import app

client = TestClient(app)


class TestAuthEndpoints:
    """Authentication endpoint tests"""
    
    def test_register_user(self, test_user_data):
        """Test user registration"""
        response = client.post("/auth/register", json=test_user_data)
        assert response.status_code == 201
        assert response.json()["success"] is True
        assert response.json()["data"]["username"] == "testuser"
    
    def test_register_duplicate_username(self, test_user_data):
        """Test duplicate username registration"""
        client.post("/auth/register", json=test_user_data)
        
        response = client.post("/auth/register", json=test_user_data)
        assert response.status_code == 400
        assert response.json()["success"] is False
    
    def test_login_success(self, test_user_data):
        """Test successful login"""
        client.post("/auth/register", json=test_user_data)
        
        response = client.post("/auth/login", json={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert "access_token" in response.json()["data"]
        assert "refresh_token" in response.json()["data"]
    
    def test_login_invalid_password(self, test_user_data):
        """Test login with invalid password"""
        client.post("/auth/register", json=test_user_data)
        
        response = client.post("/auth/login", json={
            "username": test_user_data["username"],
            "password": "WrongPassword123!"
        })
        
        assert response.status_code == 401
        assert response.json()["success"] is False
    
    def test_login_nonexistent_user(self):
        """Test login with nonexistent user"""
        response = client.post("/auth/login", json={
            "username": "nonexistent",
            "password": "Password123!"
        })
        
        assert response.status_code == 401
        assert response.json()["success"] is False
    
    def test_refresh_token(self, test_user_data):
        """Test token refresh"""
        client.post("/auth/register", json=test_user_data)
        
        login_response = client.post("/auth/login", json={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })
        
        refresh_token = login_response.json()["data"]["refresh_token"]
        
        response = client.post("/auth/refresh", json={
            "refresh_token": refresh_token
        })
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert "access_token" in response.json()["data"]
    
    def test_logout(self, test_user_data):
        """Test logout"""
        client.post("/auth/register", json=test_user_data)
        
        login_response = client.post("/auth/login", json={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })
        
        access_token = login_response.json()["data"]["access_token"]
        
        response = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200
        assert response.json()["success"] is True


class TestApiKeyEndpoints:
    """API key endpoint tests"""
    
    def test_generate_api_key(self, test_user_data):
        """Test API key generation"""
        client.post("/auth/register", json=test_user_data)
        
        login_response = client.post("/auth/login", json={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })
        
        access_token = login_response.json()["data"]["access_token"]
        
        response = client.post(
            "/auth/api-keys",
            json={"name": "Test API Key"},
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 201
        assert response.json()["success"] is True
        assert "key" in response.json()["data"]
    
    def test_list_api_keys(self, test_user_data):
        """Test API key listing"""
        client.post("/auth/register", json=test_user_data)
        
        login_response = client.post("/auth/login", json={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })
        
        access_token = login_response.json()["data"]["access_token"]
        
        client.post(
            "/auth/api-keys",
            json={"name": "Test API Key"},
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        response = client.get(
            "/auth/api-keys",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert len(response.json()["data"]) > 0
