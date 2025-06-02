"""Unit tests for the Pulse Config loader."""

import os
import pytest
from pathlib import Path
from typing import Generator, Dict

# Assuming pulse.config.loader is importable from the project root
# For testing, we might need to adjust sys.path or use a more direct import
# For now, assume the project structure allows `from pulse.config.loader import Config`
from pulse.config.loader import Config


@pytest.fixture
def temp_config_files(tmp_path: Path) -> Generator[Dict[str, Path], None, None]:
    """Provides temporary config files for testing."""
    original_cwd = os.getcwd()
    os.chdir(tmp_path)  # Change CWD to tmp_path for relative path resolution

    # Create a 'config' directory within the temporary path
    (tmp_path / "config").mkdir()

    yaml_path = tmp_path / "config" / "default.yaml"
    env_path = tmp_path / "config" / "example.env"

    # Sample default.yaml content
    yaml_content = """
app:
  name: "Test App"
  version: "1.0.0"
  debug_mode: true
database:
  host: "localhost"
  port: 5432
  user: "yaml_user"
  password: "yaml_pass"
feature_flags:
  new_feature: false
  old_feature: true
nested:
  level1:
    level2:
      key: "yaml_nested_value"
list_setting:
  - item1
  - item2
int_setting: 123
float_setting: 45.67
bool_setting: true
string_setting: "hello"
"""
    yaml_path.write_text(yaml_content)

    # Sample example.env content
    env_content = """
DATABASE_USER=env_user
DATABASE_PASSWORD=env_pass
FEATURE_FLAGS_NEW_FEATURE=true
NESTED_LEVEL1_LEVEL2_KEY=env_nested_value
INT_SETTING=456
FLOAT_SETTING=89.01
BOOL_SETTING=false
STRING_SETTING=world
"""
    env_path.write_text(env_content)

    yield {"yaml_path": yaml_path, "env_path": env_path, "tmp_path": tmp_path}

    os.chdir(original_cwd)  # Restore original CWD


class TestConfigLoader:
    """Tests for the Config class."""

    def test_load_from_yaml(self, temp_config_files: Dict[str, Path]) -> None:
        config = Config(
            yaml_path=str(temp_config_files["yaml_path"]),
            env_path="non_existent.env",  # Changed to ensure only YAML is loaded for this test
        )
        assert config.get("app.name") == "Test App"
        assert config.get("app.version") == "1.0.0"
        assert config.get("app.debug_mode") is True
        assert config.get("database.host") == "localhost"
        assert config.get("database.port") == 5432
        assert (
            config.get("database.user") == "yaml_user"
        )  # This assertion should now pass
        assert config.get("database.password") == "yaml_pass"
        assert config.get("feature_flags.new_feature") is False
        assert config.get("feature_flags.old_feature") is True
        assert config.get("nested.level1.level2.key") == "yaml_nested_value"
        assert config.get("list_setting") == ["item1", "item2"]
        assert config.get("int_setting") == 123
        assert config.get("float_setting") == 45.67
        assert config.get("bool_setting") is True
        assert config.get("string_setting") == "hello"

    def test_env_file_overrides(self, temp_config_files: Dict[str, Path]) -> None:
        config = Config(
            yaml_path=str(temp_config_files["yaml_path"]),
            env_path=str(temp_config_files["env_path"]),
        )
        assert config.get("database.user") == "env_user"
        assert config.get("database.password") == "env_pass"
        assert config.get("feature_flags.new_feature") is True
        assert config.get("nested.level1.level2.key") == "env_nested_value"
        assert config.get("int_setting") == 456
        assert config.get("float_setting") == 89.01
        assert config.get("bool_setting") is False
        assert config.get("string_setting") == "world"

    def test_os_environ_overrides(
        self, temp_config_files: Dict[str, Path], monkeypatch
    ) -> None:
        monkeypatch.setenv("DATABASE_HOST", "os_host")
        monkeypatch.setenv("DATABASE_PORT", "9876")
        monkeypatch.setenv("FEATURE_FLAGS_OLD_FEATURE", "false")
        monkeypatch.setenv("NESTED_LEVEL1_LEVEL2_KEY", "os_nested_value")
        monkeypatch.setenv("INT_SETTING", "789")
        monkeypatch.setenv("FLOAT_SETTING", "12.34")
        monkeypatch.setenv("BOOL_SETTING", "true")
        monkeypatch.setenv("STRING_SETTING", "os_world")

        config = Config(
            yaml_path=str(temp_config_files["yaml_path"]),
            env_path=str(temp_config_files["env_path"]),
        )

        assert config.get("database.host") == "os_host"
        assert config.get("database.port") == 9876  # Type casted
        assert config.get("feature_flags.old_feature") is False  # Type casted
        assert config.get("nested.level1.level2.key") == "os_nested_value"
        assert config.get("int_setting") == 789
        assert config.get("float_setting") == 12.34
        assert config.get("bool_setting") is True
        assert config.get("string_setting") == "os_world"

    def test_default_fallback(self, temp_config_files: Dict[str, Path]) -> None:
        config = Config(
            yaml_path=str(temp_config_files["yaml_path"]),
            env_path=str(temp_config_files["env_path"]),
        )
        assert config.get("non_existent_key", "default_value") == "default_value"
        assert config.get("another.missing.key", 123) == 123
        assert config.get("yet.another.missing.key", False) is False
        assert config.get("non_existent_key") is None

    def test_nested_keys(self, temp_config_files: Dict[str, Path], monkeypatch) -> None:
        # Ensure DATABASE_HOST is not set by previous tests if this test expects
        # 'localhost'
        monkeypatch.delenv("DATABASE_HOST", raising=False)

        config = Config(
            yaml_path=str(temp_config_files["yaml_path"]),
            env_path=str(temp_config_files["env_path"]),
        )
        assert config.get("app.name") == "Test App"
        assert config.get("database.host") == "localhost"
        assert (
            config.get("nested.level1.level2.key") == "env_nested_value"
        )  # From example.env

    def test_type_casting(
        self, temp_config_files: Dict[str, Path], monkeypatch
    ) -> None:
        config = Config(
            yaml_path=str(temp_config_files["yaml_path"]),
            env_path=str(temp_config_files["env_path"]),
        )
        assert config.get("app.debug_mode") is True  # From YAML, bool
        assert (
            config.get("feature_flags.new_feature") is True
        )  # From .env, string "true" to bool True
        assert config.get("int_setting") == 456  # From .env, string "456" to int 456
        assert (
            config.get("float_setting") == 89.01
        )  # From .env, string "89.01" to float 89.01
        assert (
            config.get("bool_setting") is False
        )  # From .env, string "false" to bool False
        assert (
            config.get("string_setting") == "world"
        )  # From .env, string "world" to string "world"

        # Test casting with default values
        assert config.get("some_int", 100) == 100
        assert config.get("some_float", 10.5) == 10.5
        assert config.get("some_bool", True) is True
        assert config.get("some_string", "default") == "default"

        # Test casting from OS env using monkeypatch fixture
        monkeypatch.setenv("TEST_INT", "999")
        monkeypatch.setenv("TEST_FLOAT", "99.99")
        monkeypatch.setenv("TEST_BOOL", "false")
        monkeypatch.setenv("TEST_STRING", "os_string")
        config_os_env = Config(
            yaml_path=str(temp_config_files["yaml_path"]),
            env_path=str(temp_config_files["env_path"]),
        )
        assert config_os_env.get("test.int", 0) == 999
        assert config_os_env.get("test.float", 0.0) == 99.99
        assert config_os_env.get("test.bool", True) is False
        assert config_os_env.get("test.string", "") == "os_string"

    def test_missing_yaml_file(self, tmp_path: Path) -> None:
        # Ensure no default.yaml exists
        (tmp_path / "config").mkdir(exist_ok=True)
        config = Config(
            yaml_path=str(tmp_path / "config" / "non_existent.yaml"),
            env_path=str(
                tmp_path / "config" / "example.env"
            ),  # Use a dummy env file if needed
        )
        assert config.get("app.name") is None  # Should not load from YAML

        # Create a dummy env file for this test
        env_path = tmp_path / "config" / "example.env"
        env_path.write_text("APP_NAME=Env App")
        config_with_env = Config(
            yaml_path=str(tmp_path / "config" / "non_existent.yaml"),
            env_path=str(env_path),
        )
        assert config_with_env.get("app.name") == "Env App"

    def test_missing_env_file(self, tmp_path: Path) -> None:
        # Ensure no example.env exists
        (tmp_path / "config").mkdir(exist_ok=True)
        yaml_path = tmp_path / "config" / "default.yaml"
        yaml_path.write_text('app:\n  name: "YAML App"')

        config = Config(
            yaml_path=str(yaml_path),
            env_path=str(tmp_path / "config" / "non_existent.env"),
        )
        assert config.get("app.name") == "YAML App"  # Should load from YAML
        assert config.get("DATABASE_USER") is None  # Should not load from .env

    def test_empty_config_files(self, tmp_path: Path) -> None:
        (tmp_path / "config").mkdir(exist_ok=True)
        empty_yaml_path = tmp_path / "config" / "empty.yaml"
        empty_env_path = tmp_path / "config" / "empty.env"
        empty_yaml_path.write_text("")
        empty_env_path.write_text("")

        config = Config(yaml_path=str(empty_yaml_path), env_path=str(empty_env_path))
        assert config.get("any_key") is None

    def test_no_config_files_present(self, tmp_path: Path, monkeypatch) -> None:
        # Ensure no config directory exists
        if (tmp_path / "config").exists():
            import shutil

            shutil.rmtree(tmp_path / "config")

        config = Config(
            yaml_path=str(tmp_path / "config" / "default.yaml"),
            env_path=str(tmp_path / "config" / "example.env"),
        )
        assert config.get("any_key") is None

        monkeypatch.setenv("TEST_KEY", "os_value")  # Use monkeypatch
        config_with_os_env = Config(
            yaml_path=str(tmp_path / "config" / "default.yaml"),
            env_path=str(tmp_path / "config" / "example.env"),
        )
        assert config_with_os_env.get("test.key") == "os_value"  # Use normalized key

    def test_os_environ_only(self, monkeypatch) -> None:  # Add monkeypatch
        monkeypatch.setenv("ONLY_OS_KEY", "os_only_value")
        monkeypatch.setenv("OS_INT", "12345")
        monkeypatch.setenv("OS_BOOL", "true")

        config = Config(yaml_path="non_existent.yaml", env_path="non_existent.env")
        assert config.get("only.os.key") == "os_only_value"  # Use normalized key
        assert config.get("os.int") == 12345  # Use normalized key
        assert config.get("os.bool") is True  # Use normalized key

    def test_get_with_different_defaults(
        self, temp_config_files: Dict[str, Path]
    ) -> None:
        config = Config(
            yaml_path=str(temp_config_files["yaml_path"]),
            env_path=str(temp_config_files["env_path"]),
        )
        assert config.get("non_existent", 10) == 10
        assert config.get("non_existent", 10.5) == 10.5
        assert config.get("non_existent", True) is True
        assert config.get("non_existent", "default_string") == "default_string"
        assert config.get("non_existent", [1, 2]) == [1, 2]
        assert config.get("non_existent", {"a": 1}) == {"a": 1}

    def test_type_casting_from_yaml(self, temp_config_files: Dict[str, Path]) -> None:
        config = Config(
            yaml_path=str(temp_config_files["yaml_path"]),
            env_path=str(temp_config_files["env_path"]),
        )
        assert config.get("int_setting") == 456  # Overridden by .env
        assert config.get("float_setting") == 89.01  # Overridden by .env
        assert config.get("bool_setting") is False  # Overridden by .env

        # Test original YAML values if not overridden
        # To do this, we need a config instance that only loads YAML
        yaml_only_config = Config(
            yaml_path=str(temp_config_files["yaml_path"]),
            env_path="non_existent.env",  # Ensure no .env is loaded
        )
        assert yaml_only_config.get("int_setting") == 123
        assert yaml_only_config.get("float_setting") == 45.67
        assert yaml_only_config.get("bool_setting") is True
