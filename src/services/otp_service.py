"""OTP service for MFA"""
import random
import string
from typing import Optional
from datetime import datetime, timedelta
from uuid import uuid4
from src.config import settings
from utils import logger


class OtpRecord:
    """OTP record"""
    
    def __init__(self, email: str, otp: str, expires_at: datetime):
        self.email = email
        self.otp = otp
        self.expires_at = expires_at
        self.attempts = 0
        self.verified = False


# In-memory OTP store (use Redis in production)
_otp_store: dict = {}


class OtpService:
    """One-Time Password service"""
    
    @staticmethod
    def generate_otp(email: str) -> tuple[str, int]:
        """Generate and store OTP"""
        otp = ''.join(random.choices(string.digits, k=settings.mfa_otp_length))
        expires_at = datetime.utcnow() + timedelta(seconds=settings.mfa_otp_expiry)
        
        key = str(uuid4())
        _otp_store[key] = OtpRecord(email, otp, expires_at)
        
        logger.info(f"OTP generated for {email}: {otp}")
        
        return otp, settings.mfa_otp_expiry
    
    @staticmethod
    def verify_otp(email: str, otp: str) -> bool:
        """Verify OTP"""
        for key, record in list(_otp_store.items()):
            if record.email == email and not record.verified:
                # Check expiry
                if datetime.utcnow() > record.expires_at:
                    del _otp_store[key]
                    logger.warn(f"OTP expired for {email}")
                    return False
                
                # Check attempts
                if record.attempts >= settings.mfa_otp_attempts:
                    del _otp_store[key]
                    logger.warn(f"OTP max attempts exceeded for {email}")
                    return False
                
                record.attempts += 1
                
                # Check OTP
                if record.otp == otp:
                    record.verified = True
                    logger.info(f"OTP verified for {email}")
                    return True
                
                return False
        
        logger.warn(f"OTP record not found for {email}")
        return False
    
    @staticmethod
    def is_otp_verified(email: str) -> bool:
        """Check if OTP is verified"""
        for record in _otp_store.values():
            if record.email == email and record.verified:
                return True
        return False
    
    @staticmethod
    def clear_otp(email: str) -> None:
        """Clear OTP for email"""
        for key, record in list(_otp_store.items()):
            if record.email == email:
                del _otp_store[key]
