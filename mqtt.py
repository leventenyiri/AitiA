import logging
import time
from config import CONFIG_PATH, BROKER, PORT, PUBTOPIC, SUBTOPIC, QOS
from utils import log_execution_time
try:
    from paho.mqtt import client as mqtt_client
except:
    mqtt_client = None


class MQTT:
    def __init__(self):
        self.broker = BROKER
        self.pubtopic = PUBTOPIC
        self.subtopic = SUBTOPIC
        self.port = PORT
        self.qos = QOS
        self.client = None
        self.reconnect_counter = 0

    def init_receive(self):
        def on_message(client, userdata, msg):
            try:
                with open(CONFIG_PATH, "wb") as config:
                    config.write(msg.payload)
                logging.info(f"Received and saved config to {CONFIG_PATH}")
            except Exception as e:
                logging.error(e)
                # TODO: ask for config resend

        self.client.on_message = on_message
        self.client.subscribe(self.subtopic)

    def connect(self):
        def on_connect(client, userdata, flags, rc, properties=None):
            if rc == 0:
                logging.info("Connected to MQTT Broker!")
                # We need to reset the counter if the connection was successful
                self.reconnect_counter = 0
            else:
                logging.error(f"Failed to connect, return code {rc}")

        def on_disconnect(client, userdata, disconnect_flags, reason_code, properties=None):
            if reason_code == 0:
                logging.info("Disconnected voluntarily.")
                return

            logging.error(f"Involuntary disconnect. Reason code: {reason_code}")

            if self.reconnect_counter == 0:
                self.client.connect(self.broker, self.port)
            elif 1 <= self.reconnect_counter <= 4:
                time.sleep(2)
                logging.info(f"Trying to reconnect: {self.reconnect_counter} out of 5")
                self.client.connect(self.broker, self.port)
            elif self.reconnect_counter == 5:
                logging.critical("Couldn't reconnect 5 times, rebooting...")
                exit(2)

            self.reconnect_counter += 1

        self.client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2)
        self.client.on_connect = on_connect
        self.client.on_disconnect = on_disconnect
        self.client.connect_timeout = 0.5
        self.client.enable_logger()

        try:
            self.client.connect(self.broker, self.port)
            self.client.loop_start()
        except Exception as e:
            logging.error(f"Error connecting to the broker: {e}")
            exit(1)

        return self.client

    @log_execution_time("Image publish time")
    def publish(self, message):
        try:
            msg_info = self.client.publish(self.pubtopic, message, qos=self.qos)
            # Take this out in production
            # msg_info.wait_for_publish()
            # if msg_info.is_published():
            #     logging.info(f"Image and timestamp sent to topic {self.pubtopic}")
            # else:
            #     logging.error(f"Failed to send image and timestamp to topic {self.pubtopic}")
        except Exception as e:
            logging.error(f"Error publishing image and timestamp: {str(e)}")
            exit(1)

    def disconnect(self):
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
