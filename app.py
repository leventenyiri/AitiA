import logging
import json
import io
from PIL import Image
import pybase64
from mqtt import MQTT
from camera import Camera
from utils import log_execution_time, get_cpu_temperature, RTC


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

    @log_execution_time("Creating the json message")
    def create_message(self, image_array, timestamp):
        try:
            # Convert numpy array to bytes (JPEG)
            image = Image.fromarray(image_array)
            image_bytes = io.BytesIO()
            image.save(image_bytes, format='JPEG', quality=75)
            image_data = image_bytes.getvalue()

            image_base64 = pybase64.b64encode(image_data).decode('utf-8')

            cpu_temp = get_cpu_temperature()

            # timestamp is already an ISO format string, no need to format it
            message = {
                "timestamp": timestamp,
                "image": image_base64,
                "CPU_temperature": cpu_temp
            }

            return json.dumps(message)

        except Exception as e:
            logging.error(f"Problem creating the message: {e}")
            raise

    def resize_image(self, image, max_size=(800, 600)):
        image.thumbnail(max_size, Image.LANCZOS)
        return image

    @log_execution_time("Starting the app")
    def start(self):
        # Start the camera
        self.camera.start()

        # Start the MQTT
        self.mqtt.connect()
        self.mqtt.init_receive()

    @log_execution_time("Taking a picture and sending it")
    def run(self):
        try:
            # Capture the image
            image_raw = self.camera.capture()

            # Get the timestamp
            timestamp = RTC.get_time()

            # Create the message
            message = self.create_message(image_raw, timestamp)

            # Publish the message
            self.mqtt.publish(message)
        except Exception as e:
            logging.error(f"Error in run method: {e}")

    def run_always(self):
        while True:
            self.run()

    # Need RTC API for the implementation
    def run_periodically(self, period):
        return NotImplementedError
