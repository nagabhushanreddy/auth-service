
# Multi-Finance User Application  
## Microservices Requirements Document (OpenAPI-Compliant)

---

## 1. Overview

This document defines the functional and non-functional requirements for a **Multi-Finance User Web Application** built using a **microservices REST architecture**.  
All services **MUST expose OpenAPI 3.x compliant specifications**.

### Core Domains
- User & Identity
- Authorization
- User Profile
- Loan Management

---

## 2. Architecture Principles

- Microservices with **single responsibility**
- **Database-per-service or use entity-service**
- REST APIs with **OpenAPI 3.0+**
- Stateless services
- JWT-based security
- Event-driven integration where applicable
- Default **DENY** authorization model

---

## 3. Services Overview

| Service | Responsibility |
|------|---------------|
| API Gateway / BFF | Single entry point, auth enforcement |
| **Identity & Authentication Service** ⭐ | **Login, OTP, token issuance** |
| Authorization Service | Central policy decision (RBAC + ABAC) |
| User Profile Service | Customer profile & KYC metadata |
| Loan Service | Loan products, applications, accounts |
| Document Service | KYC & loan document storage |
| Notification Service | Email/SMS orchestration |
| Audit & Compliance Service | Immutable audit logging |

---

## 4. API Gateway / BFF

### Responsibilities
- JWT validation
- Rate limiting
- Request aggregation
- OpenAPI exposure for frontend

### OpenAPI Requirements
- Versioned paths `/api/v1`
- OAuth2 / Bearer JWT security scheme
- Correlation-Id header propagation

---

## 5. Identity & Authentication Service (IAM)

A RESTful microservice for user authentication, session management, and credential handling with multi-factor authentication (MFA) and API key management capabilities.

## Features

- **User Authentication**: Username/password authentication with secure bcrypt hashing
- **Multi-Factor Authentication (MFA)**: SMS/Email OTP support with configurable methods
- **JWT Token Management**: Secure access and refresh token generation with HS256
- **API Key Authentication**: Generate and manage API keys for service-to-service auth
- **Password Recovery**: Secure password reset flow with email verification
- **SSO Integration**: OAuth 2.0 support for Google, Facebook, Microsoft Azure AD
- **Account Security**: Brute force protection with account locking mechanism
- **Session Management**: Token blacklist and session tracking
- **RESTful API**: Follows REST and OpenAPI standards
- **Async/Await**: Fully asynchronous operations for high performance
- **Entity Service Integration**: All CRUD operations via entity-service
- **Utils Service Integration**: Shared logging and configuration utilities
- **Type Safety**: Full Pydantic schema validation
- **Error Handling**: Comprehensive error responses with proper HTTP status codes
- **Rate Limiting**: Configurable rate limits for security
- **OpenAPI Documentation**: Auto-generated interactive documentation

## Architecture

### Multi-Service Design

This service integrates with other microservices for separation of concerns:

```
Service Structure:
├── main.py                   (FastAPI app, lifespan, middleware)
├── app/
│   ├── __init__.py
│   ├── config.py            (Configuration loader)
│   ├── middleware.py        (Request context, correlation ID)
│   ├── cache.py             (In-memory cache for tokens, OTP)
│   ├── routes/              (API endpoints - thin layer)
│   │   ├── __init__.py
│   │   ├── auth_routes.py
│   │   ├── api_key_routes.py
│   │   └── password_routes.py
│   ├── services/            (Business logic layer)
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── token_service.py
│   │   ├── otp_service.py
│   │   ├── api_key_service.py
│   │   ├── password_service.py
│   │   └── validation_service.py
│   ├── models/              (Pydantic schemas)
│   │   ├── __init__.py
│   │   ├── auth_models.py
│   │   ├── api_key_models.py
│   │   ├── error_models.py
│   │   └── user_models.py
│   └── clients/             (External service clients)
│       ├── __init__.py
│       ├── entity_service.py
│       └── notification_service.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth_endpoints.py
│   ├── test_api_key_endpoints.py
│   ├── test_token_service.py
│   └── test_otp_service.py
├── reports/
│   ├── junit.xml
│   ├── coverage.xml
│   └── htmlcov/
├── logs/
├── config/
├── main.py (at root level)
├── requirements.txt
├── requirements-dev.txt
└── config/
```

**Benefits:**
- ✅ Separation of concerns (auth logic vs data storage)
- ✅ Reusable utilities across services
- ✅ Scalable architecture
- ✅ Easy to test and maintain
- ✅ Clear service boundaries

### OpenAPI Requirements
- Versioned paths `/api/v1`
- OAuth2 / Bearer JWT security scheme
- Correlation-Id header propagation

---

### 5.1 Scope
Authentication, session management, credential handling, and token issuance for Multi-Finance application.

### 5.2 Technology Stack
- **Language**: Python 3.10+
- **Framework**: FastAPI (async, OpenAPI native)
- **Password Hashing**: bcrypt (OWASP compliant)
- **Token Management**: PyJWT (HS256 algorithm)
- **Data Validation**: Pydantic
- **Testing**: pytest with coverage reporting
- **Logging**: Structured JSON logs (via utils-service)
- **Configuration**: Config management (via utils-service)
- **Server**: Uvicorn ASGI

### 5.3 Core APIs/Endpoints

### Health Check
- `GET /health` - Service health check
- `GET /healthz` - Kubernetes health probe

### User Registration & Login

#### Register New User
**Endpoint**: `POST /api/v1/auth/register`

**Request Requirements:**
- Must accept username (required, 3-30 characters, alphanumeric)
- Must accept email (required, valid RFC 5321 format)
- Must accept password (required, meets strength requirements)
- Must accept phone (optional, E.164 format)
- Must accept mfa_enabled flag (optional, boolean, default: false)
- Must accept mfa_method (optional if MFA disabled, required if enabled: "sms", "email", or "none")

**Response Requirements:**
- Success Status: 201 Created
- Must return user_id (UUID format)
- Must return sanitized user data (no password)
- Must include mfa configuration status
- Must include account status (active, pending, etc.)
- Must include creation timestamp (ISO 8601)
- Must include metadata with timestamp and correlation_id

**Business Logic:**
- Must validate username uniqueness
- Must validate email uniqueness
- Must hash password using bcrypt
- Must validate password strength
- Must store user via entity-service
- Must not return password or hash in response

#### User Login
**Endpoint**: `POST /api/v1/auth/login`

**Request Requirements:**
- Must accept username (required, case-insensitive)
- Must accept password (required)

**Response Requirements (MFA Disabled):**
- Success Status: 200 OK
- Must return access_token (JWT format)
- Must return refresh_token (JWT format)
- Must return token_type (value: "Bearer")
- Must return expires_in (seconds until expiry)
- Must return user object with user_id, username, email
- Must include metadata with timestamp and correlation_id

**Response Requirements (MFA Enabled):**
- Success Status: 202 Accepted
- Must return message indicating OTP sent
- Must return otp_expires_in (seconds)
- Must return mfa_method used (sms/email)
- Must include metadata with timestamp and correlation_id

**Business Logic:**
- Must verify username exists (case-insensitive)
- Must verify password using bcrypt comparison
- Must check account lock status
- Must increment failed login counter on failure
- Must lock account after configured max attempts
- Must reset failed login counter on success
- Must update last_login timestamp
- If MFA enabled: generate and send OTP, return 202
- If MFA disabled: generate tokens, return 200
- Must track login attempt in audit log

#### Verify OTP
**Endpoint**: `POST /api/v1/auth/verify-otp`

**Request Requirements:**
- Must accept username (required)
- Must accept otp (required, 6-digit numeric)

**Response Requirements:**
- Success Status: 200 OK
- Must return access_token (JWT format)
- Must return refresh_token (JWT format)
- Must return token_type (value: "Bearer")
- Must return expires_in (seconds)

**Business Logic:**
- Must verify OTP matches stored value
- Must check OTP expiration (5 minutes default)
- Must track OTP attempt count
- Must fail after max attempts (3 default)
- Must invalidate OTP after successful verification
- Must invalidate OTP after max failed attempts
- Must generate access and refresh tokens on success

#### Refresh Token
**Endpoint**: `POST /api/v1/auth/refresh`

**Request Requirements:**
- Must accept refresh_token (required, JWT format)

**Response Requirements:**
- Success Status: 200 OK
- Must return new access_token
- Must return new refresh_token
- Must return token_type ("Bearer")
- Must return expires_in

**Business Logic:**
- Must validate refresh token signature
- Must check refresh token expiration
- Must check token not in blacklist
- Must generate new token pair
- Must invalidate old refresh token

#### Logout
**Endpoint**: `POST /api/v1/auth/logout`

**Request Requirements:**
- Must require Authorization header with Bearer token

**Response Requirements:**
- Success Status: 200 OK
- Must return success confirmation

**Business Logic:**
- Must extract token from Authorization header
- Must add token to blacklist
- Must invalidate associated refresh token

### API Key Management

#### Create API Key
**Endpoint**: `POST /api/v1/auth/api-keys`

**Authentication**: Required (Bearer token)

**Request Requirements:**
- Must accept name (required, human-readable identifier)
- Must accept expires_at (optional, ISO 8601 datetime)

**Response Requirements:**
- Success Status: 201 Created
- Must return key_id (unique identifier)
- Must return api_key (plain text, shown only once)
- Must return name
- Must return created_at timestamp
- Must return expires_at (if provided)
- Must include warning about key storage

**Business Logic:**
- Must generate cryptographically secure random key (32+ bytes entropy)
- Must hash key using SHA-256 for storage
- Must associate key with authenticated user
- Must store via entity-service
- Must never store plain key
- Must return plain key only in creation response
- Must enforce rate limit (10 per hour per user)

#### List API Keys
**Endpoint**: `GET /api/v1/auth/api-keys`

**Authentication**: Required (Bearer token)

**Response Requirements:**
- Success Status: 200 OK
- Must return array of user's API keys
- Must include key_id, name, created_at, expires_at, last_used_at, active status
- Must NOT include actual key or hash

#### Delete API Key
**Endpoint**: `DELETE /api/v1/auth/api-keys/{key_id}`

**Authentication**: Required (Bearer token)

**Response Requirements:**
- Success Status: 200 OK
- Must return deletion confirmation

**Business Logic:**
- Must verify key belongs to authenticated user
- Must soft delete or mark as inactive
- Must prevent reactivation

### Password Recovery

#### Request Password Reset
**Endpoint**: `POST /api/v1/auth/password-reset`

**Request Requirements:**
- Must accept email (required, valid format)

**Response Requirements:**
- Success Status: 200 OK (always, even if email not found - security)
- Must return generic success message

**Business Logic:**
- Must verify email exists in system
- If email found: generate cryptographically secure reset token
- Must store token with user_id and expiration (1 hour)
- Must send reset link via notification-service
- If email not found: return success (prevent enumeration)
- Must enforce rate limit (3 per hour per email)
- Must invalidate previous reset tokens for user

#### Confirm Password Reset
**Endpoint**: `POST /api/v1/auth/password-reset/confirm`

**Request Requirements:**
- Must accept reset_token (required)
- Must accept new_password (required, meets strength requirements)

**Response Requirements:**
- Success Status: 200 OK
- Must return success confirmation

**Business Logic:**
- Must validate reset token exists
- Must check token not expired (1 hour)
- Must check token not already used
- Must validate new password strength
- Must hash new password using bcrypt
- Must update user password via entity-service
- Must mark reset token as used
- Must invalidate all user sessions/tokens
- Must send confirmation notification

### System Endpoints

#### Health Check
**Endpoints**: `GET /health`, `GET /healthz`

**Response Requirements:**
- Success Status: 200 OK
- Must return service status
- Must include timestamp
- Must include service name and version

#### OpenAPI Specification
**Endpoint**: `GET /v3/api-docs`

**Response Requirements:**
- Success Status: 200 OK
- Must return complete OpenAPI 3.0+ specification
- Must include all endpoint definitions
- Must include all schema definitions
- Must include security schemes
- Must include error response schemas

### 5.4 Functional Requirements

#### 5.4.1 User Authentication
- **Username/password based authentication**
  - Case-insensitive username matching
  - Secure password hashing with bcrypt (10 salt rounds)
  - Password strength validation:
    - Minimum 8 characters
    - Mixed case (uppercase + lowercase)
    - At least one number
    - At least one special character (@$!%*?&)

#### 5.4.2 Multi-Factor Authentication (MFA)
- **Configurable MFA during registration**
  - Methods: SMS, Email, None
  - OTP generation: 6-digit numeric code
  - OTP expiry: 5 minutes (configurable)
  - OTP retry limit: 3 attempts maximum
  - Automatic OTP generation on login if MFA enabled
  - Completion of MFA required before token issuance

#### 5.4.3 Token Management
- **JWT-based tokens**
  - Algorithm: HS256
  - Access Token Expiry: 15 minutes
  - Refresh Token Expiry: 7 days
  - Issuer: auth-service
  - Audience: api
  - Token refresh using valid refresh token
  - Token revocation on logout (blacklist)
  - Renewal of refresh token on access token refresh

#### 5.4.4 API Key Authentication
- **Secure API key generation**
  - Random generation (32+ bytes entropy)
  - SHA-256 hashing for storage
  - Key displayed only once during creation
  - Optional expiration dates
  - Last used timestamp tracking
  - Revocation capability

#### 5.4.5 Credential Recovery
- **Password reset flow**
  - Email-based reset link generation
  - Reset token expiry: 1 hour
  - One-time use enforcement
  - Password strength validation required
  - Notification via email

#### 5.4.6 SSO Integration
- **OAuth 2.0 provider support**
  - Google OAuth
  - Facebook OAuth
  - Microsoft Azure AD
  - Authorization code flow
  - Automatic account linking
  - Fallback to email-based account matching

#### 5.4.7 Account Security
- **Brute force protection**
  - Login attempt tracking
  - Account locking after 5 failed attempts
  - Lock duration: 15 minutes (configurable)
  - Admin unlock capability
  - Attempt counter reset on successful login

#### 5.4.8 Session Management
- **Session tracking**
  - Last login timestamp
  - Active token management
  - Logout invalidates tokens
  - Token blacklist (in-memory, upgrade to Redis)

### 5.5 Non-Functional Requirements

#### 5.5.1 Performance
- **Latency Targets**
  - User registration: < 200ms
  - User login: < 300ms
  - Token verification: < 50ms
  - OTP generation: < 10ms
  - API key validation: < 20ms
  - P95 latency overall: < 300ms

#### 5.5.2 Security
- **Encryption & Hashing**: Passwords via bcrypt (salt rounds=10), API Keys via SHA-256, Tokens via HS256 with >32 char secrets
- **Transport**: TLS 1.2+ enforced in production
- **Input Validation**: 
  - Email format (RFC 5321)
  - Username (3-30 chars, alphanumeric)
  - Password strength validation (8+ chars, mixed case, number, special char)
  - OTP format (6 digits only)
  - Correlation ID (UUID format)
- **Rate Limiting**:
  - Login: 5 per 15 minutes per IP
  - Password reset: 3 per hour per email
  - OTP verification: 3 attempts per OTP
  - API key generation: 10 per hour per user
- **CORS Configuration**: Configurable origins, credentials support, specific HTTP methods, custom header support (X-API-Key, X-Correlation-ID)

#### 5.5.3 Availability & Reliability
- **Uptime Target**: 99.9% SLA
- **Graceful Shutdown**: 30 second timeout
- **Health Check**: Every 10 seconds
- **Error Recovery**: Automatic retry with exponential backoff

#### 5.5.4 Observability
- **Logging**
  - Structured JSON format
  - Correlation ID propagation
  - All authentication events logged
  - Failed attempts logged
  - Token operations logged

- **Metrics**
  - Request latency (histogram)
  - Error rates (counter)
  - Active sessions (gauge)
  - Token creation rate (counter)

- **Tracing**
  - Correlation ID on all requests
  - X-Correlation-ID response header
  - Trace propagation to dependent services

#### 5.5.5 Data Storage
- **Current Implementation**: In-memory (for development)
- **Production**: Must use entity-service for all CRUD operations
- **Data Entities**:
  - **Users**: Core user authentication data
    - Fields: id, username, email, password_hash, phone, mfa_enabled, mfa_method, status, failed_login_attempts, locked_until, last_login, timestamps
  - **API Keys**: Service authentication keys
    - Fields: id, user_id, hashed_key, name, created_at, expires_at, last_used_at, active
  - **Reset Tokens**: Password reset tokens
    - Fields: token, user_id, expires_at, used_flag, created_at
  - **OTP Codes**: One-time passwords for MFA
    - Fields: user_id, otp_code, expires_at, attempts, created_at
  - **SSO Linkages**: OAuth provider mappings
    - Fields: user_id, provider, provider_id, created_at
  - **Token Blacklist**: Revoked tokens
    - Fields: token_jti, revoked_at, expires_at

### 5.6 Service Dependencies

#### 5.6.1 Entity Service Integration
**Required for production deployment**

All CRUD operations must use entity-service:
- **User Management**: Create, retrieve, update user records
- **API Key Storage**: API key lifecycle management
- **Token Storage**: Reset tokens and OTP storage
- **SSO Linkage**: OAuth provider mapping storage
- **Token Blacklist**: Revoked token tracking

**Integration Requirements:**
- Must implement async HTTP client for entity-service communication
- Must support base URL configuration via environment variable
- Must provide methods for create, retrieve, update, delete operations
- Must handle entity type as parameter (user, api_key, reset_token, etc.)
- Must support filtering entities by field values
- Must include proper error handling and retries
- Must propagate correlation ID headers
- Must handle authentication headers (X-Requestor-Id)

**Current Implementation**: `src/clients/entity_service.py`

#### 5.6.2 Utils Service Integration
**Required for code reusability**

Common utilities to be reused from utils-service:
- **Logging**: Must use structured JSON logging with correlation ID support
  - Import logger from utils package
  - Use logger methods with extra parameter for structured fields
  - Include user_id, action, and other context in logs
- **Configuration**: Must use config file and environment variable loading
  - Import load_settings function from utils
  - Define Settings class with required fields
  - Load config from config/ directory with env override support

Auth-specific utilities to be placed under `src/services/`:
- Password hashing utilities (`src/services/password_service.py`)
- OTP generation algorithms (`src/services/otp_service.py`)
- Token generation helpers (`src/services/token_service.py`)
- Email/phone validation (`src/services/validation_service.py`)
- Password strength validation (`src/services/password_service.py`)

**Current Implementation**: `src/clients/utils_service.py`

#### 5.6.3 Notification Service Integration
**Optional but recommended for production**

For email/SMS delivery:
- **OTP Delivery**: Send OTP codes via SMS/Email
- **Password Reset**: Send password reset emails
- **MFA Notifications**: Account security notifications
- **Welcome Emails**: User registration confirmations

**Integration Requirements:**
- Must implement async HTTP client for notification-service communication
- Must provide send_sms method with phone, message, correlation_id parameters
- Must provide send_email method with to, subject, template, data parameters
- Must support template-based email rendering
- Must include proper error handling and retries
- Must propagate correlation ID for tracing
- Must handle service unavailability gracefully

**Fallback**: If notification service unavailable, log OTP codes (dev only)

### 5.7 Request/Response Specifications

#### 5.7.1 Standard Response Format
```json
{
  "success": true|false,
  "data": { /* endpoint-specific data */ },
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": { /* validation errors */ }
  },
  "metadata": {
    "timestamp": "ISO8601",
    "correlation_id": "UUID"
  }
}
```

#### 5.7.2 Error Codes

Use error codes in conjunction with http status codes. 

```
VALIDATION_ERROR: Request validation failed
REGISTRATION_FAILED: User registration failed
LOGIN_FAILED: Login authentication failed
INVALID_CREDENTIALS: Password/username incorrect
ACCOUNT_LOCKED: Account locked due to failed attempts
INVALID_OTP: OTP verification failed
OTP_EXPIRED: OTP has expired
INVALID_TOKEN: JWT token invalid or expired
REFRESH_FAILED: Token refresh failed
API_KEY_GENERATION_FAILED: API key creation failed
INVALID_API_KEY: API key invalid or expired
USER_NOT_FOUND: User does not exist
DUPLICATE_USER: Username or email already exists
PASSWORD_RESET_FAILED: Password reset process failed
INVALID_RESET_TOKEN: Reset token invalid or expired
WEAK_PASSWORD: Password does not meet strength requirements
UNAUTHORIZED: Missing or invalid authentication
RATE_LIMIT_EXCEEDED: Too many requests
INTERNAL_ERROR: Server error
```

### 5.8 OpenAPI Requirements
- **Version**: OpenAPI 3.0+
- **Endpoint**: `GET /v3/api-docs` returns complete specification
- **Security Schemes**:
  - bearerAuth (JWT tokens)
  - apiKeyAuth (X-API-Key header)
- **Request/Response Schemas**: Strict validation
- **Error Schemas**: Standardized error responses
- **Documentation**: Clear descriptions for all endpoints

### 5.9 Testing Requirements

#### 5.9.1 Unit Tests
- Password hashing and verification
- JWT token generation and validation
- OTP generation and verification
- API key generation and validation
- Password strength validation

#### 5.9.2 Integration Tests
- Complete authentication flows
- MFA login flow
- API key lifecycle
- Password reset flow
- SSO flow (mocked providers)

#### 5.9.3 Coverage & Reporting
- Minimum 80% code coverage
- XML test reports (JUnit format)
- HTML coverage reports
- Test execution logs

#### 5.9.4 Test Framework
- pytest (Python testing framework)
- pytest-cov (coverage reporting)
- pytest-asyncio (async test support)
- TestClient (FastAPI testing)

### 5.10 Configuration Management

#### 5.10.1 Environment Variables
**Required Environment Variables:**
- NODE_ENV: Environment mode (development, production)
- PORT: Service port number
- JWT_ACCESS_SECRET: Secret for access tokens (minimum 32 characters)
- JWT_REFRESH_SECRET: Secret for refresh tokens (minimum 32 characters)
- JWT_ACCESS_EXPIRY: Access token expiry in seconds
- JWT_REFRESH_EXPIRY: Refresh token expiry in seconds
- JWT_ALGORITHM: JWT signing algorithm (HS256)

**MFA Configuration:**
- MFA_OTP_LENGTH: OTP code length (default: 6)
- MFA_OTP_EXPIRY: OTP expiry in seconds (default: 300)
- MFA_OTP_ATTEMPTS: Max OTP verification attempts (default: 3)

**Security Configuration:**
- RATE_LIMIT_WINDOW_MS: Rate limit window in milliseconds
- RATE_LIMIT_MAX_REQUESTS: Max requests per window
- BRUTE_FORCE_MAX_ATTEMPTS: Max failed login attempts
- BRUTE_FORCE_LOCK_TIME: Account lock duration in milliseconds

**CORS Configuration:**
- CORS_ORIGINS: Comma-separated allowed origins

**OAuth Provider Configuration:**
- GOOGLE_CLIENT_ID: Google OAuth client ID
- GOOGLE_CLIENT_SECRET: Google OAuth secret
- FACEBOOK_CLIENT_ID: Facebook OAuth client ID
- MICROSOFT_CLIENT_ID: Microsoft OAuth client ID

**Service URLs:**
- FRONTEND_URL: Frontend application URL
- ENTITY_SERVICE_URL: Entity service base URL
- NOTIFICATION_SERVICE_URL: Notification service base URL

**Logging:**
- LOG_LEVEL: Logging level (debug, info, warning, error)

#### 5.10.2 Secrets Management
- All secrets loaded from environment variables
- Minimum 32 character secrets for JWT
- Never commit secrets to repository
- Use Vault/KMS in production

### 5.11 Deployment Architecture

#### 5.11.1 Development
**Requirements:**
- Must support hot reload for code changes
- Must use uvicorn ASGI server
- Must load from src.main:app
- Must support debug logging

#### 5.11.2 Production
**Requirements:**
- Must use production ASGI server (gunicorn with uvicorn workers)
- Must support multiple worker processes
- Must use uvicorn worker class
- Must load from src.main:app
- Must configure worker count based on CPU cores

#### 5.11.3 Containerization
- Docker image with Python 3.10 base
- Health check endpoint
- Graceful shutdown handling
- Environment variable configuration

### 5.12 Acceptance Criteria
- [ ] All endpoints OpenAPI compliant
- [ ] Authentication enforced on protected endpoints
- [ ] MFA implementation complete and tested
- [ ] API key management functional
- [ ] Password reset flow secure and tested
- [ ] SSO framework integrated
- [ ] Test coverage >= 80%
- [ ] All error codes documented
- [ ] Correlation ID propagation working
- [ ] Rate limiting functional
- [ ] Account locking functional
- [ ] Token blacklisting functional
- [ ] Security tests passed
- [ ] Performance tests passed (P95 < 300ms)
- [ ] Integration with entity-service completed
- [ ] Integration with utils-service completed

---

## 6. Cross-Cutting Requirements

### 6.1 Security
- **Transport Security**: TLS 1.2+ everywhere, mTLS for internal service-to-service communication
- **Secrets Management**: All sensitive data via environment variables/Vault/KMS
- **Input Validation**: Strict validation per section 5.5.2
- **Output Encoding**: Prevent injection attacks

### 6.2 Observability & Monitoring
- **Structured Logging**: JSON format with correlation ID propagation (see section 5.5.4)
- **Metrics**: Request latency, error rates, active sessions (section 5.5.4)
- **Distributed Tracing**: Correlation ID on all requests for end-to-end visibility
- **Health Monitoring**: `/health` endpoint for readiness/liveness checks

### 6.3 API Standards
- **OpenAPI 3.0+**: All services expose `/v3/api-docs` with complete schema documentation
- **Error Handling**: Standardized error response format (section 5.7)
- **Request/Response**: Strict Pydantic validation
- **API Versioning**: Version via paths (e.g., `/api/v1`)

### 6.4 Testing & Quality
- **Test-Driven Development**: Unit, integration, and end-to-end tests
- **Code Coverage**: Minimum 80% coverage requirement
- **Test Reports**: XML (JUnit) and HTML formats for CI/CD integration
- **Test Frameworks**: pytest with pytest-cov and pytest-asyncio

### 6.5 Service Dependencies & Reusability
- **Entity-Service**: All CRUD operations (User, ApiKey, ResetToken, SsoLinkage)
- **Utils-Service**: Common utilities (config, logging)
- **Notification-Service**: Email/SMS delivery integration

### 6.6 API Discoverability
- OpenAPI schemas support AI agent discovery
- Clear operation descriptions and example payloads
- Comprehensive error documentation

### 6.7 Project Structure

All microservices MUST follow a consistent directory structure for maintainability and discoverability:

**Root Level:**
- `main.py` - Application entry point with FastAPI app, lifespan, middleware
- `requirements.txt` - Production dependencies
- `requirements-dev.txt` - Development dependencies (pytest, black, mypy, coverage)
- `.env.example` - Environment variable template
- `README.md` - Service documentation
- `IMPLEMENTATION_STATUS.md` - Implementation progress tracking
- `config/` - Configuration files (JSON/YAML) with placeholder support

**Application Module (`app/`):**
- `__init__.py` - Package initialization
- `config.py` - Configuration loader (utils-service first, local JSON fallback)
- `middleware.py` - Request context, correlation ID, logging middleware
- `cache.py` - In-memory cache for tokens, OTP codes

**Organized Submodules:**
- `app/models/` - Pydantic schemas for request/response validation
  - `__init__.py` - Export commonly used models
  - `auth_models.py` - Authentication schemas
  - `api_key_models.py` - API key schemas
  - `error_models.py` - Error response schemas
  - `user_models.py` - User data schemas
  
- `app/routes/` - API route handlers (thin layer, delegates to services)
  - `__init__.py` - Router initialization and aggregation
  - `auth_routes.py` - /api/v1/auth/* endpoints
  - `api_key_routes.py` - /api/v1/auth/api-keys/* endpoints
  - `password_routes.py` - /api/v1/auth/password-reset/* endpoints
  
- `app/services/` - Business logic layer
  - `__init__.py` - Export service classes
  - `auth_service.py` - Authentication workflows
  - `token_service.py` - JWT token generation/validation
  - `otp_service.py` - OTP generation/verification
  - `api_key_service.py` - API key management
  - `password_service.py` - Password hashing/validation
  - `validation_service.py` - Input validation helpers
  
- `app/clients/` - External service clients
  - `__init__.py` - Export client classes
  - `entity_service.py` - Entity service integration
  - `notification_service.py` - Notification service integration

**Testing:**
- `tests/` - All test files
  - `__init__.py` - Test package initialization
  - `conftest.py` - Shared test fixtures
  - `test_auth_endpoints.py` - Authentication endpoint tests
  - `test_api_key_endpoints.py` - API key endpoint tests
  - `test_password_endpoints.py` - Password reset endpoint tests
  - `test_token_service.py` - Token service unit tests
  - `test_otp_service.py` - OTP service unit tests
  - `test_api_key_service.py` - API key service unit tests
  - Test files named `test_*.py` for pytest discovery

**Reports:**
- `reports/` - Test and coverage reports
  - `junit.xml` - JUnit test results
  - `coverage.xml` - Coverage XML report
  - `htmlcov/` - HTML coverage report

**Logs:**
- `logs/` - Application log files (development only)

**Standards:**
- Each directory with Python code MUST have `__init__.py` for clean imports
- Use absolute imports: `from app.services import AuthService`
- Export commonly used classes/functions in `__init__.py` files
- Follow layered architecture: Routes → Services → Clients → External Services
- Keep routes thin (validation + delegation only)
- Business logic in services layer
- External integrations in clients layer

---

## 7. Implementation Status

For detailed implementation status, progress tracking, and open items, please refer to [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md).

---

## 8. Future Work / TODO Items

### 8.1 Security Enhancements (Phase 2)
- **Transport Security**: TLS 1.2+ everywhere, mTLS for internal service-to-service communication
- **Advanced MFA**: TOTP (Time-based OTP) support, Authenticator app integration
- **WebAuthn/FIDO2**: Passwordless authentication support
- **Biometric Authentication**: Fingerprint, Face ID integration for mobile
- **Session Management**: Redis-based distributed session store
- **Token Rotation**: Automatic token rotation policies
- **Risk-Based Authentication**: IP reputation, device fingerprinting
- **Audit Logging**: Comprehensive authentication audit trail via audit-service

### 8.2 Performance Improvements (Phase 2)
- **Caching Layer**: Redis cache for user data, reduce entity-service calls
- **Token Caching**: Cache token validation results
- **Connection Pooling**: Optimize database connection management
- **Rate Limiting**: Distributed rate limiting with Redis
- **Async Processing**: Background jobs for notifications

### 8.3 Feature Additions (Phase 2)
- **Social Login Expansion**: GitHub, LinkedIn, Twitter OAuth support
- **Account Management**: Email/phone verification, profile updates
- **Device Management**: Track and manage logged-in devices
- **Security Notifications**: Alert users of suspicious activity
- **Password History**: Prevent password reuse
- **Account Recovery**: Additional recovery methods (security questions)

### 8.4 Observability (Phase 2)
- **Metrics Export**: Prometheus metrics endpoint
- **Distributed Tracing**: OpenTelemetry integration
- **Performance Monitoring**: APM tool integration (New Relic, DataDog)
- **Security Monitoring**: Failed login alerts, anomaly detection

---

**End of Document**
