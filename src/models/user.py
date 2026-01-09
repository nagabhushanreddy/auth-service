"""User models"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    """Base user model"""
    username: str = Field(..., min_length=3, max_length=30)
    email: EmailStr
    phone: Optional[str] = None


class UserRegister(UserBase):
    """User registration model"""
    password: str = Field(..., min_length=8)
    mfa_enabled: bool = False
    mfa_method: str = Field(default="none", pattern="^(sms|email|none)$")


class UserLogin(BaseModel):
    """User login model"""
    username: str
    password: str
    mfa_code: Optional[str] = None


class UserResponse(BaseModel):
    """User response model (no sensitive data)"""
    id: str
    username: str
    email: str
    phone: Optional[str] = None
    mfa_enabled: bool
    mfa_method: str
    status: str
    created_at: datetime


class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginResponse(BaseModel):
    """Login response model"""
    user: UserResponse
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


class VerifyOtpRequest(BaseModel):
    """Verify OTP request"""
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)


class PasswordResetRequest(BaseModel):
    """Password reset request"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation"""
    token: str
    password: str = Field(..., min_length=8)


class ApiKeyGenerate(BaseModel):
    """API key generation request"""
    name: str = Field(..., min_length=3, max_length=100)
    expires_in: Optional[int] = None


class ApiKeyResponse(BaseModel):
    """API key response"""
    id: str
    key: str
    name: str
    message: str


class ApiKeyRecord(BaseModel):
    """API key record (without the key itself)"""
    id: str
    name: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    active: bool
