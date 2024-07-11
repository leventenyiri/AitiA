from mqtt import MQTT, BROKER, PORT, PUBTOPIC, SUBTOPIC, CONFIG_PATH
import pytest
from unittest.mock import Mock, patch, create_autospec
from paho.mqtt import client as mqtt_client


@pytest.fixture
def mqtt_instance():
    return MQTT()


@pytest.fixture
def mock_mqtt_client():
    with patch('paho.mqtt.client.Client') as mock_client:
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

    mock_mqtt_client.assert_called_once_with(mqtt_client.CallbackAPIVersion.VERSION2)
    assert mqtt.client == mock_mqtt_client.return_value
