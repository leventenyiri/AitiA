import pytest
import json
import logging
from unittest.mock import patch, mock_open
from app import App
from camera import Camera
from mqtt import MQTT
from static_config import CONFIG_PATH


@pytest.fixture
def app():
    return App(CONFIG_PATH)


@pytest.fixture
def valid_config():
    return {
        "Basic": {
            "quality": "3K",
            "mode": "single-shot",
            "period": "0:0:50",
            "manual_camera_settings_on": False,
            "wake_up_time": "06:59:31",
            "shut_down_time": "22:00:00"
        },
        "Camera": {
            "quality": 95,
            "width": 3840,
            "height": 2160
        }
    }


def test_init_with_valid_json_config(app):
    assert isinstance(app.camera_config, dict)
    assert isinstance(app.basic_config, dict)
    assert isinstance(app.camera, Camera)
    assert isinstance(app.mqtt, MQTT)


def test_load_config_valid(valid_config):
    mock_file = mock_open(read_data=json.dumps(valid_config))
    with patch('builtins.open', mock_file):
        camera_config, basic_config = App.load_config(CONFIG_PATH)

    # The path we give to load_config doesn't matter, because the open function returns a mock object
    # so we have to also test if it was called with the correct path
    mock_file.assert_called_once_with(CONFIG_PATH, 'r')

    assert camera_config == valid_config["Camera"]
    assert basic_config == valid_config["Basic"]


def test_load_config_missing_key(valid_config):
    # Remove the required 'Basic' key from the valid_config
    del valid_config['Basic']
    mock_file = mock_open(read_data=json.dumps(valid_config))
    with patch('builtins.open', mock_file):
        camera_config, basic_config = App.load_config(CONFIG_PATH)

    # Check if basic_config contains default values
    assert basic_config == {
        "quality": "3K",
        "mode": "single-shot",
        "period": "0:0:50",
        "manual_camera_settings_on": False,
        "wake_up_time": "06:59:31",
        "shut_down_time": "22:00:00"
    }


# Test for invalid JSON in config file
def test_load_config_invalid_json():
    mock_file = mock_open(read_data="{invalid json")
    with patch('builtins.open', mock_file):
        with pytest.raises(SystemExit) as exc_info:
            App.load_config(CONFIG_PATH)
    assert exc_info.value.code == 1
    # Explanation: This test verifies that load_config exits correctly
    # when the config file contains invalid JSON.


# Test for file not found scenario
def test_load_config_file_not_found():
    with patch('builtins.open', side_effect=FileNotFoundError):
        with pytest.raises(SystemExit) as exc_info:
            App.load_config(CONFIG_PATH)
    assert exc_info.value.code == 1
    # Explanation: This test ensures that load_config handles the case
    # where the config file is not found, exiting with the correct code.


# Test for general exception handling
def test_load_config_general_exception():
    with patch('builtins.open', side_effect=Exception("Unexpected error")):
        with pytest.raises(SystemExit) as exc_info:
            App.load_config(CONFIG_PATH)
    assert exc_info.value.code == 1
    # Explanation: This test checks if load_config correctly handles
    # and exits for any unexpected exceptions.


# Parametrized test for various error logging scenarios
@pytest.mark.parametrize("exception, expected_log", [
    (json.JSONDecodeError("Expecting value", "", 0), "Invalid JSON in the config file"),
    (FileNotFoundError(), "Config file not found"),
    (Exception("Unexpected error"), "Unexpected error loading config")
])
def test_load_config_logging(exception, expected_log, caplog):
    caplog.set_level(logging.ERROR)
    with patch('builtins.open', side_effect=exception):
        with pytest.raises(SystemExit):
            App.load_config(CONFIG_PATH)
    assert expected_log in caplog.text
    # Explanation: This parametrized test checks if load_config correctly logs
    # different types of errors that might occur during config loading.
    # The way it works is, each time it runs, exception and expected_log will be a different pair of values.
    # E.g: if the side_effect is set to FileNotFoundError, we will be expecting it to log "Config file not found".


@pytest.mark.parametrize("section, key, default_value", [
    ("Basic", "quality", "3K"),
    ("Basic", "mode", "single-shot"),
    ("Basic", "period", "0:0:50"),
    ("Basic", "manual_camera_settings_on", False),
    ("Basic", "wake_up_time", "06:59:31"),
    ("Basic", "shut_down_time", "22:00:00"),
    ("Camera", "quality", 95),
    ("Camera", "width", 3840),
    ("Camera", "height", 2160)
])
def test_load_config_missing_nested_key(valid_config, section, key, default_value):
    # Remove the specified key
    del valid_config[section][key]

    mock_file = mock_open(read_data=json.dumps(valid_config))
    with patch('builtins.open', mock_file):
        camera_config, basic_config = App.load_config(CONFIG_PATH)

    if section == "Basic":
        assert basic_config[key] == default_value
    elif section == "Camera":
        assert camera_config[key] == default_value

    # Explanation: This test verifies that load_config correctly handles
    # the case where various nested keys are missing from the config.


def test_load_config_overrides_defaults():
    # Create a config that differs from the defaults
    custom_config = {
        "Basic": {
            "quality": "4K",
            "mode": "periodic",
            "period": "0:1:00",
            "manual_camera_settings_on": True,
            "wake_up_time": "07:00:00",
            "shut_down_time": "23:00:00"
        },
        "Camera": {
            "quality": 90,
            "width": 4096,
            "height": 2304
        }
    }

    mock_file = mock_open(read_data=json.dumps(custom_config))
    with patch('builtins.open', mock_file):
        camera_config, basic_config = App.load_config(CONFIG_PATH)

    # Assert that the loaded config matches our custom values, not the defaults
    assert basic_config == custom_config["Basic"]
    assert camera_config == custom_config["Camera"]


def test_load_config_extra_keys():
    extra_keys_config = {
        "Basic": {
            "quality": "3K",
            "extra_key": "should be ignored"
        },
        "Camera": {
            "quality": 95,
            "width": 3840,
            "height": 2160,
            "another_extra": 42
        },
        "ExtraSection": {
            "should": "be ignored"
        }
    }
    expected_basic = {
        "quality": "3K",
        "mode": "single-shot",
        "period": "0:0:50",
        "manual_camera_settings_on": False,
        "wake_up_time": "06:59:31",
        "shut_down_time": "22:00:00"
    }
    expected_camera = {
        "quality": 95,
        "width": 3840,
        "height": 2160
    }

    mock_file = mock_open(read_data=json.dumps(extra_keys_config))
    with patch('builtins.open', mock_file):
        camera_config, basic_config = App.load_config(CONFIG_PATH)

    assert camera_config == expected_camera
    assert basic_config == expected_basic

    assert "extra_key" not in basic_config
    assert "another_extra" not in camera_config
    assert "ExtraSection" not in camera_config and "ExtraSection" not in basic_config
