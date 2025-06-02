import pytest
from pytest import CaptureFixture
import json
import yaml
from unittest.mock import patch
from pathlib import Path
from typing import Iterator

# Import the actual module to test its functions and classes
import engine.pulse_config


# Fixture to create a temporary thresholds.json file
@pytest.fixture
def temp_thresholds_file(tmp_path: Path) -> Iterator[Path]:
    """Creates a temporary thresholds.json file for testing and patches pulse_config."""
    original_config_path = engine.pulse_config.THRESHOLD_CONFIG_PATH
    original_thresholds_dict = engine.pulse_config._thresholds.copy()
    original_confidence_threshold = engine.pulse_config.CONFIDENCE_THRESHOLD
    original_fragility_threshold = engine.pulse_config.DEFAULT_FRAGILITY_THRESHOLD

    data = {"CONFIDENCE_THRESHOLD": 0.8, "DEFAULT_FRAGILITY_THRESHOLD": 0.9}
    file_path = tmp_path / "thresholds.json"
    with open(file_path, "w") as f:
        json.dump(data, f)

    # Patch the THRESHOLD_CONFIG_PATH to point to the temporary file
    with patch("engine.pulse_config.THRESHOLD_CONFIG_PATH", str(file_path)):
        # Force pulse_config to reload its _thresholds from the patched path
        engine.pulse_config._thresholds = engine.pulse_config.load_thresholds()
        engine.pulse_config.CONFIDENCE_THRESHOLD = engine.pulse_config._thresholds.get(
            "CONFIDENCE_THRESHOLD", 0.4
        )
        engine.pulse_config.DEFAULT_FRAGILITY_THRESHOLD = (
            engine.pulse_config._thresholds.get("DEFAULT_FRAGILITY_THRESHOLD", 0.7)
        )
        yield file_path

    # Cleanup: Restore original values
    engine.pulse_config.THRESHOLD_CONFIG_PATH = original_config_path
    engine.pulse_config._thresholds = original_thresholds_dict
    engine.pulse_config.CONFIDENCE_THRESHOLD = original_confidence_threshold
    engine.pulse_config.DEFAULT_FRAGILITY_THRESHOLD = original_fragility_threshold


# Fixture to create temporary YAML config files
@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Iterator[Path]:
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

    # Patch the global config_loader instance and configure it to use the
    # temporary directory
    with patch("engine.pulse_config.config_loader") as mock_config_loader:
        # Create a real ConfigLoader instance with the temporary directory
        real_loader = engine.pulse_config.ConfigLoader(config_dir=str(config_dir))
        # Configure the mock to delegate calls to the real instance
        mock_config_loader.load_config.side_effect = real_loader.load_config
        mock_config_loader.load_all_configs.side_effect = real_loader.load_all_configs
        mock_config_loader.get_config_value.side_effect = real_loader.get_config_value
        mock_config_loader.reload_config.side_effect = real_loader.reload_config
        mock_config_loader.configs = (
            real_loader.configs
        )  # Ensure the configs dict is shared

        yield config_dir  # Yield the directory path for potential use in tests


# Test load_thresholds function
def test_load_thresholds_exists(temp_thresholds_file: Path) -> None:
    """Test load_thresholds when the file exists."""
    # After temp_thresholds_file fixture, engine.pulse_config is reloaded,
    # so load_thresholds will use the patched path.
    thresholds = engine.pulse_config.load_thresholds()
    assert thresholds == {
        "CONFIDENCE_THRESHOLD": 0.8,
        "DEFAULT_FRAGILITY_THRESHOLD": 0.9,
    }


def test_load_thresholds_not_exists(tmp_path: Path) -> None:
    """Test load_thresholds when the file does not exist."""
    # Save original state
    original_config_path = engine.pulse_config.THRESHOLD_CONFIG_PATH
    original_thresholds_dict = engine.pulse_config._thresholds.copy()
    original_confidence_threshold = engine.pulse_config.CONFIDENCE_THRESHOLD
    original_fragility_threshold = engine.pulse_config.DEFAULT_FRAGILITY_THRESHOLD

    # Patch the THRESHOLD_CONFIG_PATH to a non-existent file
    with patch(
        "engine.pulse_config.THRESHOLD_CONFIG_PATH", str(tmp_path / "non_existent.json")
    ):
        # Force pulse_config to reload its _thresholds from the patched path
        engine.pulse_config._thresholds = engine.pulse_config.load_thresholds()
        engine.pulse_config.CONFIDENCE_THRESHOLD = engine.pulse_config._thresholds.get(
            "CONFIDENCE_THRESHOLD", 0.4
        )
        engine.pulse_config.DEFAULT_FRAGILITY_THRESHOLD = (
            engine.pulse_config._thresholds.get("DEFAULT_FRAGILITY_THRESHOLD", 0.7)
        )

        thresholds = engine.pulse_config.load_thresholds()
        assert thresholds == {}

    # Cleanup: Restore original values
    engine.pulse_config.THRESHOLD_CONFIG_PATH = original_config_path
    engine.pulse_config._thresholds = original_thresholds_dict
    engine.pulse_config.CONFIDENCE_THRESHOLD = original_confidence_threshold
    engine.pulse_config.DEFAULT_FRAGILITY_THRESHOLD = original_fragility_threshold


# Test save_thresholds function
def test_save_thresholds(tmp_path: Path) -> None:
    """Test save_thresholds function."""
    # Save original state
    original_config_path = engine.pulse_config.THRESHOLD_CONFIG_PATH
    original_thresholds_dict = engine.pulse_config._thresholds.copy()
    original_confidence_threshold = engine.pulse_config.CONFIDENCE_THRESHOLD
    original_fragility_threshold = engine.pulse_config.DEFAULT_FRAGILITY_THRESHOLD

    file_path = tmp_path / "test_save.json"
    test_data = {"NEW_THRESHOLD": 0.5}
    with patch("engine.pulse_config.THRESHOLD_CONFIG_PATH", str(file_path)):
        # Force pulse_config to reload its _thresholds from the patched path
        engine.pulse_config._thresholds = engine.pulse_config.load_thresholds()
        engine.pulse_config.CONFIDENCE_THRESHOLD = engine.pulse_config._thresholds.get(
            "CONFIDENCE_THRESHOLD", 0.4
        )
        engine.pulse_config.DEFAULT_FRAGILITY_THRESHOLD = (
            engine.pulse_config._thresholds.get("DEFAULT_FRAGILITY_THRESHOLD", 0.7)
        )

        engine.pulse_config.save_thresholds(test_data)
        with open(file_path, "r") as f:
            loaded_data = json.load(f)
        assert loaded_data == test_data

    # Cleanup: Restore original values
    engine.pulse_config.THRESHOLD_CONFIG_PATH = original_config_path
    engine.pulse_config._thresholds = original_thresholds_dict
    engine.pulse_config.CONFIDENCE_THRESHOLD = original_confidence_threshold
    engine.pulse_config.DEFAULT_FRAGILITY_THRESHOLD = original_fragility_threshold


# Test update_threshold function
def test_update_threshold(temp_thresholds_file: Path) -> None:
    """Test update_threshold function."""
    # Ensure initial state is as expected from the fixture
    # The fixture already reloaded engine.pulse_config, so its globals are fresh
    initial_thresholds = engine.pulse_config.load_thresholds()
    assert initial_thresholds.get("CONFIDENCE_THRESHOLD") == 0.8
    assert (
        engine.pulse_config.CONFIDENCE_THRESHOLD == 0.8
    )  # This assertion should pass if fixture works as expected

    # Update a threshold
    engine.pulse_config.update_threshold("CONFIDENCE_THRESHOLD", 0.95)

    # Verify the internal _thresholds is updated
    assert engine.pulse_config._thresholds.get("CONFIDENCE_THRESHOLD") == 0.95

    # Verify the saved file is updated
    with open(temp_thresholds_file, "r") as f:
        saved_data = json.load(f)
    assert saved_data.get("CONFIDENCE_THRESHOLD") == 0.95

    # Verify the global variable is updated
    # Since update_threshold uses globals()[name] = value,
    # the change should be reflected immediately in the module's globals.
    assert engine.pulse_config.CONFIDENCE_THRESHOLD == 0.95

    # Test updating a new threshold and verifying its global presence
    engine.pulse_config.update_threshold("NEW_TEST_THRESHOLD", 0.1)
    assert engine.pulse_config._thresholds.get("NEW_TEST_THRESHOLD") == 0.1
    # We cannot directly assert engine.pulse_config.NEW_TEST_THRESHOLD due to static analysis
    # but the update_threshold function's globals()[name] = value ensures it's set.

    # Clean up the added global variable to avoid affecting other tests
    # This is important because subsequent tests might not expect this global to exist.
    if hasattr(engine.pulse_config, "NEW_TEST_THRESHOLD"):
        delattr(engine.pulse_config, "NEW_TEST_THRESHOLD")
    if "NEW_TEST_THRESHOLD" in engine.pulse_config._thresholds:
        del engine.pulse_config._thresholds["NEW_TEST_THRESHOLD"]
    engine.pulse_config.save_thresholds(engine.pulse_config._thresholds)


# Test ConfigLoader class
def test_configloader_load_config_exists(temp_config_dir: Path) -> None:
    """Test ConfigLoader.load_config when the file exists."""
    loader = engine.pulse_config.ConfigLoader(config_dir=str(temp_config_dir))
    config = loader.load_config("config1.yaml")
    assert config == {"setting1": "value1", "setting2": 123}
    assert "config1.yaml" in loader.configs


def test_configloader_load_config_not_exists(
    temp_config_dir: Path, capsys: CaptureFixture[str]
) -> None:
    """Test ConfigLoader.load_config when the file does not exist."""
    loader = engine.pulse_config.ConfigLoader(config_dir=str(temp_config_dir))
    config = loader.load_config("non_existent.yaml")
    assert config == {}
    captured = capsys.readouterr()
    assert "Error loading configuration from" in captured.out


def test_configloader_load_all_configs(temp_config_dir: Path) -> None:
    """Test ConfigLoader.load_all_configs."""
    loader = engine.pulse_config.ConfigLoader(config_dir=str(temp_config_dir))
    loader.load_all_configs()
    assert "config1.yaml" in loader.configs
    assert "config2.yaml" in loader.configs
    assert loader.configs["config1.yaml"] == {"setting1": "value1", "setting2": 123}
    assert loader.configs["config2.yaml"] == {
        "list_setting": [1, 2, 3],
        "bool_setting": True,
    }


def test_configloader_get_config_value(temp_config_dir: Path) -> None:
    """Test ConfigLoader.get_config_value."""
    loader = engine.pulse_config.ConfigLoader(config_dir=str(temp_config_dir))
    # Test getting a value from a loaded config
    loader.load_config("config1.yaml")
    value = loader.get_config_value("config1.yaml", "setting1")
    assert value == "value1"

    # Test getting a value from a config that needs loading
    value = loader.get_config_value("config2.yaml", "bool_setting")
    assert value is True

    # Test getting a non-existent key
    value = loader.get_config_value("config1.yaml", "non_existent_key")
    assert value is None

    # Test getting a non-existent key with a default
    value = loader.get_config_value(
        "config1.yaml", "non_existent_key", default="default_value"
    )
    assert value == "default_value"

    # Test getting a value from a non-existent file
    value = loader.get_config_value("non_existent.yaml", "some_key")
    assert value is None

    # Test getting a value from a non-existent file with a default
    value = loader.get_config_value(
        "non_existent.yaml", "some_key", default="default_value"
    )
    assert value == "default_value"


def test_configloader_reload_config(temp_config_dir: Path) -> None:
    """Test ConfigLoader.reload_config."""
    loader = engine.pulse_config.ConfigLoader(config_dir=str(temp_config_dir))
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
def test_get_config_whole(temp_config_dir: Path) -> None:
    """Test get_config to retrieve the whole config dictionary."""
    # get_config uses the global config_loader, which is patched by the fixture
    config = engine.pulse_config.get_config("config1.yaml")
    assert config == {"setting1": "value1", "setting2": 123}


def test_get_config_value(temp_config_dir: Path) -> None:
    """Test get_config to retrieve a specific value."""
    # get_config uses the global config_loader, which is patched by the fixture
    value = engine.pulse_config.get_config("config2.yaml", "bool_setting")
    assert value is True


def test_get_config_value_default(temp_config_dir: Path) -> None:
    """Test get_config to retrieve a specific value with a default."""
    # get_config uses the global config_loader, which is patched by the fixture
    value = engine.pulse_config.get_config(
        "config1.yaml", "non_existent_key", default="default_value"
    )
    assert value == "default_value"


def test_get_config_non_existent_file(
    temp_config_dir: Path, capsys: CaptureFixture[str]
) -> None:
    """Test get_config for a non-existent file."""
    # get_config uses the global config_loader, which is patched by the fixture
    config = engine.pulse_config.get_config("non_existent.yaml")
    assert config == {}
    captured = capsys.readouterr()
    assert "Error loading configuration from" in captured.out


def test_get_config_value_non_existent_file(
    temp_config_dir: Path, capsys: CaptureFixture[str]
) -> None:
    """Test get_config for a value from a non-existent file."""
    # get_config uses the global config_loader, which is patched by the fixture
    value = engine.pulse_config.get_config("non_existent.yaml", "some_key")
    assert value is None
    captured = capsys.readouterr()
    assert "Error loading configuration from" in captured.out


def test_get_config_value_non_existent_file_default(
    temp_config_dir: Path, capsys: CaptureFixture[str]
) -> None:
    """Test get_config for a value from a non-existent file with a default."""
    # get_config uses the global config_loader, which is patched by the fixture
    value = engine.pulse_config.get_config(
        "non_existent.yaml", "some_key", default="default_value"
    )
    assert value == "default_value"
    captured = capsys.readouterr()
    assert "Error loading configuration from" in captured.out
