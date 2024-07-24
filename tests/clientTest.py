import time
import threading
import pytest
from unittest.mock import patch, MagicMock
import json
from datetime import datetime
import pytz
import numpy as np
from app import App
from utils import System, CPUTemperature


@pytest.fixture
def mock_mqtt():
    with patch('app.MQTT', autospec=True) as mock_mqtt:
        mock_mqtt_instance = mock_mqtt.return_value
        mock_mqtt_instance.client = MagicMock()
        mock_mqtt_instance.client.is_connected.return_value = False  # Start disconnected
        yield mock_mqtt_instance


@pytest.fixture
def mock_camera():
    with patch('app.Camera', autospec=True) as mock_camera:
        camera_instance = mock_camera.return_value
        camera_instance.capture.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
        yield camera_instance


@pytest.fixture
def mock_rtc():
    with patch('utils.RTC.get_time', return_value=datetime.now(pytz.UTC).isoformat()):
        yield


@pytest.fixture
def mock_system():
    with patch('utils.System.shutdown'):
        yield


@pytest.fixture
def mock_cpu_temperature():
    with patch('utils.CPUTemperature') as mock_cpu:
        mock_cpu.return_value.temperature = 50.0
        yield


@pytest.fixture
def temp_config(tmp_path):
    config_data = {
        "Basic": {
            "quality": "3K",
            "mode": "single-shot",
            "period": "0:0:50",
            "manual_camera_settings_on": False,
            "wake_up_time": "06:00:00",
            "shut_down_time": "22:00:00"
        },
        "Camera": {
            "quality": 95,
            "width": 2560,
            "height": 1440
        }
    }
    config_file = tmp_path / "test_config.json"
    with open(config_file, 'w') as f:
        json.dump(config_data, f)
    return config_file


@pytest.fixture
def app(temp_config, mock_mqtt, mock_camera, mock_rtc, mock_system, mock_cpu_temperature):
    with patch('static_config.CONFIG_PATH', str(temp_config)):
        return App(str(temp_config))


def test_single_shot_mode(app):
    app.start()
    app.run()

    app.camera.start.assert_called_once()
    app.camera.capture.assert_called_once()
    app.mqtt.connect.assert_called_once()
    app.mqtt.init_receive.assert_called_once()
    app.mqtt.publish.assert_called_once()
    System.shutdown.assert_not_called()


def test_always_on_mode(app, monkeypatch):
    app.basic_config['mode'] = 'always_on'

    # Mock the run method to raise an exception after 3 calls
    original_run = app.run
    call_count = 0

    def mock_run():
        nonlocal call_count
        call_count += 1
        if call_count >= 3:
            raise Exception("Stop infinite loop")
        original_run()

    monkeypatch.setattr(app, 'run', mock_run)

    with pytest.raises(Exception, match="Stop infinite loop"):
        app.run_always()

    assert call_count == 3


def test_working_time_check_during_work_hours(app):
    with patch('utils.RTC.get_time', return_value=datetime(2023, 1, 1, 12, 0, 0, tzinfo=pytz.UTC).isoformat()):
        app.working_time_check()

    System.shutdown.assert_not_called()


def test_working_time_check_outside_work_hours(app):
    with patch('utils.RTC.get_time', return_value=datetime(2023, 1, 1, 23, 0, 0, tzinfo=pytz.UTC).isoformat()):
        app.working_time_check()

    System.shutdown.assert_called_once()
