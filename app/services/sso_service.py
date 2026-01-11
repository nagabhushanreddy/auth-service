"""SSO service"""
from typing import Optional, Dict
from utils import logger


class SsoProvider:
    """SSO provider configuration"""
    
    def __init__(
        self,
        name: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str
    ):
        self.name = name
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri


class SsoProfile:
    """SSO profile"""
    
    def __init__(
        self,
        id: str,
        email: str,
        name: str,
        provider: str,
        picture: Optional[str] = None
    ):
        self.id = id
        self.email = email
        self.name = name
        self.provider = provider
        self.picture = picture


# In-memory SSO provider configuration
_sso_providers: Dict[str, SsoProvider] = {}

# In-memory SSO account linkage
_sso_linkages: dict = {}


class SsoService:
    """Single Sign-On service"""
    
    @staticmethod
    def register_provider(
        provider: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str
    ) -> None:
        """Register SSO provider"""
        _sso_providers[provider] = SsoProvider(
            name=provider,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri
        )
        logger.info(f"SSO provider registered: {provider}")
    
    @staticmethod
    def get_provider(provider: str) -> Optional[SsoProvider]:
        """Get SSO provider config"""
        return _sso_providers.get(provider)
    
    @staticmethod
    def link_account(
        user_id: str,
        provider: str,
        sso_id: str
    ) -> None:
        """Link SSO account to user"""
        key = f"{provider}:{sso_id}"
        _sso_linkages[key] = {
            "user_id": user_id,
            "provider": provider
        }
        logger.info(f"SSO account linked: {user_id}, {provider}")
    
    @staticmethod
    def get_user_by_sso_profile(provider: str, sso_id: str) -> Optional[str]:
        """Get user by SSO profile"""
        key = f"{provider}:{sso_id}"
        linkage = _sso_linkages.get(key)
        return linkage["user_id"] if linkage else None
    
    @staticmethod
    def generate_auth_url(provider: str, state: str) -> str:
        """Generate OAuth authorization URL"""
        provider_config = SsoService.get_provider(provider)
        
        if not provider_config:
            raise ValueError(f"Unknown SSO provider: {provider}")
        
        urls = {
            "google": f"https://accounts.google.com/o/oauth2/v2/auth?client_id={provider_config.client_id}&redirect_uri={provider_config.redirect_uri}&response_type=code&scope=openid%20email%20profile&state={state}",
            "facebook": f"https://www.facebook.com/v12.0/dialog/oauth?client_id={provider_config.client_id}&redirect_uri={provider_config.redirect_uri}&scope=public_profile,email&state={state}",
            "microsoft": f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id={provider_config.client_id}&redirect_uri={provider_config.redirect_uri}&response_type=code&scope=openid%20email%20profile&state={state}",
        }
        
        return urls.get(provider, "")
    
    @staticmethod
    async def handle_callback(provider: str, code: str) -> Optional[SsoProfile]:
        """Handle OAuth callback"""
        provider_config = SsoService.get_provider(provider)
        
        if not provider_config:
            logger.warning(f"Unknown SSO provider: {provider}")
            return None
        
        # In production, exchange code for token and fetch user profile
        # This is a simplified mock
        logger.info(f"Handling OAuth callback for {provider}")
        
        # TODO: Implement actual OAuth token exchange
        return None
