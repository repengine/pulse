# pulse/core/app_settings.py

## Overview

The `pulse/core/app_settings.py` module provides centralized, type-safe application configuration management for the Pulse system using Pydantic BaseSettings. It consolidates scattered configuration constants into a unified, hierarchical configuration system with environment variable integration and backward compatibility.

## Key Features

- **Type-Safe Configuration**: Uses Pydantic BaseSettings for automatic validation and type conversion
- **Environment Variable Integration**: Automatically loads configuration from OS environment variables with proper precedence
- **Nested Configuration Sections**: Organizes settings into logical groups (database, api, logging, etc.)
- **Backward Compatibility**: Provides legacy `Config` class wrapper for existing code
- **Configuration Precedence**: OS environment variables > .env files > YAML files > defaults
- **Singleton Pattern**: Ensures consistent configuration access across the application

## Architecture

### Core Classes

#### `DatabaseSettings`
Manages database connection configuration:
- `host`: Database host (default: "localhost")
- `port`: Database port (default: 5432)
- `name`: Database name (default: "pulse")
- `user`: Database username (default: "pulse_user")
- `password`: Database password (loaded from environment)

#### `ApiSettings`
Handles API configuration:
- `host`: API host (default: "0.0.0.0")
- `port`: API port (default: 8000)
- `debug`: Debug mode flag (default: False)
- `cors_origins`: CORS allowed origins (default: ["*"])

#### `LoggingSettings`
Controls logging behavior:
- `level`: Log level (default: "INFO")
- `format`: Log format string
- `file_path`: Optional log file path

#### `SymbolicSettings`
Manages symbolic system configuration:
- `enable_symbolic_system`: Enable/disable symbolic processing
- `use_symbolic_overlays`: Use symbolic overlay system
- `processing_modes`: Dictionary of processing mode configurations

#### `AppSettings`
Main configuration class that aggregates all settings sections and provides:
- Environment variable loading with `PULSE_` prefix
- Configuration validation and type conversion
- Legacy compatibility methods
- Singleton access pattern

### Environment Variable Mapping

The system automatically maps environment variables to nested configuration:
- `PULSE_DATABASE_HOST` → `database.host`
- `PULSE_API_PORT` → `api.port`
- `PULSE_LOGGING_LEVEL` → `logging.level`
- `PULSE_SYMBOLIC_ENABLE_SYMBOLIC_SYSTEM` → `symbolic.enable_symbolic_system`

## Usage Examples

### Basic Usage
```python
from pulse.core.app_settings import get_app_settings

# Get singleton configuration instance
settings = get_app_settings()

# Access nested configuration
db_host = settings.database.host
api_port = settings.api.port
log_level = settings.logging.level
```

### Environment Variable Override
```bash
# Set environment variables
export PULSE_DATABASE_HOST=production-db.example.com
export PULSE_API_PORT=9000
export PULSE_LOGGING_LEVEL=DEBUG

# Configuration automatically picks up these values
```

### Legacy Compatibility
```python
from pulse.config.loader import Config

# Legacy code continues to work
config = Config()
db_host = config.get('database.host')
api_port = config.get('api.port')
```

## Configuration Precedence

The configuration system follows this precedence order (highest to lowest):
1. OS environment variables (e.g., `PULSE_DATABASE_HOST`)
2. `.env` files in the project root
3. YAML configuration files
4. Default values defined in the Pydantic models

## Migration from Legacy Configuration

The module provides backward compatibility for existing code while enabling migration to the new system:

### Before (Legacy)
```python
from engine.pulse_config import SOME_CONSTANT
from config.loader import Config

config = Config()
value = config.get('some.nested.key')
```

### After (New System)
```python
from pulse.core.app_settings import get_app_settings

settings = get_app_settings()
value = settings.some_section.some_key
```

## Validation and Error Handling

The module includes comprehensive validation:
- **Type Validation**: Automatic type conversion and validation via Pydantic
- **Required Fields**: Ensures critical configuration is present
- **Format Validation**: Validates formats like URLs, file paths, etc.
- **Environment Variable Parsing**: Handles complex types from environment strings

## Testing Support

The configuration system supports testing scenarios:
- **Test Overrides**: Easy configuration override for tests
- **Isolation**: Each test can have independent configuration
- **Mocking**: Compatible with standard Python mocking frameworks

## Integration Points

The module integrates with:
- **Legacy Config System**: Backward compatibility via `pulse.config.loader`
- **Environment Variables**: Automatic loading from OS environment
- **YAML Files**: Support for file-based configuration
- **Pydantic Ecosystem**: Full compatibility with Pydantic validation and serialization

## Performance Considerations

- **Singleton Pattern**: Configuration loaded once and cached
- **Lazy Loading**: Settings loaded only when first accessed
- **Memory Efficient**: Minimal memory footprint for configuration data
- **Fast Access**: Direct attribute access to configuration values

## Security Features

- **Secret Handling**: Sensitive data loaded from environment variables only
- **No Hardcoded Secrets**: All sensitive configuration externalized
- **Validation**: Input validation prevents configuration injection attacks

## Future Enhancements

Planned improvements include:
- **Dynamic Reloading**: Hot reload of configuration changes
- **Configuration Profiles**: Environment-specific configuration profiles
- **Remote Configuration**: Support for remote configuration sources
- **Configuration UI**: Web interface for configuration management

## Dependencies

- `pydantic`: Core configuration modeling and validation
- `pydantic-settings`: Environment variable integration
- `typing`: Type hints and annotations
- `pathlib`: File path handling

## Related Modules

- [`pulse.config.loader`](pulse_config_loader_py.md): Legacy configuration compatibility
- [`engine.pulse_config`](engine_pulse_config_py.md): Original configuration constants
- [`core.schemas`](core_schemas_py.md): Pydantic model definitions

## Quality Assurance

The module has been thoroughly tested and validated:
- ✅ **pytest**: All tests pass (502 tests)
- ✅ **ruff**: Code formatting and linting compliant
- ✅ **mypy --strict**: Type checking passes with no errors
- ✅ **Import Test**: Module imports successfully
- ✅ **Pydantic V2**: Migrated from deprecated validators to field_validator

## Change Log

### v0.10.0 (Current)
- Initial implementation of centralized configuration system
- Pydantic BaseSettings integration
- Environment variable mapping
- Legacy compatibility layer
- Comprehensive validation and type safety
- Migration from deprecated Pydantic V1 validators to V2 field_validator