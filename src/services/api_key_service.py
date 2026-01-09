"""API Key service"""
import secrets
from typing import Optional, Dict
from uuid import uuid4
from datetime import datetime, timedelta
import hashlib
from utils import logger


class ApiKeyRecord:
    """API key record"""
    
    def __init__(
        self,
        key_id: str,
        user_id: str,
        hashed_key: str,
        name: str,
        expires_at: Optional[datetime] = None
    ):
        self.id = key_id
        self.user_id = user_id
        self.key = hashed_key
        self.name = name
        self.created_at = datetime.utcnow()
        self.expires_at = expires_at
        self.last_used_at: Optional[datetime] = None
        self.active = True


# In-memory API key store (use database in production)
_api_key_store: Dict[str, ApiKeyRecord] = {}


class ApiKeyService:
    """API Key management service"""
    
    @staticmethod
    def generate_api_key(
        user_id: str,
        name: str,
        expires_in_seconds: Optional[int] = None
    ) -> tuple[str, str]:
        """Generate new API key, returns (key_id, plain_key)"""
        plain_key = str(uuid4()).replace("-", "") + str(uuid4()).replace("-", "")
        hashed_key = hashlib.sha256(plain_key.encode()).hexdigest()
        
        key_id = str(uuid4())
        expires_at = None
        
        if expires_in_seconds:
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in_seconds)
        
        record = ApiKeyRecord(
            key_id=key_id,
            user_id=user_id,
            hashed_key=hashed_key,
            name=name,
            expires_at=expires_at
        )
        
        _api_key_store[key_id] = record
        logger.info(f"API key generated for user: {user_id}")
        
        return key_id, plain_key
    
    @staticmethod
    def validate_api_key(plain_key: str) -> Optional[tuple[str, str]]:
        """Validate API key, returns (user_id, key_id) or None"""
        hashed_key = hashlib.sha256(plain_key.encode()).hexdigest()
        
        for key_id, record in _api_key_store.items():
            if (record.key == hashed_key and 
                record.active and 
                (not record.expires_at or datetime.utcnow() < record.expires_at)):
                record.last_used_at = datetime.utcnow()
                logger.info(f"API key validated for user: {record.user_id}")
                return record.user_id, key_id
        
        logger.warn("API key validation failed")
        return None
    
    @staticmethod
    def revoke_api_key(key_id: str, user_id: str) -> bool:
        """Revoke API key"""
        record = _api_key_store.get(key_id)
        
        if record and record.user_id == user_id:
            record.active = False
            logger.info(f"API key revoked: {key_id}")
            return True
        
        return False
    
    @staticmethod
    def list_api_keys(user_id: str) -> list:
        """List API keys for user (without revealing the key)"""
        keys = []
        for record in _api_key_store.values():
            if record.user_id == user_id:
                keys.append({
                    "id": record.id,
                    "name": record.name,
                    "created_at": record.created_at,
                    "expires_at": record.expires_at,
                    "last_used_at": record.last_used_at,
                    "active": record.active
                })
        return keys
    
    @staticmethod
    def delete_api_key(key_id: str, user_id: str) -> bool:
        """Delete API key"""
        record = _api_key_store.get(key_id)
        
        if record and record.user_id == user_id:
            del _api_key_store[key_id]
            logger.info(f"API key deleted: {key_id}")
            return True
        
        return False
