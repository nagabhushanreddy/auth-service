"""User service - handles user management"""
from typing import Optional, Dict
from uuid import uuid4
from datetime import datetime, timedelta
from passlib.context import CryptContext
from utils import logger
from app.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User:
    """User entity"""
    
    def __init__(
        self,
        id: str,
        username: str,
        email: str,
        password_hash: str,
        phone: Optional[str] = None,
        mfa_enabled: bool = False,
        mfa_method: str = "none",
        sso_providers: Optional[list] = None,
        status: str = "active",
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.phone = phone
        self.mfa_enabled = mfa_enabled
        self.mfa_method = mfa_method
        self.sso_providers = sso_providers or []
        self.status = status
        self.login_attempts = 0
        self.locked_until: Optional[datetime] = None
        self.last_login_at: Optional[datetime] = None
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "phone": self.phone,
            "mfa_enabled": self.mfa_enabled,
            "mfa_method": self.mfa_method,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# In-memory user store (replace with database in production)
_user_store: Dict[str, User] = {}


class AuthService:
    """Authentication service"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def is_password_strong(password: str) -> bool:
        """Check if password is strong"""
        if len(password) < 8:
            return False
        if not any(c.isupper() for c in password):
            return False
        if not any(c.islower() for c in password):
            return False
        if not any(c.isdigit() for c in password):
            return False
        if not any(c in "@$!%*?&" for c in password):
            return False
        return True
    
    @staticmethod
    def register_user(
        username: str,
        email: str,
        password: str,
        phone: Optional[str] = None,
        mfa_enabled: bool = False,
        mfa_method: str = "none"
    ) -> User:
        """Register a new user"""
        # Check if user exists
        for user in _user_store.values():
            if user.username == username or user.email == email:
                raise ValueError("Username or email already exists")
        
        # Hash password
        password_hash = AuthService.hash_password(password)
        
        # Create user
        user = User(
            id=str(uuid4()),
            username=username,
            email=email,
            password_hash=password_hash,
            phone=phone,
            mfa_enabled=mfa_enabled,
            mfa_method=mfa_method
        )
        
        _user_store[user.id] = user
        logger.info(f"User registered: {user.id}")
        
        return user
    
    @staticmethod
    def login_user(username: str, password: str) -> tuple[User, bool, Optional[str]]:
        """Login user, returns (user, mfa_required, mfa_method)"""
        user = None
        for u in _user_store.values():
            if u.username == username:
                user = u
                break
        
        if not user:
            raise ValueError("Invalid credentials")
        
        if user.status == "locked":
            if user.locked_until and datetime.utcnow() >= user.locked_until:
                # auto-unlock after lock duration
                user.status = "active"
                user.login_attempts = 0
                user.locked_until = None
            else:
                raise ValueError("Account is locked")
        
        # Verify password
        if not AuthService.verify_password(password, user.password_hash):
            user.login_attempts += 1
            if user.login_attempts >= settings.brute_force_max_attempts:
                user.status = "locked"
                user.locked_until = datetime.utcnow() + timedelta(milliseconds=settings.brute_force_lock_time)
                logger.warning(f"Account locked: {user.id}")
            raise ValueError("Invalid credentials")
        
        # Reset login attempts
        user.login_attempts = 0
        user.last_login_at = datetime.utcnow()
        
        if user.mfa_enabled:
            return user, True, user.mfa_method
        
        logger.info(f"User logged in: {user.id}")
        return user, False, None
    
    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[User]:
        """Get user by ID"""
        return _user_store.get(user_id)
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        """Get user by email"""
        for user in _user_store.values():
            if user.email == email:
                return user
        return None
    
    @staticmethod
    def get_user_by_username(username: str) -> Optional[User]:
        """Get user by username"""
        for user in _user_store.values():
            if user.username == username:
                return user
        return None
    
    @staticmethod
    def update_password(user_id: str, current_password: str, new_password: str) -> None:
        """Update user password"""
        user = _user_store.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Verify current password
        if not AuthService.verify_password(current_password, user.password_hash):
            raise ValueError("Current password is incorrect")
        
        # Hash new password
        user.password_hash = AuthService.hash_password(new_password)
        user.updated_at = datetime.utcnow()
        
        logger.info(f"Password updated: {user_id}")
    
    @staticmethod
    def lock_account(user_id: str) -> None:
        """Lock user account"""
        user = _user_store.get(user_id)
        if user:
            user.status = "locked"
            user.locked_until = datetime.utcnow() + timedelta(milliseconds=settings.brute_force_lock_time)
            logger.info(f"Account locked: {user_id}")
    
    @staticmethod
    def unlock_account(user_id: str) -> None:
        """Unlock user account"""
        user = _user_store.get(user_id)
        if user:
            user.status = "active"
            user.login_attempts = 0
            user.locked_until = None
            logger.info(f"Account unlocked: {user_id}")
    
    @staticmethod
    def link_sso_provider(user_id: str, provider: str) -> None:
        """Link SSO provider to user"""
        user = _user_store.get(user_id)
        if user and provider not in user.sso_providers:
            user.sso_providers.append(provider)
            user.updated_at = datetime.utcnow()
            logger.info(f"SSO provider linked: {user_id}, {provider}")
