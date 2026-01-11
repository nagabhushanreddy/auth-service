"""Authentication routes"""
from fastapi import APIRouter, Depends, status, Request
from typing import Optional
from app.models.user import (
    UserRegister, UserLogin, VerifyOtpRequest, RefreshTokenRequest,
    PasswordResetRequest, PasswordResetConfirm, ApiKeyGenerate,
    ApiKeyResponse, ApiKeyRecord
)
from app.models.response import create_success_response, create_error_response, AppException
from app.services.auth_service import AuthService
from app.services.jwt_service import JwtService
from app.services.otp_service import OtpService
from app.services.api_key_service import ApiKeyService
from app.services.password_reset_service import PasswordResetService
from app.services.notification_service import NotificationService
from utils import logger
from app.middleware import get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", status_code=201)
async def register(
    req: Request,
    user_data: UserRegister
):
    """Register a new user"""
    try:
        # Validate password strength
        if not AuthService.is_password_strong(user_data.password):
            raise AppException(
                code="WEAK_PASSWORD",
                message="Password must contain uppercase, lowercase, number, and special character",
                status_code=400
            )
        
        user = AuthService.register_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            phone=user_data.phone,
            mfa_enabled=user_data.mfa_enabled,
            mfa_method=user_data.mfa_method
        )
        
        # If MFA enabled, generate OTP
        if user_data.mfa_enabled:
            otp, _ = OtpService.generate_otp(user_data.email)
            await NotificationService.send_otp(user_data.email, otp, user_data.mfa_method)
        
        return create_success_response(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "mfa_enabled": user.mfa_enabled,
                "mfa_method": user.mfa_method,
            },
            getattr(req, 'correlation_id', None)
        )
    except ValueError as e:
        raise AppException(
            code="REGISTRATION_FAILED",
            message=str(e),
            status_code=400
        )


@router.post("/login")
async def login(
    req: Request,
    credentials: UserLogin
):
    """Login user"""
    try:
        user, mfa_required, mfa_method = AuthService.login_user(
            credentials.username,
            credentials.password
        )
        
        if mfa_required:
            return create_success_response(
                {
                    "mfa_required": True,
                    "mfa_method": mfa_method,
                    "message": f"Please verify OTP sent to your {mfa_method}"
                },
                getattr(req, 'correlation_id', None)
            )
        
        # Generate tokens
        tokens = JwtService.issue_token_pair(
            user_id=user.id,
            username=user.username,
            email=user.email
        )
        
        return create_success_response(
            {
                "user": user.to_dict(),
                **tokens
            },
            getattr(req, 'correlation_id', None)
        )
    except ValueError as e:
        raise AppException(
            code="LOGIN_FAILED",
            message=str(e),
            status_code=401
        )


@router.post("/verify-otp")
async def verify_otp(
    req: Request,
    otp_data: VerifyOtpRequest
):
    """Verify OTP for MFA"""
    try:
        is_valid = OtpService.verify_otp(otp_data.email, otp_data.otp)
        
        if not is_valid:
            raise AppException(
                code="INVALID_OTP",
                message="OTP verification failed",
                status_code=400
            )
        
        user = AuthService.get_user_by_email(otp_data.email)
        if not user:
            raise AppException(
                code="USER_NOT_FOUND",
                message="User not found",
                status_code=400
            )
        
        # Generate tokens
        tokens = JwtService.issue_token_pair(
            user_id=user.id,
            username=user.username,
            email=user.email
        )
        
        OtpService.clear_otp(otp_data.email)
        
        return create_success_response(
            {
                "user": user.to_dict(),
                **tokens
            },
            getattr(req, 'correlation_id', None)
        )
    except AppException:
        raise
    except Exception as e:
        raise AppException(
            code="OTP_VERIFICATION_FAILED",
            message=str(e),
            status_code=400
        )


@router.post("/refresh")
async def refresh(
    req: Request,
    token_data: RefreshTokenRequest
):
    """Refresh access token"""
    try:
        tokens = JwtService.refresh_access_token(token_data.refresh_token)
        
        return create_success_response(
            tokens,
            getattr(req, 'correlation_id', None)
        )
    except ValueError as e:
        raise AppException(
            code="REFRESH_FAILED",
            message=str(e),
            status_code=401
        )


@router.post("/logout")
async def logout(
    req: Request,
    current_user: dict = Depends(get_current_user)
):
    """Logout user"""
    try:
        auth_header = req.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            JwtService.revoke_token(token)
        
        return create_success_response(
            {"message": "Logged out successfully"},
            getattr(req, 'correlation_id', None)
        )
    except Exception as e:
        raise AppException(
            code="LOGOUT_FAILED",
            message=str(e),
            status_code=400
        )


@router.post("/api-keys", status_code=201)
async def generate_api_key(
    req: Request,
    key_data: ApiKeyGenerate,
    current_user: dict = Depends(get_current_user)
):
    """Generate API key"""
    try:
        api_key_data = ApiKeyService.generate_api_key(
            user_id=current_user["user_id"],
            name=key_data.name,
            expires_in_seconds=key_data.expires_in
        )
        
        return create_success_response(
            {
                "id": api_key_data["api_key_id"],
                "key": api_key_data["plain_key"],
                "message": "Save this key securely, you will not see it again"
            },
            getattr(req, 'correlation_id', None)
        )
    except Exception as e:
        raise AppException(
            code="API_KEY_GENERATION_FAILED",
            message=str(e),
            status_code=400
        )


@router.get("/api-keys")
async def list_api_keys(
    req: Request,
    current_user: dict = Depends(get_current_user)
):
    """List API keys"""
    try:
        keys = ApiKeyService.list_api_keys(current_user["user_id"])
        
        return create_success_response(
            keys,
            getattr(req, 'correlation_id', None)
        )
    except Exception as e:
        raise AppException(
            code="API_KEY_LIST_FAILED",
            message=str(e),
            status_code=400
        )


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    req: Request,
    key_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Revoke API key"""
    try:
        success = ApiKeyService.revoke_api_key(key_id, current_user["user_id"])
        
        if not success:
            raise AppException(
                code="API_KEY_NOT_FOUND",
                message="API key not found",
                status_code=404
            )
        
        return create_success_response(
            {"message": "API key revoked"},
            getattr(req, 'correlation_id', None)
        )
    except AppException:
        raise
    except Exception as e:
        raise AppException(
            code="API_KEY_REVOKE_FAILED",
            message=str(e),
            status_code=400
        )


@router.post("/password-reset")
async def request_password_reset(
    req: Request,
    data: PasswordResetRequest
):
    """Request password reset"""
    try:
        user = AuthService.get_user_by_email(data.email)
        
        if user:
            token, expires_in = PasswordResetService.generate_reset_token(user.id)
            reset_link_base = getattr(req, 'reset_link_base', 'http://localhost:3000')
            reset_link = f"{reset_link_base}/reset-password?token={token}"
            await NotificationService.send_password_reset_email(user.email, reset_link)
        
        # Don't reveal if email exists
        return create_success_response(
            {"message": "If email exists, reset link has been sent"},
            getattr(req, 'correlation_id', None)
        )
    except Exception as e:
        raise AppException(
            code="PASSWORD_RESET_FAILED",
            message=str(e),
            status_code=400
        )


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    req: Request,
    data: PasswordResetConfirm
):
    """Confirm password reset"""
    try:
        user_id = PasswordResetService.validate_token(data.token)
        
        if not user_id:
            raise AppException(
                code="INVALID_RESET_TOKEN",
                message="Reset token is invalid or expired",
                status_code=400
            )
        
        user = AuthService.get_user_by_id(user_id)
        if not user:
            raise AppException(
                code="USER_NOT_FOUND",
                message="User not found",
                status_code=400
            )
        
        # Validate password strength
        if not AuthService.is_password_strong(data.password):
            raise AppException(
                code="WEAK_PASSWORD",
                message="Password must contain uppercase, lowercase, number, and special character",
                status_code=400
            )
        
        # Update password
        AuthService.update_password(user_id, user.password_hash, data.password)
        PasswordResetService.mark_token_as_used(data.token)
        
        return create_success_response(
            {"message": "Password reset successfully"},
            getattr(req, 'correlation_id', None)
        )
    except AppException:
        raise
    except Exception as e:
        raise AppException(
            code="PASSWORD_RESET_FAILED",
            message=str(e),
            status_code=400
        )
