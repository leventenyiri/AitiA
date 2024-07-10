from client import MQTT, BROKER, PORT, PUBTOPIC, SUBTOPIC, CONFIG_PATH
import pytest
from unittest.mock import Mock, patch
import time
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def mqtt_instance():
    return MQTT()


@pytest.fixture
def mock_mqtt_client():
    with patch('client.mqtt_client.Client') as mock_client:
        yield mock_client.return_value


def test_mqtt_initialization(mqtt_instance):
    assert mqtt_instance.broker == BROKER
    assert mqtt_instance.port == PORT
    assert mqtt_instance.pubtopic == PUBTOPIC
    assert mqtt_instance.subtopic == SUBTOPIC
    assert mqtt_instance.client is None
    assert mqtt_instance.reconnect_counter == 0
