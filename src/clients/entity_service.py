"""Entity Service Client - Interface for persistence layer"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import httpx
from src.config import settings
from utils import logger


class EntityServiceClient:
    """Client for interacting with entity-service"""
    
    BASE_URL = getattr(settings, 'entity_service_url', "http://localhost:3002")
    TIMEOUT = 5.0
    
    @staticmethod
    async def create_user(
        username: str,
        email: str,
        password_hash: str,
        phone: Optional[str] = None,
        mfa_enabled: bool = False,
        mfa_method: str = "none"
    ) -> Dict[str, Any]:
        """Create a new user in entity-service"""
        try:
            async with httpx.AsyncClient(timeout=EntityServiceClient.TIMEOUT) as client:
                response = await client.post(
                    f"{EntityServiceClient.BASE_URL}/api/v1/users",
                    json={
                        "username": username,
                        "email": email,
                        "password_hash": password_hash,
                        "phone": phone,
                        "mfa_enabled": mfa_enabled,
                        "mfa_method": mfa_method,
                        "status": "active"
                    }
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Entity service create_user failed: {e}")
            raise ValueError(f"Failed to create user: {e}")
    
    @staticmethod
    async def get_user(user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            async with httpx.AsyncClient(timeout=EntityServiceClient.TIMEOUT) as client:
                response = await client.get(
                    f"{EntityServiceClient.BASE_URL}/api/v1/users/{user_id}"
                )
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Entity service get_user failed: {e}")
            return None
    
    @staticmethod
    async def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        try:
            async with httpx.AsyncClient(timeout=EntityServiceClient.TIMEOUT) as client:
                response = await client.get(
                    f"{EntityServiceClient.BASE_URL}/api/v1/users/username/{username}"
                )
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Entity service get_user_by_username failed: {e}")
            return None
    
    @staticmethod
    async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            async with httpx.AsyncClient(timeout=EntityServiceClient.TIMEOUT) as client:
                response = await client.get(
                    f"{EntityServiceClient.BASE_URL}/api/v1/users/email/{email}"
                )
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Entity service get_user_by_email failed: {e}")
            return None
    
    @staticmethod
    async def update_user(user_id: str, **kwargs) -> Dict[str, Any]:
        """Update user"""
        try:
            async with httpx.AsyncClient(timeout=EntityServiceClient.TIMEOUT) as client:
                response = await client.patch(
                    f"{EntityServiceClient.BASE_URL}/api/v1/users/{user_id}",
                    json=kwargs
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Entity service update_user failed: {e}")
            raise ValueError(f"Failed to update user: {e}")
    
    @staticmethod
    async def create_api_key(
        user_id: str,
        hashed_key: str,
        name: str,
        expires_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Create API key"""
        try:
            async with httpx.AsyncClient(timeout=EntityServiceClient.TIMEOUT) as client:
                response = await client.post(
                    f"{EntityServiceClient.BASE_URL}/api/v1/api-keys",
                    json={
                        "user_id": user_id,
                        "hashed_key": hashed_key,
                        "name": name,
                        "expires_at": expires_at.isoformat() if expires_at else None,
                        "active": True
                    }
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Entity service create_api_key failed: {e}")
            raise ValueError(f"Failed to create API key: {e}")
    
    @staticmethod
    async def get_api_key(key_id: str) -> Optional[Dict[str, Any]]:
        """Get API key by ID"""
        try:
            async with httpx.AsyncClient(timeout=EntityServiceClient.TIMEOUT) as client:
                response = await client.get(
                    f"{EntityServiceClient.BASE_URL}/api/v1/api-keys/{key_id}"
                )
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Entity service get_api_key failed: {e}")
            return None
    
    @staticmethod
    async def list_api_keys(user_id: str) -> List[Dict[str, Any]]:
        """List API keys for user"""
        try:
            async with httpx.AsyncClient(timeout=EntityServiceClient.TIMEOUT) as client:
                response = await client.get(
                    f"{EntityServiceClient.BASE_URL}/api/v1/users/{user_id}/api-keys"
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Entity service list_api_keys failed: {e}")
            return []
    
    @staticmethod
    async def revoke_api_key(key_id: str) -> None:
        """Revoke API key"""
        try:
            async with httpx.AsyncClient(timeout=EntityServiceClient.TIMEOUT) as client:
                response = await client.delete(
                    f"{EntityServiceClient.BASE_URL}/api/v1/api-keys/{key_id}"
                )
                response.raise_for_status()
        except Exception as e:
            logger.error(f"Entity service revoke_api_key failed: {e}")
            raise ValueError(f"Failed to revoke API key: {e}")
    
    @staticmethod
    async def create_reset_token(
        user_id: str,
        token: str,
        expires_at: datetime
    ) -> Dict[str, Any]:
        """Create password reset token"""
        try:
            async with httpx.AsyncClient(timeout=EntityServiceClient.TIMEOUT) as client:
                response = await client.post(
                    f"{EntityServiceClient.BASE_URL}/api/v1/password-reset-tokens",
                    json={
                        "user_id": user_id,
                        "token": token,
                        "expires_at": expires_at.isoformat(),
                        "used": False
                    }
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Entity service create_reset_token failed: {e}")
            raise ValueError(f"Failed to create reset token: {e}")
    
    @staticmethod
    async def get_reset_token(token: str) -> Optional[Dict[str, Any]]:
        """Get reset token"""
        try:
            async with httpx.AsyncClient(timeout=EntityServiceClient.TIMEOUT) as client:
                response = await client.get(
                    f"{EntityServiceClient.BASE_URL}/api/v1/password-reset-tokens/{token}"
                )
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Entity service get_reset_token failed: {e}")
            return None
    
    @staticmethod
    async def mark_reset_token_used(token_id: str) -> None:
        """Mark reset token as used"""
        try:
            async with httpx.AsyncClient(timeout=EntityServiceClient.TIMEOUT) as client:
                response = await client.patch(
                    f"{EntityServiceClient.BASE_URL}/api/v1/password-reset-tokens/{token_id}",
                    json={"used": True}
                )
                response.raise_for_status()
        except Exception as e:
            logger.error(f"Entity service mark_reset_token_used failed: {e}")
    
    @staticmethod
    async def link_sso_provider(
        user_id: str,
        provider: str,
        provider_user_id: str
    ) -> Dict[str, Any]:
        """Link SSO provider to user"""
        try:
            async with httpx.AsyncClient(timeout=EntityServiceClient.TIMEOUT) as client:
                response = await client.post(
                    f"{EntityServiceClient.BASE_URL}/api/v1/sso-linkages",
                    json={
                        "user_id": user_id,
                        "provider": provider,
                        "provider_user_id": provider_user_id
                    }
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Entity service link_sso_provider failed: {e}")
            raise ValueError(f"Failed to link SSO provider: {e}")
    
    @staticmethod
    async def get_sso_linkage(provider: str, provider_user_id: str) -> Optional[Dict[str, Any]]:
        """Get SSO linkage"""
        try:
            async with httpx.AsyncClient(timeout=EntityServiceClient.TIMEOUT) as client:
                response = await client.get(
                    f"{EntityServiceClient.BASE_URL}/api/v1/sso-linkages/{provider}/{provider_user_id}"
                )
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Entity service get_sso_linkage failed: {e}")
            return None
