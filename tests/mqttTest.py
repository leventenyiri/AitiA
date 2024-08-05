from source.mqtt import MQTT, BROKER, PORT, PUBTOPIC, SUBTOPIC
import pytest
from unittest.mock import patch, MagicMock
from paho.mqtt import client as mqtt_client
import logging
import json
import numpy as np
from PIL import Image
import pybase64
import io


@pytest.fixture
def mqtt_instance():
    return MQTT()


@pytest.fixture
def mock_client():
    with patch('mqtt.mqtt_client.Client', autospec=True) as mock_client_class:
        # If i simply returned the mock_client_class, then it would have returned the class itself, but if i return the
        # return value, then it returns an object of that class, which is what i want
        mock_client = mock_client_class.return_value
        yield mock_client


def test_mqtt_initialization(mqtt_instance):
    assert mqtt_instance.broker == BROKER
    assert mqtt_instance.port == PORT
    assert mqtt_instance.pubtopic == PUBTOPIC
    assert mqtt_instance.subtopic == SUBTOPIC
    assert isinstance(mqtt_instance.client, mqtt_client.Client)
    assert mqtt_instance.reconnect_counter == 0


def test_connect(mqtt_instance, mock_client):
    mqtt_instance.connect()

    # Check if Client was created with the correct argument
    # mqtt_client.Client.assert_called_once_with(mqtt_client.CallbackAPIVersion.VERSION2)

    # Check if the client is assigned to the instance
    # assert mqtt_instance.client == mock_client

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


def test_disconnect(mqtt_instance, mock_client):
    mqtt_instance.connect()  # This sets up the client
    mqtt_instance.disconnect()

    mock_client.loop_stop.assert_called_once()
    mock_client.disconnect.assert_called_once()


def test_on_disconnect_voluntary(mqtt_instance, caplog):
    caplog.set_level(logging.INFO)
    mqtt_instance.connect()
    on_disconnect = mqtt_instance.client.on_disconnect
    on_disconnect(mqtt_instance.client, None, None, 0)
    assert "Disconnected voluntarily." in caplog.text


def test_on_disconnect_involuntary(mqtt_instance, caplog, mock_client):
    caplog.set_level(logging.ERROR)
    mqtt_instance.connect()
    on_disconnect = mqtt_instance.client.on_disconnect
    on_disconnect(mqtt_instance.client, None, None, 1)
    assert "Involuntary disconnect. Reason code: 1" in caplog.text
    mock_client.reconnect.assert_called_once


def test_reconnection_attempts(mqtt_instance, caplog, mock_client):
    caplog.set_level(logging.INFO)
    mqtt_instance.connect()
    mqtt_instance.reconnect_counter = 0  # Reset the counter
    on_disconnect = mqtt_instance.client.on_disconnect

    for i in range(1, 6):
        caplog.clear()  # Clear previous log messages
        on_disconnect(mqtt_instance.client, None, None, 1)
        assert f"Trying to reconnect: {i} out of 5" in caplog.text
        mock_client.reconnect.assert_called()

    caplog.clear()  # Clear previous log messages
    with pytest.raises(SystemExit):
        on_disconnect(mqtt_instance.client, None, None, 1)
    assert "Couldn't reconnect 5 times, rebooting..." in caplog.text


def test_connect_exception(mqtt_instance, mock_client, caplog):
    # Set up the mock to raise an exception when connect_async is called
    mock_client.connect_async.side_effect = Exception("Connection error")

    # Set the log level to capture error messages
    caplog.set_level(logging.ERROR)

    # Expect the connect method to raise a SystemExit
    with pytest.raises(SystemExit) as excinfo:
        mqtt_instance.connect()

    assert excinfo.value.code == 1
    assert "Error connecting to the broker: Connection error" in caplog.text

    mock_client.connect_async.assert_called_once_with(mqtt_instance.broker, mqtt_instance.port)

    # Verify that loop_start was not called (since an exception was raised)
    mock_client.loop_start.assert_not_called()


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


def test_publish(mqtt_instance, mock_client):
    # Set up the client
    mqtt_instance.connect()

    # Create a dummy image
    image_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

    # Create a timestamp
    timestamp = "2023-07-19T10:30:00Z"

    # Mock the CPU temperature function
    with patch('utils.get_cpu_temperature', return_value=45.6):
        # Create the message
        message = create_test_message(image_array, timestamp)

    # Call the publish method
    mqtt_instance.publish(message)

    # Assert that publish was called with the correct arguments
    mock_client.publish.assert_called_once_with(
        mqtt_instance.pubtopic,
        message,
        qos=mqtt_instance.qos
    )

    # Not really needed, might delete later idk
    decoded_message = json.loads(message)
    assert "timestamp" in decoded_message
    assert "image" in decoded_message
    assert "CPU_temperature" in decoded_message
    assert decoded_message["timestamp"] == timestamp
    assert decoded_message["CPU_temperature"] == 45.6


def create_test_message(image_array, timestamp):
    # Convert numpy array to bytes (JPEG)
    image = Image.fromarray(image_array)
    image_bytes = io.BytesIO()
    image.save(image_bytes, format='JPEG', quality=75)
    image_data = image_bytes.getvalue()
    image_base64 = pybase64.b64encode(image_data).decode('utf-8')

    # Use a fixed CPU temperature for the test
    cpu_temp = 45.6

    message = {
        "timestamp": timestamp,
        "image": image_base64,
        "CPU_temperature": cpu_temp
    }
    return json.dumps(message)
