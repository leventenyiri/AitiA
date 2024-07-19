import pytest
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
