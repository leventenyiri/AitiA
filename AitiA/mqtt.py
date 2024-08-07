import logging
import time
import shutil
from .static_config import BROKER, SUBTOPIC, PORT, QOS, TEMP_CONFIG_PATH, CONFIG_PATH, USERNAME, PASSWORD
try:
    from paho.mqtt import client as mqtt_client
except ImportError:
    mqtt_client = None
import json
import socket
import threading


class MQTT:
    """
    A class to handle MQTT client operations.

    This class manages the connection to an MQTT broker, publishes messages,
    and handles incoming configuration messages.

    Attributes
    ----------
    broker : str
        The address of the MQTT broker.
    subtopic : str
        The topic to subscribe to for incoming messages.
    port : int
        The port number for the MQTT broker connection.
    qos : int
        The Quality of Service level for MQTT messages.
    client : mqtt_client.Client
        The MQTT client instance.
    reconnect_counter : int
        A counter to track reconnection attempts.
    config_received_event : threading.Event
        An event to signal when a new configuration is received.
    config_confirm_message : str
        A message to confirm the receipt of a new configuration.

    Methods
    -------
    is_connected()
        Check if the MQTT client is connected to the broker.
    get_client()
        Get the MQTT client instance.
    init_receive()
        Initialize the MQTT client to receive messages.
    reset_config_received_event()
        Reset the config_received_event.
    connect()
        Connect to the MQTT broker.
    is_broker_available()
        Check if the MQTT broker is available.
    publish(message, topic)
        Publish a message to a specified topic.
    disconnect()
        Disconnect the MQTT client from the broker.
    """

    def __init__(self):
        self.broker = BROKER
        self.subtopic = SUBTOPIC
        self.port = PORT
        self.qos = QOS
        self.client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2)
        self.reconnect_counter = 0
        self.config_received_event = threading.Event()
        self.config_confirm_message = "config-nok|Confirm message uninitialized"

    def is_connected(self):
        return self.client.is_connected() if self.client else False

    def get_client(self):
        return self.client

    def init_receive(self):
        """
        Initializes the MQTT client to receive messages on the subscribed topic and process them.

        This function sets up the MQTT client's `on_message` callback to handle incoming messages.
        When a message is received, it attempts to parse the message as JSON, validate the configuration,
        and save it to a temporary file. If successful, the configuration is copied to the final
        configuration path, and a confirmation message is set. If an error occurs, an appropriate
        error message is set.
        """
        def on_message(client, userdata, msg):
            from .app_config import Config
            try:
                # Parse the JSON message
                config_data = json.loads(msg.payload)
                logging.info("Starting config validation...")
                Config.validate_config(config_data)

                # Write the validated JSON to the temp file
                with open(TEMP_CONFIG_PATH, "w") as temp_config:
                    json.dump(config_data, temp_config, indent=4)

                logging.info(f"Received config to {TEMP_CONFIG_PATH}")

                # Copy the file
                shutil.copyfile(TEMP_CONFIG_PATH, CONFIG_PATH)
                logging.info(f"Config saved to {CONFIG_PATH}")
                self.config_confirm_message = "config-ok"
                # Signal the config change
                self.config_received_event.set()

            except json.JSONDecodeError as e:
                self.config_confirm_message = f"config-nok|Invalid JSON received: {e}"
                logging.error(f"Invalid JSON received: {e}")
                # Signal the config change
                self.config_received_event.set()
            except Exception as e:
                self.config_confirm_message = f"config-nok| {e}"
                logging.error(f"Error processing message: {e}")
                # Signal the config change
                self.config_received_event.set()

        self.client.on_message = on_message
        self.client.subscribe(self.subtopic)

    def reset_config_received_event(self):
        self.config_received_event.clear()

    def connect(self):
        """
        Connect to the MQTT broker.

        This method sets up various callbacks for connection events and
        attempts to establish a connection to the MQTT broker.

        Returns
        -------
        mqtt_client.Client
            The connected MQTT client instance.
        """
        def on_connect(client, userdata, flags, rc, properties=None):
            if rc == 0:
                logging.info("Connected to MQTT Broker!")
            else:
                logging.error(f"Failed to connect, return code {rc}")

        self.client.on_connect = on_connect
        self.client.username_pw_set(USERNAME, PASSWORD)

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
                logging.error("Failed to connect to MQTT Broker!")
                # Implement sleep to reduce power consumption if necessary
                self.client.connect(self.broker, self.port)
                time.sleep(1)

        self.client.on_connect = on_connect
        self.client.on_disconnect = on_disconnect
        self.client.on_connect_fail = on_connect_fail
        self.client.username_pw_set(USERNAME, PASSWORD)
        self.client.disable_logger()

        network_connect_counter = 0
        # Making sure the network is up before trying to connect
        while not self.is_broker_available():
            logging.info("Waiting for broker to become available...")
            time.sleep(0.5)
            network_connect_counter += 1
            if network_connect_counter == 20:
                logging.error("Connecting to network failed 20 times, restarting script...")
                exit(1)

        self.client.connect(self.broker, self.port)
        self.client.loop_start()

        return self.client

    def is_broker_available(self):
        """
        Check if the network is available by trying to connect to the MQTT broker.

        Returns:
            bool: True if the network is available, False otherwise.

        Raises:
        Exception: If an error occurs during the network check.
        """
        try:
            socket.create_connection((BROKER, PORT), timeout=5)
            return True
        except OSError:
            return False
        except Exception as e:
            logging.error(f"Error during creating connection: {e}")
            exit(1)

    def publish(self, message, topic):
        """
        Publish a message to a specified topic.

        Parameters
        ----------
        message : str
            The message to publish.
        topic : str
            The topic to publish the message to.

        Raises
        ------
        SystemExit
            If there's an error during publishing.
        """
        try:
            msg_info = self.client.publish(topic, message, qos=self.qos)
            msg_info.wait_for_publish()

        except Exception:
            exit(1)

    def disconnect(self):
        """
        Disconnect the MQTT client from the broker.

        This method stops the network loop and disconnects the client from the MQTT broker.
        """
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
