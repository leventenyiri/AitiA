from mqtt import MQTT, BROKER, PORT, PUBTOPIC, SUBTOPIC
import pytest
from unittest.mock import patch
from paho.mqtt import client as mqtt_client
import logging


@pytest.fixture
def mqtt_instance():
    return MQTT()


@pytest.fixture
def mock_mqtt_client():
    with patch('paho.mqtt.client.Client', autospec=True) as mock_client:
        yield mock_client


def test_mqtt_initialization(mqtt_instance):
    assert mqtt_instance.broker == BROKER
    assert mqtt_instance.port == PORT
    assert mqtt_instance.pubtopic == PUBTOPIC
    assert mqtt_instance.subtopic == SUBTOPIC
    assert mqtt_instance.client is None
    assert mqtt_instance.reconnect_counter == 0


def test_connect(mqtt_instance, mock_mqtt_client):
    mqtt_instance.connect()

    # Check if Client was called with the correct argument
    mock_mqtt_client.assert_called_once_with(mqtt_client.CallbackAPIVersion.VERSION2)

    # Check if the client is assigned to the instance
    assert mqtt_instance.client == mock_mqtt_client.return_value

    # Check if connect was called on the client
    mqtt_instance.client.connect.assert_called_once_with(mqtt_instance.broker, mqtt_instance.port)

    # Check if loop_start was called
    mqtt_instance.client.loop_start.assert_called_once()


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
