# log_receiver.py

from paho.mqtt import client as mqtt_client
import logging
from datetime import datetime
import pytz
from static_config import BROKER, LOGGING_TOPIC

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# MQTT Configuration
PORT = 1883
USERNAME = "er-edge-3c547181"
PASSWORD = "admin"


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logging.info("Connected to MQTT Broker!")
        client.subscribe(LOGGING_TOPIC)
    else:
        logging.error(f"Failed to connect, return code {rc}")


def on_message(client, userdata, msg):
    try:
        log_entry = msg.payload.decode()
        level, message = log_entry.split('|', 1)
        timestamp = datetime.now(pytz.UTC)

        log_line = f"{timestamp} - {level} - {message}"
        logging.info(f"Received log: {log_line}")

        # You can add additional processing here, such as storing logs in a file or database

    except ValueError:
        logging.error(f"Received incorrectly formatted message: {msg.payload}")
    except Exception as e:
        logging.error(f"Error processing message: {e}")


def connect_mqtt() -> mqtt_client.Client:
    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2)
    client.username_pw_set(USERNAME, PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT)
    return client


def run():
    client = connect_mqtt()
    client.loop_forever()


if __name__ == "__main__":
    run()
