import os
import logging
import time
import json
import io
from PIL import Image
from datetime import datetime
import pytz
import pybase64
from mqtt import MQTT
from camera import Camera


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
