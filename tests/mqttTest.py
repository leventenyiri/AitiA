from mqtt import MQTT, BROKER, PORT, PUBTOPIC, SUBTOPIC
import pytest
from unittest.mock import patch, MagicMock
from paho.mqtt import client as mqtt_client
import logging
import json


@pytest.fixture
def mqtt_instance():
    return MQTT()


@pytest.fixture
def mock_client():
    with patch('mqtt.mqtt_client.Client', autospec=True) as mock_client_class:
        # If i simply returned the mock_client_class, then it would have returned the class itself, but if i return the
        # return value, then it returns an object of that class, which is what i want
        mock_client = mock_client_class.return_value
        # mock_client.connect_async = MagicMock()
        # mock_client.loop_start = MagicMock()
        yield mock_client


def test_mqtt_initialization(mqtt_instance):
    assert mqtt_instance.broker == BROKER
    assert mqtt_instance.port == PORT
    assert mqtt_instance.pubtopic == PUBTOPIC
    assert mqtt_instance.subtopic == SUBTOPIC
    assert mqtt_instance.client is None
    assert mqtt_instance.reconnect_counter == 0


def test_connect(mqtt_instance, mock_client):
    mqtt_instance.connect()

    # Check if Client was created with the correct argument
    mqtt_client.Client.assert_called_once_with(mqtt_client.CallbackAPIVersion.VERSION2)

    # Check if the client is assigned to the instance
    assert mqtt_instance.client == mock_client

    mock_client.username_pw_set.assert_called_once_with('er-edge-3c547181', 'admin')
    mock_client.enable_logger.assert_called_once()
    mock_client.connect_async.assert_called_once_with(mqtt_instance.broker, mqtt_instance.port)
    mock_client.loop_start.assert_called_once()


def test_on_connect_successful(mqtt_instance, caplog):
    # Simulate a successful connection
    caplog.set_level(logging.INFO)

    # Connect and get the on_connect callback
    mqtt_instance.connect()
    on_connect = mqtt_instance.client.on_connect

    # Directly call the on_connect callback
    on_connect(mqtt_instance.client, None, None, 0)

    # Check if the log message is correct
    assert "Connected to MQTT Broker!" in caplog.text
    # Check if the reconnect counter was reset
    assert mqtt_instance.reconnect_counter == 0


def test_on_connect_failed(mqtt_instance, caplog):
    caplog.set_level(logging.ERROR)
    mqtt_instance.connect()
    on_connect = mqtt_instance.client.on_connect
    on_connect(mqtt_instance.client, None, None, 1)

    assert "Failed to connect, return code 1" in caplog.text
    assert mqtt_instance.reconnect_counter == 0  # Should not change on failed connect


def test_init_receive(mqtt_instance, mock_client):
    mqtt_instance.connect()  # This sets up the client
    mqtt_instance.init_receive()

    # Check if subscribe was called with the correct topic
    mock_client.subscribe.assert_called_once_with(mqtt_instance.subtopic)

    test_config = {
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

    test_payload = json.dumps(test_config).encode('utf-8')

    # Test the on_message callback
    msg = MagicMock()
    msg.payload = test_payload
    mock_client.on_message(mock_client, None, msg)
    # Check the config.json and temp_config.json files
