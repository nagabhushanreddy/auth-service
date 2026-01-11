"""Main FastAPI application"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import uvicorn

from utils import logger
from app.config import settings
from app.models.response import AppException, create_error_response
from app.middleware import correlation_id_middleware, rate_limit_middleware
from app.routes import auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan"""
    # Startup
    logger.info("Starting Auth Service initialization...")
    logger.info("Auth Service initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Auth service shutting down")


# Create FastAPI app
app = FastAPI(
    title="Identity & Authentication Service",
    description="OpenAPI specification for the Multi-Finance Authentication Service",
    version="1.0.0",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure as needed
)

app.middleware("http")(rate_limit_middleware)
app.middleware("http")(correlation_id_middleware)


# Health check endpoint
@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "OK",
        "service": "auth-service",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# OpenAPI endpoint per requirements
@app.get("/v3/api-docs", include_in_schema=False)
async def openapi_spec():
    return app.openapi()


# Include routes
app.include_router(auth.router)


# Exception handlers
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle application exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            exc.code,
            exc.message,
            exc.details,
            getattr(request, 'correlation_id', None)
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            "INTERNAL_ERROR",
            "Internal server error",
            correlation_id=getattr(request, 'correlation_id', None)
        ).model_dump()
    )


# 404 handler
@app.exception_handler(status.HTTP_404_NOT_FOUND)
async def not_found_exception_handler(request: Request, exc: Exception):
    """Handle 404 exceptions"""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=create_error_response(
            "NOT_FOUND",
            "Route not found",
            correlation_id=getattr(request, 'correlation_id', None)
        ).model_dump()
    )


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development"
    )
