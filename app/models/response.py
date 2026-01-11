"""Response models and utilities"""
from typing import Any, Dict, Optional
from datetime import datetime, timezone
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Error detail model"""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class Metadata(BaseModel):
    """Response metadata"""
    timestamp: str
    correlation_id: Optional[str] = None


class ApiResponse(BaseModel):
    """Generic API response wrapper"""
    success: bool
    data: Optional[Any] = None
    error: Optional[ErrorDetail] = None
    metadata: Metadata


class AppException(Exception):
    """Custom application exception"""
    
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


def create_success_response(
    data: Any,
    correlation_id: Optional[str] = None
) -> ApiResponse:
    """Create a successful API response"""
    return ApiResponse(
        success=True,
        data=data,
        metadata=Metadata(
            timestamp=datetime.now(timezone.utc).isoformat(),
            correlation_id=correlation_id
        )
    )


def create_error_response(
    code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None
) -> ApiResponse:
    """Create an error API response"""
    return ApiResponse(
        success=False,
        error=ErrorDetail(code=code, message=message, details=details),
        metadata=Metadata(
            timestamp=datetime.now(timezone.utc).isoformat(),
            correlation_id=correlation_id
        )
    )
