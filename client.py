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
import base64
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
SUBTOPIC = "settings/"
# ------------------------------------------------------

class MQTT:
    def __init__(self):
        self.broker = BROKER
        self.pubtopic = PUBTOPIC
        self.subtopic = SUBTOPIC
        self.port = PORT
        self.client = None

    def connect(self):
        def on_connect(client, userdata, flags, rc, properties=None):
            if rc == 0:
                logging.info("Connected to MQTT Broker!")
            else:
                logging.error(f"Failed to connect, return code {rc}")

        self.client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2)
        self.client.on_connect = on_connect
        self.client.connect(self.broker, self.port)
        self.client.loop_start()
        return self.client

    def publish(self, message):
        if not self.client:
            logging.error("MQTT client not connected")
            return

        try:
            start_time = time.time()
            msg_info = self.client.publish(self.pubtopic, message, qos=1)
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

    def disconnect(self):
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()

class Logger:
    def __init__(self, filepath):
        self.filepath = filepath

    def start(self):
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"Log configuration file not found: {self.filepath}")
        with open(self.filepath, 'r') as f:
            config = yaml.safe_load(f)
        logging.config.dictConfig(config)
        logging.info("Logging started")

class Camera:
    def __init__(self, config):
        self.width = config['width']
        self.height = config['height']
        self.cam = Picamera2()
        self.counter = 0

    def start(self):
        config = self.cam.create_still_configuration({"size": (self.width, self.height)})
        self.cam.configure(config)
        self.cam.set_controls({"AfMode": controls.AfModeEnum.Continuous})
        self.cam.start(show_preview=False)
        #time.sleep(2)

    def capture(self):
        image = self.cam.capture_array()
        self.counter += 1
        return image

class App:
    def __init__(self, config_path):
        self.camera_config = self._load_camera_config(config_path)
        self.camera = Camera(self.camera_config)
        self.mqtt = MQTT()

    @staticmethod
    def _load_camera_config(path):
        try:
            with open(path, 'r') as file:
                data = json.load(file)
            camera_config = data.get('Camera')
            if camera_config is None:
                raise KeyError("Key 'Camera' not found in the config file")
            return camera_config
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in the config file: {path} - {str(e)}")
            raise
        except FileNotFoundError as e:
            logging.error(f"Config file not found: {path} - {str(e)}")
            raise
        
    def create_message(self, image_array, timestamp):
        # Convert numpy array to bytes
        image = Image.fromarray(image_array)
        image_bytes = io.BytesIO()
        image.save(image_bytes, format='JPEG')
        image_data = image_bytes.getvalue()
        
        # Encode image data as base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')

        # Create a JSON object with image data and timestamp
        message = {
            "timestamp": timestamp,
            "image": image_base64
        }
        
        return json.dumps(message) 
        

    def run(self, duration):
        self.camera.start()
        self.mqtt.connect()
        end_time = time.time() + duration
        while time.time() < end_time:
            start_capture = time.time()
            image_raw = self.camera.capture()
            capture_time = time.time() - start_capture
            logging.info(f"Image captured")
            logging.info(f"Image capture time: {capture_time:.2f} seconds")
            
            # Create the message from the timestamp and image
            timestamp = datetime.now(timezone.utc).isoformat()
            message = self.create_message(image_raw, timestamp)
            
            # Publish the message
            start_publish = time.time()
            self.mqtt.publish(message)
            publish_time = time.time() - start_publish
            logging.info(f"Image publish time: {publish_time:.2f} seconds")

            total_time = time.time() - start_capture

        self.mqtt.disconnect()

if __name__ == "__main__":
    logger = Logger(LOG_CONFIG_PATH)
    logger.start()

    app = App(CONFIG_PATH)

    # Run for 60 seconds (1 minute)
    app.run(duration=60)

    print("Image capture and publish sequence completed")