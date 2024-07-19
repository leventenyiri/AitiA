import pytest
from unittest.mock import patch, Mock
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
