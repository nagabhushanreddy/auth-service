# Configuration Directory

This directory contains YAML configuration files for the auth-service.

## Configuration Files

### app.yaml
Application-specific configuration including:
- Service metadata (name, version, environment)
- Server settings (host, port)
- JWT configuration (secrets, expiry)
- API key settings
- Rate limiting rules
- CORS origins
- OAuth provider credentials
- MFA settings
- Redis connection
- Service URLs (entity-service, frontend)

### logging.yaml
Logging configuration including:
- Service name for structured logs
- Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- JSON log formatting
- Console logging options
- File logging with rotation
- Extra fields for all logs
- Logger-specific level overrides

## Environment Variable Resolution

All configuration values support environment variable resolution using `${VAR_NAME:default}` syntax:
- `${PORT:3001}` - Uses PORT env var, defaults to 3001 if not set
- `${JWT_ACCESS_SECRET}` - Uses JWT_ACCESS_SECRET env var, no default

### Config Directory Override
By default, the service loads configuration files from the `config/` folder.
You can override this by setting the `CONFIG_DIR` environment variable:

```
CONFIG_DIR=/custom/path/to/config
```

The utils-service `Config` loader will read YAML/JSON files from this directory.

## Usage

Configuration is automatically loaded by `src/config.py` using the `utils.config.Config` class:

```python
from src.config import config, settings

# Access via settings properties
port = settings.port
jwt_secret = settings.jwt_access_secret

# Access via config directly
service_name = config.get("service.name")
log_level = config.get("logging.level")
```

## Logging Setup

The logging configuration is automatically applied in `src/main.py` using `utils.logger.setup_logging()`:

```python
from utils.logger import setup_logging, get_logger

# Setup is done automatically in main.py
logger = get_logger(__name__)
logger.info("Application started")
```

## Best Practices

1. **Secrets**: Never commit secrets to config files. Use environment variables.
2. **Defaults**: Provide sensible defaults for development in config files.
3. **Production**: Override sensitive values via environment variables in production.
4. **Validation**: Settings properties in `src/config.py` provide type safety and validation.
