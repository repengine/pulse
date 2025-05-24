# Config Loader (`pulse.config.loader.Config`)

## Purpose

The `Config` class provides a unified, robust interface for loading, merging, and accessing configuration values in Pulse.  
It supports hierarchical configuration from YAML files, `.env` files, and environment variables, with a clear override order and type-safe access.

---

## Features

- **Multi-source loading:** Supports YAML config files, `.env` files, and `os.environ`.
- **Override hierarchy:** Environment variables > `.env` > YAML > defaults.
- **Nested key access:** Supports dot-notation and dictionary-style access for nested keys.
- **Type casting:** Automatically casts values to the expected type if specified.
- **Validation:** Raises clear errors for missing required keys or type mismatches.
- **Reloadable:** Can reload configuration at runtime if sources change.

---

## Loading Order & Override Hierarchy

1. **YAML file** (e.g., `config/default.yaml`): Base configuration.
2. **.env file** (e.g., `config/example.env`): Overrides YAML for any keys present.
3. **Environment variables**: Highest precedence; override both `.env` and YAML.
4. **Defaults**: Used if a key is missing from all sources and a default is provided.

---

## Usage

### Basic Example

```python
from pulse.config.loader import Config

# Load config from default locations
config = Config(
    yaml_path="config/default.yaml",
    dotenv_path="config/example.env"
)

# Access values (dot notation or dict-style)
db_url = config.get("database.url")
api_key = config["api.key"]

# With type casting
timeout: int = config.get("service.timeout", cast=int)

# Nested keys
log_level = config.get("logging.level")
```

### Override Example

Suppose you have the following in `config/default.yaml`:
```yaml
database:
  url: "sqlite:///default.db"
  pool_size: 5
```
And in `.env`:
```
DATABASE_URL=postgresql://user:pass@localhost/db
```
And in your environment:
```
export DATABASE_POOL_SIZE=10
```
Then:
- `config.get("database.url")` → `"postgresql://user:pass@localhost/db"`
- `config.get("database.pool_size", cast=int)` → `10`

### Type Casting

```python
# Will cast the value to int, float, bool, etc.
max_retries = config.get("service.max_retries", cast=int)
debug_mode = config.get("debug", cast=bool)
```

### Error Handling

- Raises `KeyError` if a required key is missing and no default is provided.
- Raises `ValueError` if type casting fails.

---

## API Reference

### `Config(yaml_path: str, dotenv_path: str = None)`

- Loads configuration from the specified YAML and optional `.env` file.

### `get(key: str, default: Any = None, cast: Callable = None) -> Any`

- Retrieves a configuration value by key (dot notation or nested).
- If `cast` is provided, attempts to cast the value.
- If not found, returns `default` or raises `KeyError`.

### `__getitem__(key: str) -> Any`

- Dict-style access: `config["some.key"]`

### `reload()`

- Reloads all configuration sources.

---

## Implementation Notes

- Uses [PyYAML](https://pyyaml.org/) for YAML parsing.
- Uses [python-dotenv](https://saurabh-kumar.com/python-dotenv/) for `.env` files.
- All keys are normalized to uppercase with underscores for environment variable matching.
- Nested keys are supported via dot notation (`section.key`).

---

## Example: Full Pattern

```python
config = Config("config/default.yaml", "config/example.env")

# Get a string
api_url = config.get("api.url")

# Get an int with casting
timeout = config.get("service.timeout", cast=int)

# Get a boolean
debug = config.get("debug", cast=bool)

# Get a nested value with fallback
log_path = config.get("logging.file", default="/tmp/pulse.log")
```

---

## See Also

- [`docs/pulse_inventory.md`](docs/pulse_inventory.md)
- [`docs/pulse_dependency_map`](docs/pulse_dependency_map)