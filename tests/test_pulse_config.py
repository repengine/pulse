import pytest
import os
import json
import yaml
from unittest.mock import patch, mock_open

# Need to import the actual module to test its functions and classes
from core.pulse_config import (
    load_thresholds,
    save_thresholds,
    update_threshold,
    ConfigLoader,
    get_config,
    PATHS, # Import PATHS to potentially mock it if needed
    _thresholds # Import the internal _thresholds for testing update_threshold
)

# Fixture to create a temporary thresholds.json file
@pytest.fixture
def temp_thresholds_file(tmp_path):
    """Creates a temporary thresholds.json file for testing."""
    data = {"CONFIDENCE_THRESHOLD": 0.8, "DEFAULT_FRAGILITY_THRESHOLD": 0.9}
    file_path = tmp_path / "thresholds.json"
    with open(file_path, "w") as f:
        json.dump(data, f)
    # Patch the THRESHOLD_CONFIG_PATH to point to the temporary file
    with patch("core.pulse_config.THRESHOLD_CONFIG_PATH", str(file_path)):
        yield file_path

# Fixture to create temporary YAML config files
@pytest.fixture
def temp_config_dir(tmp_path):
    """Creates a temporary config directory with YAML files for testing."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    config1_data = {"setting1": "value1", "setting2": 123}
    config1_path = config_dir / "config1.yaml"
    with open(config1_path, "w") as f:
        yaml.dump(config1_data, f)

    config2_data = {"list_setting": [1, 2, 3], "bool_setting": True}
    config2_path = config_dir / "config2.yaml"
    with open(config2_path, "w") as f:
        yaml.dump(config2_data, f)

    # Patch the global config_loader instance and configure it to use the temporary directory
    with patch("core.pulse_config.config_loader") as mock_config_loader:
        # Create a real ConfigLoader instance with the temporary directory
        real_loader = ConfigLoader(config_dir=str(config_dir))
        # Configure the mock to delegate calls to the real instance
        mock_config_loader.load_config.side_effect = real_loader.load_config
        mock_config_loader.load_all_configs.side_effect = real_loader.load_all_configs
        mock_config_loader.get_config_value.side_effect = real_loader.get_config_value
        mock_config_loader.reload_config.side_effect = real_loader.reload_config
        mock_config_loader.configs = real_loader.configs # Ensure the configs dict is shared

        yield config_dir # Yield the directory path for potential use in tests

# Test load_thresholds function
def test_load_thresholds_exists(temp_thresholds_file):
    """Test load_thresholds when the file exists."""
    thresholds = load_thresholds()
    assert thresholds == {"CONFIDENCE_THRESHOLD": 0.8, "DEFAULT_FRAGILITY_THRESHOLD": 0.9}

def test_load_thresholds_not_exists(tmp_path):
    """Test load_thresholds when the file does not exist."""
    # Patch the THRESHOLD_CONFIG_PATH to a non-existent file
    with patch("core.pulse_config.THRESHOLD_CONFIG_PATH", str(tmp_path / "non_existent.json")):
        thresholds = load_thresholds()
        assert thresholds == {}

# Test save_thresholds function
def test_save_thresholds(tmp_path):
    """Test save_thresholds function."""
    file_path = tmp_path / "test_save.json"
    test_data = {"NEW_THRESHOLD": 0.5}
    with patch("core.pulse_config.THRESHOLD_CONFIG_PATH", str(file_path)):
        save_thresholds(test_data)
        with open(file_path, "r") as f:
            loaded_data = json.load(f)
        assert loaded_data == test_data

# Test update_threshold function
def test_update_threshold(temp_thresholds_file):
    """Test update_threshold function."""
    # Ensure initial state is as expected from the fixture
    initial_thresholds = load_thresholds()
    assert initial_thresholds.get("CONFIDENCE_THRESHOLD") == 0.8

    # Update a threshold
    update_threshold("CONFIDENCE_THRESHOLD", 0.95)

    # Verify the internal _thresholds is updated
    assert _thresholds.get("CONFIDENCE_THRESHOLD") == 0.95

    # Verify the saved file is updated
    with open(temp_thresholds_file, "r") as f:
        saved_data = json.load(f)
    assert saved_data.get("CONFIDENCE_THRESHOLD") == 0.95

    # Verify the global variable is updated (requires patching globals)
    with patch("core.pulse_config.globals") as mock_globals:
         update_threshold("TEST_THRESHOLD", 0.1)
         mock_globals().__setitem__.assert_called_with("TEST_THRESHOLD", 0.1)


# Test ConfigLoader class
def test_configloader_load_config_exists(temp_config_dir):
    """Test ConfigLoader.load_config when the file exists."""
    loader = ConfigLoader(config_dir=str(temp_config_dir))
    config = loader.load_config("config1.yaml")
    assert config == {"setting1": "value1", "setting2": 123}
    assert "config1.yaml" in loader.configs

def test_configloader_load_config_not_exists(temp_config_dir, capsys):
    """Test ConfigLoader.load_config when the file does not exist."""
    loader = ConfigLoader(config_dir=str(temp_config_dir))
    config = loader.load_config("non_existent.yaml")
    assert config == {}
    captured = capsys.readouterr()
    assert "Error loading configuration from" in captured.out

def test_configloader_load_all_configs(temp_config_dir):
    """Test ConfigLoader.load_all_configs."""
    loader = ConfigLoader(config_dir=str(temp_config_dir))
    loader.load_all_configs()
    assert "config1.yaml" in loader.configs
    assert "config2.yaml" in loader.configs
    assert loader.configs["config1.yaml"] == {"setting1": "value1", "setting2": 123}
    assert loader.configs["config2.yaml"] == {"list_setting": [1, 2, 3], "bool_setting": True}

def test_configloader_get_config_value(temp_config_dir):
    """Test ConfigLoader.get_config_value."""
    loader = ConfigLoader(config_dir=str(temp_config_dir))
    # Test getting a value from a loaded config
    loader.load_config("config1.yaml")
    value = loader.get_config_value("config1.yaml", "setting1")
    assert value == "value1"

    # Test getting a value from a config that needs loading
    value = loader.get_config_value("config2.yaml", "bool_setting")
    assert value is True
    assert "config2.yaml" in loader.configs

    # Test getting a non-existent key
    value = loader.get_config_value("config1.yaml", "non_existent_key")
    assert value is None

    # Test getting a non-existent key with a default
    value = loader.get_config_value("config1.yaml", "non_existent_key", default="default_value")
    assert value == "default_value"

    # Test getting a value from a non-existent file
    value = loader.get_config_value("non_existent.yaml", "some_key")
    assert value is None

    # Test getting a value from a non-existent file with a default
    value = loader.get_config_value("non_existent.yaml", "some_key", default="default_value")
    assert value == "default_value"


def test_configloader_reload_config(temp_config_dir):
    """Test ConfigLoader.reload_config."""
    loader = ConfigLoader(config_dir=str(temp_config_dir))
    loader.load_config("config1.yaml")
    assert "config1.yaml" in loader.configs

    # Modify the file content
    config1_path = temp_config_dir / "config1.yaml"
    new_data = {"setting1": "new_value", "new_setting": 456}
    with open(config1_path, "w") as f:
        yaml.dump(new_data, f)

    # Reload the config
    reloaded_config = loader.reload_config("config1.yaml")

    # Verify the config is reloaded with new data
    assert "config1.yaml" in loader.configs
    assert reloaded_config == new_data
    assert loader.configs["config1.yaml"] == new_data

# Test get_config function
def test_get_config_whole(temp_config_dir):
    """Test get_config to retrieve the whole config dictionary."""
    # get_config uses the global config_loader, which is patched by the fixture
    config = get_config("config1.yaml")
    assert config == {"setting1": "value1", "setting2": 123}

def test_get_config_value(temp_config_dir):
    """Test get_config to retrieve a specific value."""
    # get_config uses the global config_loader, which is patched by the fixture
    value = get_config("config2.yaml", "bool_setting")
    assert value is True

def test_get_config_value_default(temp_config_dir):
    """Test get_config to retrieve a specific value with a default."""
    # get_config uses the global config_loader, which is patched by the fixture
    value = get_config("config1.yaml", "non_existent_key", default="default_value")
    assert value == "default_value"

def test_get_config_non_existent_file(temp_config_dir, capsys):
    """Test get_config for a non-existent file."""
    # get_config uses the global config_loader, which is patched by the fixture
    config = get_config("non_existent.yaml")
    assert config == {}
    captured = capsys.readouterr()
    assert "Error loading configuration from" in captured.out

def test_get_config_value_non_existent_file(temp_config_dir, capsys):
    """Test get_config for a value from a non-existent file."""
    # get_config uses the global config_loader, which is patched by the fixture
    value = get_config("non_existent.yaml", "some_key")
    assert value is None
    captured = capsys.readouterr()
    assert "Error loading configuration from" in captured.out

def test_get_config_value_non_existent_file_default(temp_config_dir, capsys):
    """Test get_config for a value from a non-existent file with a default."""
    # get_config uses the global config_loader, which is patched by the fixture
    value = get_config("non_existent.yaml", "some_key", default="default_value")
    assert value == "default_value"
    captured = capsys.readouterr()
    assert "Error loading configuration from" in captured.out