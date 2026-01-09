"""JWT token service"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from src.config import settings
from utils import logger
from src.cache import TokenBlacklist


class JwtService:
    """JWT token management service"""
    
    @staticmethod
    def issue_token_pair(
        user_id: str,
        username: str,
        email: str,
        roles: Optional[list] = None,
        permissions: Optional[list] = None
    ) -> Dict[str, Any]:
        """Issue access and refresh tokens"""
        now = datetime.utcnow()
        
        # Access token payload
        access_payload = {
            "user_id": user_id,
            "username": username,
            "email": email,
            "roles": roles or [],
            "permissions": permissions or [],
            "iat": now,
            "exp": now + timedelta(seconds=settings.jwt_access_expiry),
            "iss": "auth-service",
            "aud": "api"
        }
        
        # Refresh token payload
        refresh_payload = {
            "user_id": user_id,
            "username": username,
            "email": email,
            "iat": now,
            "exp": now + timedelta(seconds=settings.jwt_refresh_expiry),
            "iss": "auth-service"
        }
        
        # Encode tokens
        access_token = jwt.encode(
            access_payload,
            settings.jwt_access_secret,
            algorithm=settings.jwt_algorithm
        )
        
        refresh_token = jwt.encode(
            refresh_payload,
            settings.jwt_refresh_secret,
            algorithm=settings.jwt_algorithm
        )
        
        expires_in = settings.jwt_access_expiry
        logger.info(f"Token pair issued for user: {user_id}")
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": expires_in
        }
    
    @staticmethod
    def verify_access_token(token: str) -> Dict[str, Any]:
        """Verify access token"""
        try:
            # Check blacklist
            if TokenBlacklist.is_blacklisted(token):
                raise ValueError("Token has been revoked")
            
            payload = jwt.decode(
                token,
                settings.jwt_access_secret,
                algorithms=[settings.jwt_algorithm],
                options={"verify_aud": True},
                audience="api",
                issuer="auth-service"
            )
            
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Access token has expired")
        except jwt.InvalidTokenError as e:
            logger.error(f"Token verification failed: {e}")
            raise ValueError("Invalid access token")
    
    @staticmethod
    def verify_refresh_token(token: str) -> Dict[str, Any]:
        """Verify refresh token"""
        try:
            # Check blacklist
            if TokenBlacklist.is_blacklisted(token):
                raise ValueError("Token has been revoked")
            
            payload = jwt.decode(
                token,
                settings.jwt_refresh_secret,
                algorithms=[settings.jwt_algorithm],
                issuer="auth-service"
            )
            
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Refresh token has expired")
        except jwt.InvalidTokenError as e:
            logger.error(f"Refresh token verification failed: {e}")
            raise ValueError("Invalid refresh token")
    
    @staticmethod
    def refresh_access_token(refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        payload = JwtService.verify_refresh_token(refresh_token)
        
        # Revoke old refresh token
        TokenBlacklist.add(refresh_token, settings.jwt_refresh_expiry)
        
        # Issue new token pair
        return JwtService.issue_token_pair(
            user_id=payload["user_id"],
            username=payload["username"],
            email=payload["email"]
        )
    
    @staticmethod
    def revoke_token(token: str) -> None:
        """Revoke a token"""
        TokenBlacklist.add(token, settings.jwt_access_expiry)
        logger.info("Token revoked")
    
    @staticmethod
    def decode_token(token: str) -> Optional[Dict[str, Any]]:
        """Decode token without verification"""
        try:
            return jwt.decode(
                token,
                options={"verify_signature": False}
            )
        except Exception:
            return None
