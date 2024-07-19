import pytest
import json
import numpy as np
from unittest.mock import patch
from app import App
from camera import Camera
from mqtt import MQTT
from static_config import CONFIG_PATH


@pytest.fixture
def app():
    return App(CONFIG_PATH)


def test_init_with_valid_json_config(app):
    assert isinstance(app.camera_config, dict)
    assert isinstance(app.basic_config, dict)
    assert isinstance(app.camera, Camera)
    assert isinstance(app.mqtt, MQTT)


@patch('utils.RTC.get_time', return_value='2024-07-19T10:00:00')
@patch('utils.System.shutdown')
def test_working_hours(mock_shutdown, mock_get_time, app):
    app.basic_config = {
        "wake_up_time": "06:00:00",
        "shut_down_time": "20:00:00"
    }
    app.working_time_check()
    mock_shutdown.assert_not_called()


@patch('utils.RTC.get_time', return_value='2024-07-19T22:00:00')
@patch('utils.System.shutdown')
def test_shutdown_after_shut_down_time(mock_shutdown, mock_get_time, app):
    app.basic_config = {
        "wake_up_time": "06:00:00",
        "shut_down_time": "20:00:00"
    }
    app.working_time_check()
    mock_shutdown.assert_called_once()


@patch('utils.RTC.get_time', return_value='2024-07-19T05:00:00')
@patch('utils.System.shutdown')
def test_shutdown_before_wake_up_time(mock_shutdown, mock_get_time, app):
    app.basic_config = {
        "wake_up_time": "06:00:00",
        "shut_down_time": "20:00:00"
    }
    app.working_time_check()
    mock_shutdown.assert_called_once()


@patch('utils.RTC.get_time', return_value='2024-07-19T02:00:00')
@patch('utils.System.shutdown')
def test_night_mode(mock_shutdown, mock_get_time, app):
    app.basic_config = {
        "wake_up_time": "20:00:00",
        "shut_down_time": "06:00:00"
    }
    app.working_time_check()
    mock_shutdown.assert_not_called()


@patch('utils.CPUTemperature')
@patch('utils.get_cpu_temperature')
def test_create_message_valid_input(mock_get_cpu_temperature, MockCPUTemperature, app):
    # Mock the temperature attribute of the CPUTemperature instance
    mock_temp_instance = MockCPUTemperature.return_value
    mock_temp_instance.temperature = 45.6
    image = np.random.randint(0, 256, (480, 640), dtype=np.uint8)
    timestamp = '2024-07-19T12:00:00Z'

    message = app.create_message(image, timestamp)
    message_dict = json.loads(message)

    assert message_dict['timestamp'] == timestamp
    assert message_dict['CPU_temperature'] == 45.6
    assert message_dict['image'] is not None


@patch('utils.CPUTemperature', autospec=True)
@patch('utils.get_cpu_temperature')
def test_create_message_invalid_image(mock_get_cpu_temperature, MockCPUTemperature, app):
    # Mock the temperature attribute of the CPUTemperature instance
    MockCPUTemperature.return_value.temperature = 45.6
    image = "Invalid image data"
    timestamp = '2024-07-19T12:00:00Z'

    with pytest.raises(Exception):
        app.create_message(image, timestamp)


@patch('utils.CPUTemperature', autospec=True)
@patch('utils.get_cpu_temperature')
def test_create_message_invalid_cpu_temp_read(mock_get_cpu_temperature, MockCPUTemperature, app):
    # Mock the temperature attribute of the CPUTemperature instance
    MockCPUTemperature.side_effect = Exception('CPU temperature reading error')
    image = np.random.randint(0, 256, (480, 640), dtype=np.uint8)
    timestamp = '2024-07-19T12:00:00Z'

    with pytest.raises(Exception):
        app.create_message(image, timestamp)
