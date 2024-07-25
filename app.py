import logging
import json
import io
from PIL import Image
import pybase64
from datetime import datetime, timedelta
from mqtt import MQTT
from camera import Camera
from system import System, RTC
from utils import log_execution_time
import time
import sys


def deep_merge(default, update):
    """
    Recursively merge two dictionaries, preferring values from 'update',
    but only for keys that exist in 'default'.

    Parameters:
    default (dict): The default dictionary to merge with 'update'.
    update (dict): The dictionary to merge into 'default'.

    Returns:
    dict: The merged dictionary.
    """
    result = default.copy()
    # Finding common keys
    common_keys = set(default.keys()) & set(update.keys())
    # Iterate through common keys and merge nested dictionaries recursively
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
                "period": 50,
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
        """
        Checks if the current time is within the operational hours defined in the configuration.
        If the current time is outside the operational hours, the system will initiate a shutdown.
        The time is in UTC timezone.
        """
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
            battery_info = System.get_battery_info()
            logging.info(
                f"Battery temperature: {battery_info['temperature']}°C, battery percentage: {battery_info['percentage']}%")
            # timestamp is already an ISO format string, no need to format it
            message = {
                "timestamp": timestamp,
                "image": self.create_base64_image(image_array),
                "CPU_temperature": System.get_cpu_temperature(),
                "battery_temperature": battery_info["temperature"],
                "battery_percentage": battery_info["percentage"]
            }

            return json.dumps(message)

        except Exception as e:
            logging.error(f"Problem creating the message: {e}")
            raise

    def create_base64_image(self, image_array):
        """
        Converts a numpy array representing an image into a base64-encoded JPEG string.

        Parameters:
        image_array: The image data as a numpy array.

        Returns:
        str: The base64-encoded string representation of the JPEG image.
        """

        image = Image.fromarray(image_array)
        image_bytes = io.BytesIO()
        image.save(image_bytes, format='JPEG')
        image_data = image_bytes.getvalue()

        return pybase64.b64encode(image_data).decode('utf-8')

    @log_execution_time("Starting the app")
    def start(self):
        # Checks if the current time is within the operational hours
        self.working_time_check()
        self.camera.start()

    def connect_mqtt(self):
        # Start the MQTT
        self.mqtt.connect()
        self.mqtt.init_receive()

    def get_message(self):
        image_raw = self.camera.capture()
        timestamp = RTC.get_time()
        message = self.create_message(image_raw, timestamp)
        return message

    @log_execution_time("Taking a picture and sending it")
    def run(self):
        try:
            # Capturing the image, getting timestamp, creating message as soon as possible, while network is booting
            message = self.get_message()

            # If we are not connected to the broker, connect to it in a blocking fashion
            if not self.mqtt.client.is_connected():
                self.connect_mqtt()

            self.mqtt.publish(message)

        except Exception as e:
            logging.error(f"Error in run method: {e}")
            raise

    def run_always(self):
        while True:
            self.run()

    def run_periodically(self, period):

        remaining_time = self.run_with_time_measure(period)

        if remaining_time > 60:  # If more than a minutes left
            # Calculate wake-up time

            raise NotImplemented

            wake_time = datetime.now() + timedelta(seconds=remaining_time - 15)  # Takes about 15sec to boot

            # Schedule wake-up
            System.schedule_wakeup(wake_time)

            logging.info(f"Scheduling wake-up for {wake_time}")
            sys.exit(2)
        # Not working yet
        while remaining_time <= 60:
            """  if self.mqtt.is_config_changed():
                logging.info("Config has changed. Restarting script...")
                sys.exit(1) """

            logging.info(f"Sleeping for {remaining_time} seconds")
            time.sleep(remaining_time)

            self.run()

    def run_with_time_measure(self, period):
        start_time = time.time()
        self.run()
        elapsed_time = time.time() - start_time
        return (period - elapsed_time)
