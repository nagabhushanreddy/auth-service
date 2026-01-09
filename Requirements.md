
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

### 5.1 Scope
Authentication, session management, and credential handling for Multi-Finance application.

### 5.2 Technology Stack
- **Language**: Python 3.10+
- **Framework**: FastAPI (async, OpenAPI native)
- **Password Hashing**: bcrypt (OWASP compliant)
- **Token Management**: PyJWT (HS256 algorithm)
- **Data Validation**: Pydantic
- **Testing**: pytest with coverage reporting
- **Logging**: Structured JSON logs
- **Server**: Uvicorn ASGI

### 5.3 Core APIs

#### 5.3.1 User Registration & Login
```
POST /auth/register
POST /auth/login
POST /auth/verify-otp
POST /auth/refresh
POST /auth/logout
```

#### 5.3.2 API Key Management
```
POST /auth/api-keys
GET /auth/api-keys
DELETE /auth/api-keys/{key_id}
```

#### 5.3.3 Password Recovery
```
POST /auth/password-reset
POST /auth/password-reset/confirm
```

#### 5.3.4 System Endpoints
```
GET /health
GET /v3/api-docs (OpenAPI specification)
```

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
- **Current Implementation**: In-memory (for development but via entity-service)
- **Production**: Must use entity-service for db
- **Data Entities**:
  - Users (id, username, email, password_hash, phone, mfa_enabled, mfa_method, status, timestamps)
  - API Keys (id, user_id, hashed_key, name, created_at, expires_at, last_used_at, active)
  - Reset Tokens (token, user_id, expires_at, used_flag)
  - SSO Linkages (user_id, provider, provider_id)

### 5.6 Service Dependencies

#### 5.6.1 Entity Service Integration
**Required for production deployment**

All CRUD operations must use entity-service:
- User creation, retrieval, update
- API key management
- Token storage
- SSO linkage management

**Current Placeholder**: `src/clients/entity_service.py`

#### 5.6.2 Utils Service Integration
**Required for code reusability**

Common utilities to be reused from utils-service:
- Logging utilities
- Error handling

Auth specific utilities to be placed under utils
- Password hashing utilities
- OTP generation algorithms
- Token generation helpers
- Email/phone validation
- Password strength validation

**Current Placeholder**: `src/clients/utils_service.py`

#### 5.6.3 Notification Service Integration
**Optional but recommended**

For production email/SMS delivery:
- OTP delivery
- Password reset emails
- MFA notifications

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
```
NODE_ENV=development|production
PORT=3001
JWT_ACCESS_SECRET=<min-32-chars>
JWT_REFRESH_SECRET=<min-32-chars>
JWT_ACCESS_EXPIRY=900
JWT_REFRESH_EXPIRY=604800
JWT_ALGORITHM=HS256

MFA_OTP_LENGTH=6
MFA_OTP_EXPIRY=300
MFA_OTP_ATTEMPTS=3

RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX_REQUESTS=100
BRUTE_FORCE_MAX_ATTEMPTS=5
BRUTE_FORCE_LOCK_TIME=900000

CORS_ORIGINS=http://localhost:3000,http://localhost:3001

GOOGLE_CLIENT_ID=<client-id>
GOOGLE_CLIENT_SECRET=<secret>
FACEBOOK_CLIENT_ID=<client-id>
MICROSOFT_CLIENT_ID=<client-id>

FRONTEND_URL=http://localhost:3000
LOG_LEVEL=info
```

#### 5.10.2 Secrets Management
- All secrets loaded from environment variables
- Minimum 32 character secrets for JWT
- Never commit secrets to repository
- Use Vault/KMS in production

### 5.11 Deployment Architecture

#### 5.11.1 Development
```
python -m uvicorn src.main:app --reload
```

#### 5.11.2 Production
```
gunicorn "src.main:app" --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

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

---

## 7. Implementation Status

For detailed implementation status, progress tracking, and open items, please refer to [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md).

---

**End of Document**
