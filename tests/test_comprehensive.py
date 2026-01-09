"""Comprehensive test suite for auth-service"""
import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.services.auth_service import AuthService
from src.services.jwt_service import JwtService
from src.services.otp_service import OtpService
from src.services.api_key_service import ApiKeyService
from src.cache import TokenBlacklist, RateLimiter
import time

client = TestClient(app)


class TestUserAuthentication:
    """User registration and authentication tests"""
    
    def test_register_user_success(self):
        """Test successful user registration"""
        response = client.post("/auth/register", json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "phone": "+1234567890",
            "mfa_enabled": False,
            "mfa_method": "none"
        })
        assert response.status_code == 201
        assert response.json()["success"] is True
        assert response.json()["data"]["username"] == "newuser"
    
    def test_register_weak_password(self):
        """Test registration with weak password"""
        response = client.post("/auth/register", json={
            "username": "weakpwd",
            "email": "weak@example.com",
            "password": "weak",  # Too short, no special chars
            "mfa_enabled": False,
            "mfa_method": "none"
        })
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "WEAK_PASSWORD"
    
    def test_register_duplicate_username(self):
        """Test duplicate username rejection"""
        user_data = {
            "username": "dupuser",
            "email": "dup1@example.com",
            "password": "SecurePass123!",
            "mfa_enabled": False,
            "mfa_method": "none"
        }
        client.post("/auth/register", json=user_data)
        
        response = client.post("/auth/register", json={
            **user_data,
            "email": "dup2@example.com"  # Different email
        })
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "REGISTRATION_FAILED"
    
    def test_register_duplicate_email(self):
        """Test duplicate email rejection"""
        user_data = {
            "username": "user1",
            "email": "dup@example.com",
            "password": "SecurePass123!",
            "mfa_enabled": False,
            "mfa_method": "none"
        }
        client.post("/auth/register", json=user_data)
        
        response = client.post("/auth/register", json={
            **user_data,
            "username": "user2"  # Different username
        })
        assert response.status_code == 400
    
    def test_login_success(self):
        """Test successful login"""
        client.post("/auth/register", json={
            "username": "logintest",
            "email": "login@example.com",
            "password": "SecurePass123!",
            "mfa_enabled": False,
            "mfa_method": "none"
        })
        
        response = client.post("/auth/login", json={
            "username": "logintest",
            "password": "SecurePass123!"
        })
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert "access_token" in response.json()["data"]
        assert "refresh_token" in response.json()["data"]
    
    def test_login_invalid_username(self):
        """Test login with non-existent user"""
        response = client.post("/auth/login", json={
            "username": "nonexistent",
            "password": "AnyPassword123!"
        })
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "LOGIN_FAILED"
    
    def test_login_invalid_password(self):
        """Test login with wrong password"""
        client.post("/auth/register", json={
            "username": "wrongpwd",
            "email": "wrong@example.com",
            "password": "CorrectPass123!",
            "mfa_enabled": False,
            "mfa_method": "none"
        })
        
        response = client.post("/auth/login", json={
            "username": "wrongpwd",
            "password": "WrongPass123!"
        })
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "LOGIN_FAILED"


class TestAccountLocking:
    """Account locking after failed attempts tests"""
    
    def test_account_lock_after_failed_attempts(self):
        """Test account locking after 5 failed login attempts"""
        username = "locktest"
        email = "locktest@example.com"
        correct_password = "CorrectPass123!"
        
        # Register user
        client.post("/auth/register", json={
            "username": username,
            "email": email,
            "password": correct_password,
            "mfa_enabled": False,
            "mfa_method": "none"
        })
        
        # Make 5 failed login attempts
        for i in range(5):
            response = client.post("/auth/login", json={
                "username": username,
                "password": f"WrongPass{i}!"
            })
            assert response.status_code == 401
        
        # 6th attempt should show account locked
        response = client.post("/auth/login", json={
            "username": username,
            "password": correct_password
        })
        assert response.status_code == 401
        assert "locked" in response.json()["error"]["message"].lower()
    
    def test_failed_attempt_counter_reset_on_success(self):
        """Test that failed attempt counter resets on successful login"""
        username = "resetcounter"
        email = "reset@example.com"
        correct_password = "CorrectPass123!"
        
        # Register
        client.post("/auth/register", json={
            "username": username,
            "email": email,
            "password": correct_password,
            "mfa_enabled": False,
            "mfa_method": "none"
        })
        
        # Make 3 failed attempts
        for i in range(3):
            client.post("/auth/login", json={
                "username": username,
                "password": f"Wrong{i}!"
            })
        
        # Successful login should reset counter
        response = client.post("/auth/login", json={
            "username": username,
            "password": correct_password
        })
        assert response.status_code == 200
        
        # Now 4 more failed attempts (less than 5 total after reset)
        for i in range(4):
            response = client.post("/auth/login", json={
                "username": username,
                "password": f"Still{i}Wrong!"
            })
            assert response.status_code == 401
        
        # Still not locked (4 attempts after reset)
        response = client.post("/auth/login", json={
            "username": username,
            "password": correct_password
        })
        # Should work (not yet 5 failed attempts)
        assert response.status_code == 200 or response.status_code == 401


class TestTokenManagement:
    """JWT token management tests"""
    
    def test_token_pair_generation(self):
        """Test access and refresh token generation"""
        tokens = JwtService.issue_token_pair(
            user_id="test-user-123",
            username="testuser",
            email="test@example.com"
        )
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
        assert tokens["expires_in"] == 900  # 15 minutes
    
    def test_token_verification(self):
        """Test token verification"""
        tokens = JwtService.issue_token_pair(
            user_id="test-user",
            username="testuser",
            email="test@example.com"
        )
        
        payload = JwtService.verify_access_token(tokens["access_token"])
        assert payload["user_id"] == "test-user"
        assert payload["username"] == "testuser"
        assert payload["email"] == "test@example.com"
    
    def test_token_refresh(self):
        """Test token refresh flow"""
        tokens = JwtService.issue_token_pair(
            user_id="test-user",
            username="testuser",
            email="test@example.com"
        )
        
        new_tokens = JwtService.refresh_access_token(tokens["refresh_token"])
        
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens
        assert new_tokens["access_token"] != tokens["access_token"]
    
    def test_token_blacklisting(self):
        """Test token revocation"""
        tokens = JwtService.issue_token_pair(
            user_id="test-user",
            username="testuser",
            email="test@example.com"
        )
        
        # Token should be valid initially
        payload = JwtService.verify_access_token(tokens["access_token"])
        assert payload["user_id"] == "test-user"
        
        # Revoke token
        JwtService.revoke_token(tokens["access_token"])
        
        # Token should now be invalid
        with pytest.raises(ValueError, match="revoked"):
            JwtService.verify_access_token(tokens["access_token"])
    
    def test_expired_token_rejection(self):
        """Test that expired tokens are rejected"""
        import jwt as jwt_lib
        from src.config import settings
        from datetime import datetime, timedelta
        
        # Create expired token
        expired_payload = {
            "user_id": "test-user",
            "username": "testuser",
            "email": "test@example.com",
            "exp": datetime.utcnow() - timedelta(hours=1),
            "iss": "auth-service",
            "aud": "api"
        }
        
        expired_token = jwt_lib.encode(
            expired_payload,
            settings.jwt_access_secret,
            algorithm=settings.jwt_algorithm
        )
        
        with pytest.raises(ValueError, match="expired"):
            JwtService.verify_access_token(expired_token)


class TestOTP:
    """OTP/MFA tests"""
    
    def test_otp_generation(self):
        """Test OTP generation"""
        otp, ref = OtpService.generate_otp("test@example.com")
        
        assert len(otp) == 6
        assert otp.isdigit()
        assert ref is not None
    
    def test_otp_verification_success(self):
        """Test successful OTP verification"""
        email = "otp@example.com"
        otp, ref = OtpService.generate_otp(email)
        
        result = OtpService.verify_otp(email, otp)
        assert result is True
    
    def test_otp_verification_wrong_otp(self):
        """Test OTP verification with wrong code"""
        email = "wrong@example.com"
        OtpService.generate_otp(email)
        
        result = OtpService.verify_otp(email, "000000")
        assert result is False
    
    def test_otp_max_attempts_exceeded(self):
        """Test OTP verification after max attempts"""
        email = "maxattempts@example.com"
        OtpService.generate_otp(email)
        
        # Try 3 wrong codes
        for i in range(3):
            OtpService.verify_otp(email, f"00000{i}")
        
        # 4th attempt should fail (max is 3)
        result = OtpService.verify_otp(email, "000004")
        assert result is False


class TestAPIKeys:
    """API key management tests"""
    
    def test_api_key_generation(self):
        """Test API key generation"""
        user_id = "test-user"
        key_data = ApiKeyService.generate_api_key(user_id, "test-key", None)
        
        assert "api_key_id" in key_data
        assert "plain_key" in key_data
        assert "key_preview" in key_data
    
    def test_api_key_validation(self):
        """Test API key validation"""
        user_id = "test-user"
        key_data = ApiKeyService.generate_api_key(user_id, "test-key", None)
        
        # Validate with correct key
        result = ApiKeyService.validate_api_key(key_data["plain_key"])
        assert result is not None
        user_id_val, key_id = result
        assert user_id_val == user_id
    
    def test_api_key_revocation(self):
        """Test API key revocation"""
        user_id = "test-user"
        key_data = ApiKeyService.generate_api_key(user_id, "test-key", None)
        plain_key = key_data["plain_key"]
        
        # Validate before revocation
        result = ApiKeyService.validate_api_key(plain_key)
        assert result is not None
        
        # Revoke
        ApiKeyService.revoke_api_key(key_data["api_key_id"])
        
        # Should now be invalid
        result = ApiKeyService.validate_api_key(plain_key)
        assert result is None


class TestRateLimiting:
    """Rate limiting tests"""
    
    def test_rate_limit_allows_requests_within_limit(self):
        """Test that requests within rate limit are allowed"""
        key = f"test-ip-{time.time()}"
        max_requests = 5
        window_seconds = 60
        
        for i in range(max_requests):
            result = RateLimiter.is_allowed(key, max_requests, window_seconds)
            assert result is True
    
    def test_rate_limit_rejects_requests_exceeding_limit(self):
        """Test that requests exceeding rate limit are rejected"""
        key = f"test-ip-exceed-{time.time()}"
        max_requests = 3
        window_seconds = 60
        
        # Allow max requests
        for i in range(max_requests):
            RateLimiter.is_allowed(key, max_requests, window_seconds)
        
        # Next request should be rejected
        result = RateLimiter.is_allowed(key, max_requests, window_seconds)
        assert result is False


class TestHealthCheck:
    """Health check endpoint tests"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "OK"
        assert response.json()["service"] == "auth-service"


class TestOpenAPIDocumentation:
    """OpenAPI documentation tests"""
    
    def test_v3_api_docs_endpoint(self):
        """Test /v3/api-docs endpoint"""
        response = client.get("/v3/api-docs")
        assert response.status_code == 200
        
        spec = response.json()
        assert "openapi" in spec
        assert spec["info"]["title"] == "Identity & Authentication Service"
    
    def test_api_docs_has_required_endpoints(self):
        """Test that OpenAPI spec includes all required endpoints"""
        response = client.get("/v3/api-docs")
        spec = response.json()
        
        required_paths = [
            "/auth/register",
            "/auth/login",
            "/auth/verify-otp",
            "/auth/refresh",
            "/auth/logout",
            "/auth/api-keys",
            "/auth/password-reset",
            "/health"
        ]
        
        paths = spec.get("paths", {})
        for path in required_paths:
            assert path in paths, f"Missing endpoint: {path}"


class TestErrorHandling:
    """Error handling and response format tests"""
    
    def test_error_response_format(self):
        """Test that errors follow standardized format"""
        response = client.post("/auth/login", json={
            "username": "nonexistent",
            "password": "anypassword"
        })
        
        body = response.json()
        assert "success" in body
        assert "error" in body
        assert "metadata" in body
        assert "correlation_id" in body["metadata"]
    
    def test_correlation_id_propagation(self):
        """Test that correlation ID is propagated in responses"""
        response = client.get("/health", headers={
            "X-Correlation-ID": "test-correlation-123"
        })
        
        assert response.headers["X-Correlation-ID"] == "test-correlation-123"


class TestMFALoginFlow:
    """MFA login flow tests"""
    
    def test_register_with_mfa_enabled(self):
        """Test registration with MFA enabled"""
        response = client.post("/auth/register", json={
            "username": "mfauser",
            "email": "mfa@example.com",
            "password": "SecurePass123!",
            "mfa_enabled": True,
            "mfa_method": "email"
        })
        
        assert response.status_code == 201
        assert response.json()["data"]["mfa_enabled"] is True
        assert response.json()["data"]["mfa_method"] == "email"
    
    def test_login_with_mfa_required(self):
        """Test login flow when MFA is required"""
        client.post("/auth/register", json={
            "username": "mfalogin",
            "email": "mfalogin@example.com",
            "password": "SecurePass123!",
            "mfa_enabled": True,
            "mfa_method": "email"
        })
        
        response = client.post("/auth/login", json={
            "username": "mfalogin",
            "password": "SecurePass123!"
        })
        
        assert response.status_code == 200
        assert response.json()["data"]["mfa_required"] is True
        assert "access_token" not in response.json()["data"]  # No token until MFA verified


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src", "--cov-report=html", "--cov-report=xml"])
