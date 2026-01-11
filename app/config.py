"""Auth Service Configuration - Uses utils-service config loader"""
from typing import Optional, List
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from utils import config  # Simplified import - config is auto-initialized
from utils import logger, init_utils

# Initialize utils with config and logger
_CONFIG_DIR = Path(os.environ.get("CONFIG_DIR", "config"))
init_utils(str(_CONFIG_DIR))

class Settings(BaseSettings):
    """Auth Service settings loaded from config files and environment.
    
    Config files (config/app.yaml, config/logging.yaml) are loaded by 
    utils.config.Config and can be accessed via config.get() method.
    
    This class provides convenient access to configuration with defaults.
    """
    
    # Application
    @property
    def app_name(self) -> str:
        return config.get("service.name", "Auth Service")
    
    @property
    def debug(self) -> bool:
        return config.get("service.debug", False)
    
    @property
    def environment(self) -> str:
        return config.get("service.environment", "development")
    
    # Server
    @property
    def host(self) -> str:
        return config.get("server.host", "0.0.0.0")
    
    @property
    def port(self) -> int:
        return int(config.get("server.port", 3001))
    
    # JWT Configuration
    @property
    def jwt_access_secret(self) -> str:
        return config.get("jwt.access_secret", "your-super-secret-access-key-min-32-chars")
    
    @property
    def jwt_refresh_secret(self) -> str:
        return config.get("jwt.refresh_secret", "your-super-secret-refresh-key-min-32-chars")
    
    @property
    def jwt_access_expiry(self) -> int:
        return int(config.get("jwt.access_expiry", 900))
    
    @property
    def jwt_refresh_expiry(self) -> int:
        return int(config.get("jwt.refresh_expiry", 604800))
    
    @property
    def jwt_algorithm(self) -> str:
        return config.get("jwt.algorithm", "HS256")
    
    # API Key Configuration
    @property
    def api_key_secret(self) -> str:
        return config.get("api_key.secret", "your-api-key-secret")
    
    # Rate Limiting
    @property
    def rate_limit_window_ms(self) -> int:
        return int(config.get("rate_limiting.window_ms", 900000))
    
    @property
    def rate_limit_max_requests(self) -> int:
        return int(config.get("rate_limiting.max_requests", 100))
    
    @property
    def brute_force_max_attempts(self) -> int:
        return int(config.get("rate_limiting.brute_force_max_attempts", 5))
    
    @property
    def brute_force_lock_time(self) -> int:
        return int(config.get("rate_limiting.brute_force_lock_time", 900000))
    
    # CORS
    @property
    def cors_origins(self) -> List[str]:
        return config.get("cors.origins", ["http://localhost:3000", "http://localhost:3001"])
    
    # OAuth2 SSO
    @property
    def google_client_id(self) -> Optional[str]:
        return config.get("oauth.google.client_id")
    
    @property
    def google_client_secret(self) -> Optional[str]:
        return config.get("oauth.google.client_secret")
    
    @property
    def google_redirect_uri(self) -> Optional[str]:
        return config.get("oauth.google.redirect_uri")
    
    @property
    def facebook_client_id(self) -> Optional[str]:
        return config.get("oauth.facebook.client_id")
    
    @property
    def facebook_client_secret(self) -> Optional[str]:
        return config.get("oauth.facebook.client_secret")
    
    @property
    def facebook_redirect_uri(self) -> Optional[str]:
        return config.get("oauth.facebook.redirect_uri")
    
    @property
    def microsoft_client_id(self) -> Optional[str]:
        return config.get("oauth.microsoft.client_id")
    
    @property
    def microsoft_client_secret(self) -> Optional[str]:
        return config.get("oauth.microsoft.client_secret")
    
    @property
    def microsoft_redirect_uri(self) -> Optional[str]:
        return config.get("oauth.microsoft.redirect_uri")
    
    # MFA
    @property
    def mfa_otp_length(self) -> int:
        return int(config.get("mfa.otp_length", 6))
    
    @property
    def mfa_otp_expiry(self) -> int:
        return int(config.get("mfa.otp_expiry", 300))
    
    @property
    def mfa_otp_attempts(self) -> int:
        return int(config.get("mfa.otp_attempts", 3))
    
    # Redis (optional, falls back to in-memory)
    @property
    def redis_host(self) -> str:
        return config.get("redis.host", "localhost")
    
    @property
    def redis_port(self) -> int:
        return int(config.get("redis.port", 6379))
    
    @property
    def redis_db(self) -> int:
        return int(config.get("redis.db", 0))
    
    # Entity Service URL
    @property
    def entity_service_url(self) -> str:
        return config.get("external_services.entity_service.url", "http://localhost:3002")
    
    # Frontend URL (for password reset links)
    @property
    def frontend_url(self) -> str:
        return config.get("external_services.frontend.url", "http://localhost:3000")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env file


settings = Settings()
