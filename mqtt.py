import logging
import time
import shutil
from static_config import BROKER, PUBTOPIC, SUBTOPIC, PORT, QOS, TEMP_CONFIG_PATH, CONFIG_PATH, USERNAME, PASSWORD
from utils import log_execution_time
try:
    from paho.mqtt import client as mqtt_client
except ImportError:
    mqtt_client = None
import json
import socket


class MQTT:
    def __init__(self):
        self.broker = BROKER
        self.pubtopic = PUBTOPIC
        self.subtopic = SUBTOPIC
        self.port = PORT
        self.qos = QOS
        self.client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2)
        self.reconnect_counter = 0
        self.config_changed = False

    def init_receive(self):
        def on_message(client, userdata, msg):
            try:
                # Parse the JSON message
                config_data = json.loads(msg.payload)

                # Write the formatted JSON to the temp file
                with open(TEMP_CONFIG_PATH, "w") as temp_config:
                    json.dump(config_data, temp_config, indent=4)

                logging.info(f"Received config to {TEMP_CONFIG_PATH}")

                # Copy the file
                shutil.copyfile(TEMP_CONFIG_PATH, CONFIG_PATH)
                logging.info(f"Config saved to {CONFIG_PATH}")
                # Signal the config change
                self.config_changed = True

            except json.JSONDecodeError as e:
                logging.error(f"Invalid JSON received: {e}")
            except Exception as e:
                logging.error(f"Error processing message: {e}")

        self.client.on_message = on_message
        self.client.subscribe(self.subtopic)

    def is_config_changed(self):
        return self.config_changed

    def connect(self):
        def on_connect(client, userdata, flags, rc, properties=None):
            if rc == 0:
                logging.info("Connected to MQTT Broker!")
            else:
                logging.error(f"Failed to connect, return code {rc}")

        self.client.on_connect = on_connect
        self.client.username_pw_set(USERNAME, PASSWORD)
        self.client.enable_logger()

        def on_disconnect(client, userdata, disconnect_flags, reason_code, properties=None):
            if reason_code == 0:
                logging.info("Disconnected voluntarily.")
                return
            logging.error(f"Involuntary disconnect. Reason code: {reason_code}")

            self.reconnect_counter += 1

            if self.reconnect_counter <= 5:
                logging.info(f"Trying to reconnect: {self.reconnect_counter} out of 5")
                time.sleep(2)  # Sleep for all reconnection attempts
                self.client.reconnect()
            else:
                logging.critical("Couldn't reconnect 5 times, rebooting...")
                exit(2)

        def on_connect_fail(client, userdata):
            while not self.client.is_connected():
                # Implement sleep to reduce power consumption if necessary
                self.client.connect(self.broker, self.port)
                time.sleep(1)

        self.client.on_connect = on_connect
        self.client.on_disconnect = on_disconnect
        self.client.on_connect_fail = on_connect_fail
        self.client.username_pw_set(USERNAME, PASSWORD)
        self.client.enable_logger()

        network_connect_counter = 0
        # Making sure the network is up before trying to connect
        while not self.is_network_available():
            logging.info("Waiting for network to become available...")
            time.sleep(0.5)
            network_connect_counter += 1
            if network_connect_counter == 20:
                logging.error("Connecting to network failed 20 times, restarting script...")
                exit(1)

        self.client.connect(self.broker, self.port)
        self.client.loop_start()

        return self.client

    def is_network_available(self):
        try:
            socket.create_connection((BROKER, PORT), timeout=5)
            return True
        except OSError:
            return False
        except Exception as e:
            logging.error(f"Error during creating connection: {e}")
            exit(1)

    @log_execution_time("Image publish time")
    def publish(self, message):
        try:
            msg_info = self.client.publish(self.pubtopic, message, qos=self.qos)

            msg_info.wait_for_publish()
            if msg_info.is_published():
                logging.info(f"Image and timestamp sent to topic {self.pubtopic}")
            else:
                logging.error(f"Failed to send image and timestamp to topic {self.pubtopic}")
        except Exception as e:
            logging.error(f"Error publishing image and timestamp: {str(e)}")
            exit(1)

    def disconnect(self):
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
