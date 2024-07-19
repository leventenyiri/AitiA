import logging
import json
import io
from PIL import Image
import pybase64
from datetime import datetime, timedelta
from mqtt import MQTT
from camera import Camera
from utils import log_execution_time, get_cpu_temperature, RTC, System
import time
import sys


def deep_merge(default, update):
    """
    Recursively merge two dictionaries, preferring values from 'update',
    but only for keys that exist in 'default'.
    """
    result = default.copy()

    common_keys = set(default.keys()) & set(update.keys())

    for key in common_keys:
        if all(isinstance(d.get(key), dict) for d in (default, update)):
            result[key] = deep_merge(default[key], update[key])
        else:
            result[key] = update[key]

    return result


class App:
    def __init__(self, config_path):
        self.camera_config, self.basic_config = self.load_config(config_path)
        self.camera = Camera(self.camera_config, self.basic_config)
        self.mqtt = MQTT()

    @staticmethod
    def load_config(path):
        # Define default values
        default_config = {
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

        try:
            with open(path, 'r') as file:
                data = json.load(file)

            # Use a deep merge function to combine loaded data with defaults
            camera_config = deep_merge(default_config['Camera'], data.get('Camera', {}))
            basic_config = deep_merge(default_config['Basic'], data.get('Basic', {}))

            return camera_config, basic_config

        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in the config file: {path} - {str(e)}")
            exit(1)
        except FileNotFoundError as e:
            logging.error(f"Config file not found: {path} - {str(e)}")
            exit(1)
        except Exception as e:
            logging.error(f"Unexpected error loading config: {e}")
            exit(1)

    def working_time_check(self):
        wake_up_time = datetime.strptime(self.basic_config["wake_up_time"], "%H:%M:%S").time()
        shut_down_time = datetime.strptime(self.basic_config["shut_down_time"], "%H:%M:%S").time()

        utc_time = datetime.fromisoformat(RTC.get_time())
        current_time = utc_time.time()

        logging.info(
            f"wake up time is : {wake_up_time}, shutdown time is : {shut_down_time}, current time is : {current_time}")

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
            raise

    def run_always(self):
        while True:
            self.run()

    # Need RTC API for the implementation
    def run_periodically(self, period):
        start_time = time.time()
        self.run()

        elapsed_time = time.time() - start_time
        remaining_time = period - elapsed_time

        if remaining_time > 120:  # If more than 2 minutes left
            # Calculate wake-up time
            wake_time = datetime.now() + timedelta(seconds=remaining_time - 60)  # Wake up 1 minute early

            # Schedule wake-up
            System.schedule_wakeup(wake_time)

            logging.info(f"Scheduling wake-up for {wake_time}")
            sys.exit(2)
        else:
            logging.info(f"Sleeping for {remaining_time} seconds")
            time.sleep(remaining_time)
