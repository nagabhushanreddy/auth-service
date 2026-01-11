"""Password reset service"""
from datetime import datetime, timedelta, timezone
from typing import Optional
import secrets
from app.config import settings
from utils import logger

RESET_TOKEN_EXPIRY = 3600  # 1 hour


class ResetToken:
    """Password reset token"""
    
    def __init__(self, user_id: str, token: str, expires_at: datetime):
        self.user_id = user_id
        self.token = token
        self.expires_at = expires_at
        self.used = False


# In-memory reset token storage (use database in production)
_reset_token_store: dict = {}


class PasswordResetService:
    """Password reset service"""
    
    @staticmethod
    def generate_reset_token(user_id: str) -> tuple[str, int]:
        """Generate password reset token"""
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=RESET_TOKEN_EXPIRY)
        
        _reset_token_store[token] = ResetToken(user_id, token, expires_at)
        
        logger.info(f"Password reset token generated for user: {user_id}")
        
        return token, RESET_TOKEN_EXPIRY
    
    @staticmethod
    def validate_token(token: str) -> Optional[str]:
        """Validate reset token, returns user_id or None"""
        record = _reset_token_store.get(token)
        
        if not record:
            logger.warning("Reset token not found")
            return None
        
        # Check expiry
        if datetime.now(timezone.utc) > record.expires_at:
            del _reset_token_store[token]
            logger.warning("Reset token expired")
            return None
        
        # Check if already used
        if record.used:
            logger.warning("Reset token already used")
            return None
        
        return record.user_id
    
    @staticmethod
    def mark_token_as_used(token: str) -> None:
        """Mark token as used"""
        record = _reset_token_store.get(token)
        if record:
            record.used = True
            logger.info("Reset token marked as used")
    
    @staticmethod
    def revoke_token(token: str) -> None:
        """Revoke token"""
        if token in _reset_token_store:
            del _reset_token_store[token]
            logger.info("Reset token revoked")
