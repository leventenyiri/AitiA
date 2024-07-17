import logging
import json
import io
from PIL import Image
import pybase64
from datetime import datetime, timedelta
from mqtt import MQTT
from camera import Camera
from utils import log_execution_time, get_cpu_temperature, RTC, System


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

    def working_time_check(self):
        wake_up_time = datetime.strptime(self.basic_config["wake_up_time"], "%H:%M:%S").time()
        shut_down_time = datetime.strptime(self.basic_config["shut_down_time"], "%H:%M:%S").time()

        utc_time = datetime.fromisoformat(RTC.get_time())

        # Add two hours, because the RTC is in UTC, and Budapest is two hours ahead
        adjusted_time = utc_time + timedelta(hours=2)

        current_time = adjusted_time.time()

        logging.info("working_time_check called \n")
        logging.info(
            f"wake up time is : {wake_up_time}, shutdown time is : {shut_down_time}, current time is : {current_time}")
        logging.info(f"If true it can compare correctly : {current_time >= shut_down_time}")

        # If e.g: wake up time = 6:00:00 and shutdown time = 20:00:00
        if (wake_up_time < shut_down_time) and (wake_up_time > current_time or current_time >= shut_down_time):
            logging.info("Starting shutdown")
            System.shutdown()

        # If e.g: wake up time = 20:00:00 and shutdown time = 6:00:00
        elif (current_time >= shut_down_time and current_time < wake_up_time):
            logging.info("Starting shutdown")
            System.shutdown()

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
        self.working_time_check()
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
