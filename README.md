# Auth Service - Python Implementation

Complete Identity & Authentication Service for Multi-Finance Application using FastAPI and Python.

## Service Dependencies

⚠️ **IMPORTANT**: This service is designed to integrate with shared microservices:

### Entity Service
Currently using in-memory storage. **Must migrate to entity-service** for:
- User CRUD operations
- API Key management
- Password reset tokens
- SSO account linkages

Replace in-memory dictionaries with entity-service API calls:
- `_user_store` → Entity Service User endpoints
- `_api_key_store` → Entity Service API Key endpoints
- `_reset_token_store` → Entity Service Token endpoints
- `_sso_linkages` → Entity Service SSO Linkage endpoints

### Utils Service
Extract and reuse from utils-service:
- Password hashing utilities
- OTP generation algorithms
- Token generation helpers
- Validation utilities
- Logging utilities
- Error handling utilities

Migration tasks will be tracked in the entity-service and utils-service repositories.

## Quick Start
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout user
- `POST /api/v1/auth/password-reset` - Request password reset
- `POST /api/v1/auth/mfa/enable` - Enable MFA
- `POST /api/v1/auth/mfa/verify` - Verify MFA code
