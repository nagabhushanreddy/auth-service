"""Test services"""
import sys
from pathlib import Path
import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.services.auth_service import AuthService
from app.services.jwt_service import JwtService
from app.services.otp_service import OtpService
from app.services.api_key_service import ApiKeyService


class TestAuthService:
    """Auth service tests"""
    
    def test_register_user(self):
        """Test user registration"""
        user = AuthService.register_user(
            "testuser",
            "test@example.com",
            "TestPassword123!"
        )
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.status == "active"
    
    def test_password_hashing(self):
        """Test password hashing"""
        password = "TestPassword123!"
        hashed = AuthService.hash_password(password)
        
        assert hashed != password
        assert AuthService.verify_password(password, hashed)
        assert not AuthService.verify_password("WrongPassword123!", hashed)
    
    def test_password_strength(self):
        """Test password strength validation"""
        assert AuthService.is_password_strong("TestPassword123!")
        assert not AuthService.is_password_strong("weak")
        assert not AuthService.is_password_strong("Nonum123")


class TestJwtService:
    """JWT service tests"""
    
    def test_issue_token_pair(self):
        """Test token pair generation"""
        tokens = JwtService.issue_token_pair(
            user_id="123",
            username="testuser",
            email="test@example.com"
        )
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
    
    def test_verify_access_token(self):
        """Test access token verification"""
        tokens = JwtService.issue_token_pair(
            user_id="123",
            username="testuser",
            email="test@example.com"
        )
        
        payload = JwtService.verify_access_token(tokens["access_token"])
        assert payload["user_id"] == "123"
        assert payload["username"] == "testuser"


class TestOtpService:
    """OTP service tests"""
    
    def test_generate_otp(self):
        """Test OTP generation"""
        otp, expires_in = OtpService.generate_otp("test@example.com")
        
        assert len(otp) == 6
        assert otp.isdigit()
        assert expires_in > 0
    
    def test_verify_otp(self):
        """Test OTP verification"""
        email = "test@example.com"
        otp, _ = OtpService.generate_otp(email)
        
        assert OtpService.verify_otp(email, otp)
        assert not OtpService.verify_otp(email, "000000")


class TestApiKeyService:
    """API key service tests"""
    
    def test_generate_api_key(self):
        """Test API key generation"""
        key_data = ApiKeyService.generate_api_key(
            user_id="123",
            name="Test API Key"
        )
        
        assert key_data["api_key_id"]
        assert key_data["plain_key"]
        assert len(key_data["plain_key"]) > 20
    
    def test_validate_api_key(self):
        """Test API key validation"""
        key_data = ApiKeyService.generate_api_key(
            user_id="123",
            name="Test API Key"
        )
        
        result = ApiKeyService.validate_api_key(key_data["plain_key"])
        assert result is not None
        assert result[0] == "123"
