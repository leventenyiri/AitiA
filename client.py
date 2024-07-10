import os
import time
import json
import logging
import logging.config
import yaml
import io
import numpy as np
from PIL import Image
from subprocess import CalledProcessError
from datetime import datetime, timezone
import pybase64
import pytz
try:
    from libcamera import controls
    from picamera2 import Picamera2
    from paho.mqtt import client as mqtt_client
except ImportError:
    Picamera2 = None
    controls = None
    mqtt_client = None

# ----------------- Config file data ------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_CONFIG_PATH = os.path.join(SCRIPT_DIR, 'log_config.yaml')
CONFIG_PATH = os.path.join(SCRIPT_DIR, 'config.json')
BROKER = "192.168.0.103"
PORT = 1883
PUBTOPIC = "mqtt/rpi/image"
SUBTOPIC = "settings/er-edge"
# ------------------------------------------------------


class MQTT:
    def __init__(self):
        self.broker = BROKER
        self.pubtopic = PUBTOPIC
        self.subtopic = SUBTOPIC
        self.port = PORT
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

        self.client.connect(self.broker, self.port)
        self.client.loop_start()
        return self.client

    def publish(self, message):
        try:
            start_time = time.time()
            msg_info = self.client.publish(self.pubtopic, message, qos=1)
            # Take this out in production
            msg_info.wait_for_publish()
            end_time = time.time()
            time_taken = end_time - start_time
            logging.info(f"Time taken to publish: {time_taken:.2f} seconds")
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


class Logger:
    def __init__(self, filepath):
        self.filepath = filepath

    def start(self):
        try:
            if not os.path.exists(self.filepath):
                raise FileNotFoundError(f"Log configuration file not found: {self.filepath}")
            with open(self.filepath, 'r') as f:
                config = yaml.safe_load(f)
            logging.config.dictConfig(config)
            logging.info("Logging started")
        except Exception as e:
            logging.error(e)
            exit(1)


class Camera:
    def __init__(self, cam_config, basic_config):
        # The best quality is set as default
        self.quality = 95
        self.cam = Picamera2()

        # Set the costum camera settings from the config file
        if basic_config['manual_camera_settings_on']:
            self.width = cam_config['width']
            self.height = cam_config['height']
            self.quality = cam_config['quality']

        # Set the premade settings
        elif basic_config['quality'] == "4K":
            self.width = 3840
            self.height = 2160
        elif basic_config['quality'] == "3K":
            self.width = 2560
            self.height = 1440
        elif basic_config['quality'] == "HD":
            self.width = 1920
            self.height = 1080

    def start(self):
        config = self.cam.create_still_configuration({"size": (self.width, self.height)})
        self.cam.configure(config)
        self.cam.options["quality"] = self.quality
        self.cam.set_controls({"AfMode": controls.AfModeEnum.Continuous})
        self.cam.start(show_preview=False)

    def capture(self):
        image = self.cam.capture_array()
        return image


class App:
    def __init__(self, config_path):
        self.camera_config, self.basic_config = self.load_config(config_path)
        self.camera = Camera(self.camera_config, self.basic_config)
        self.mqtt = MQTT()

    @staticmethod
    def load_config(path):
        try:
            with open(path, 'r') as file:
                data = json.load(file)

            camera_config = data.get('Camera')
            basic_config = data.get('Basic')

            if camera_config is None or basic_config is None:
                raise KeyError("Key not found in the config file")

            return camera_config, basic_config

        # TODO: solve the config error issue
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in the config file: {path} - {str(e)}")
            exit(1)
        except FileNotFoundError as e:
            logging.error(f"Config file not found: {path} - {str(e)}")
            exit(1)
        except KeyError as e:
            logging.error(e)
            exit(1)
        except Exception as e:
            logging.error(e)
            exit(1)

    def create_message(self, image_array, timestamp):
        try:
            # Convert numpy array to bytes (JPEG)
            image = Image.fromarray(image_array)
            image_bytes = io.BytesIO()
            image.save(image_bytes, format='JPEG', quality=75)
            image_data = image_bytes.getvalue()

            image_base64 = pybase64.b64encode(image_data).decode('utf-8')

            # Create a JSON object with image data and timestamp
            message = {
                "timestamp": timestamp,
                "image": image_base64
            }
        except Exception as e:
            logging.error(f"Problem creating the message: {e}")
            exit(1)

        return json.dumps(message)

    def resize_image(self, image, max_size=(800, 600)):
        image.thumbnail(max_size, Image.LANCZOS)
        return image

    def start(self):
        # Start the camera
        self.camera.start()

        # Start the MQTT
        mqtt_client = self.mqtt.connect()
        mqtt_client.enable_logger()
        self.mqtt.init_receive()

    def run(self):
        # Capture the image
        start_capture = time.time()
        image_raw = self.camera.capture()
        capture_time = time.time() - start_capture
        logging.info(f"Image captured")
        logging.info(f"Image capture time: {capture_time:.2f} seconds")

        # Create the message
        timestamp = datetime.now(pytz.utc).isoformat()
        message = self.create_message(image_raw, timestamp)

        # Publish the message
        start_publish = time.time()
        self.mqtt.publish(message)
        publish_time = time.time() - start_publish
        logging.info(f"Image publish time: {publish_time:.2f} seconds")

    def run_old(self, duration):
        end_time = time.time() + duration
        while time.time() < end_time:
            start_capture = time.time()
            image_raw = self.camera.capture()
            capture_time = time.time() - start_capture
            logging.info(f"Image captured")
            logging.info(f"Image capture time: {capture_time:.2f} seconds")

            # Create the message
            timestamp = datetime.now(pytz.utc).isoformat()
            message = self.create_message(image_raw, timestamp)

            # Publish the message
            start_publish = time.time()
            self.mqtt.publish(message)
            publish_time = time.time() - start_publish
            logging.info(f"Image publish time: {publish_time:.2f} seconds")

        self.mqtt.disconnect()

    def run_always(self):
        while True:
            self.run()

    # Need RTC API for the implementation
    def run_periodically(self, period):
        return NotImplementedError


if __name__ == "__main__":

    logger = Logger(LOG_CONFIG_PATH)
    logger.start()

    app = App(CONFIG_PATH)
    app.start()

    try:
        # The app is taking pictures nonstop
        if app.basic_config['mode'] == "always_on":
            app.run_always()
    # The app is sending the images periodically and shuts down in between
        elif app.basic_config['mode'] == "periodic":
            app.run_periodically(app.basic_config['period'])
    # The app takes one picture then shuts down
        elif app.basic_config['mode'] == "single-shot":
            app.run()

    finally:
        app.mqtt.disconnect()

    print("Image capture and publish sequence completed")
    # Run for 60 seconds
    # TODO get the run time from config
    # app.run_old(duration=60)
