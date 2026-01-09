"""Middleware for authentication, rate limiting, and request handling"""
from fastapi import HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
import uuid
from src.services.jwt_service import JwtService
from src.services.api_key_service import ApiKeyService
from src.config import settings
from src.cache import RateLimiter
from utils import logger

security = HTTPBearer(auto_error=False)


async def correlation_id_middleware(request: Request, call_next):
    """Add correlation ID to request"""
    correlation_id = request.headers.get("x-correlation-id") or str(uuid.uuid4())
    request.correlation_id = correlation_id
    request.reset_link_base = request.headers.get("x-reset-link-base", "http://localhost:3000")
    
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    
    return response


async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting per client IP"""
    client_ip = request.client.host if request.client else "unknown"
    max_requests = settings.rate_limit_max_requests
    window_seconds = settings.rate_limit_window_ms // 1000
    
    if not RateLimiter.is_allowed(client_ip, max_requests, window_seconds):
        remaining = RateLimiter.get_remaining(client_ip, max_requests)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"code": "RATE_LIMIT_EXCEEDED", "message": "Too many requests"},
            headers={
                "Retry-After": str(max(1, window_seconds)),
                "X-RateLimit-Remaining": str(remaining)
            }
        )
    
    return await call_next(request)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Get current user from JWT token or API key"""
    
    # Try JWT first
    if credentials:
        token = credentials.credentials
        try:
            payload = JwtService.verify_access_token(token)
            return {
                "user_id": payload["user_id"],
                "username": payload["username"],
                "email": payload["email"],
                "auth_type": "jwt"
            }
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_TOKEN", "message": str(e)}
            )
    
    # Try API Key
    api_key = request.headers.get("x-api-key")
    if api_key:
        result = ApiKeyService.validate_api_key(api_key)
        if result:
            user_id, key_id = result
            return {
                "user_id": user_id,
                "api_key_id": key_id,
                "auth_type": "api_key"
            }
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_API_KEY", "message": "API key is invalid or expired"}
        )
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "MISSING_AUTH", "message": "Bearer token or API key required"}
    )


def get_correlation_id(request: Request) -> str:
    """Get correlation ID from request"""
    return getattr(request, 'correlation_id', str(uuid.uuid4()))
