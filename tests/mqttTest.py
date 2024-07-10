from client import MQTT, BROKER, PORT, PUBTOPIC, SUBTOPIC, CONFIG_PATH
import pytest
from unittest.mock import Mock, patch, create_autospec
import time
import logging
import sys
import os
import paho.mqtt.client as mqtt_client

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def mqtt_instance():
    return MQTT()


@pytest.fixture
def mock_mqtt_client():
    with patch('client.mqtt_client', new=create_autospec(mqtt_client)):
        yield mqtt_client.Client.return_value


def test_mqtt_initialization(mqtt_instance):
    assert mqtt_instance.broker == BROKER
    assert mqtt_instance.port == PORT
    assert mqtt_instance.pubtopic == PUBTOPIC
    assert mqtt_instance.subtopic == SUBTOPIC
    assert mqtt_instance.client is None
    assert mqtt_instance.reconnect_counter == 0


def test_connect(mqtt_instance, mock_mqtt_client):
    mqtt_instance.connect()

    assert mqtt_instance.client == mock_mqtt_client
    mock_mqtt_client.on_connect.assert_called_once()
    mock_mqtt_client.on_disconnect.assert_called_once()
    mock_mqtt_client.connect.assert_called_once_with(BROKER, PORT)
    mock_mqtt_client.loop_start.assert_called_once()
