import logging
import json
import io
from PIL import Image
import pybase64
from datetime import datetime, timedelta
from mqtt import MQTT
from camera import Camera
from app_config import Config
from system import System, RTC
from utils import log_execution_time
from static_config import SHUTDOWN_THRESHOLD
import time
import sys
import os


class App:
    def __init__(self, config_path):
        self.config = Config(config_path)
        self.camera = Camera(self.config.data)
        self.mqtt = MQTT()
        self.state_file = "state_file.json"  # Choose an appropriate path
        self.load_boot_state()
        self.max_boot_time = 10800  # 3 hours

    def working_time_check(self):
        """
        Checks if the current time is within the operational hours defined in the configuration.
        If the current time is outside the operational hours, the system will initiate a shutdown.
        The time is in UTC timezone.
        """
        wake_up_time = datetime.strptime(
            self.config.data["wake_up_time"], "%H:%M:%S"
        ).time()
        shut_down_time = datetime.strptime(
            self.config.data["shut_down_time"], "%H:%M:%S"
        ).time()

        utc_time = datetime.fromisoformat(RTC.get_time())
        current_time = utc_time.time()

        logging.info(
            f"wake up time is : {wake_up_time}, shutdown time is : {shut_down_time}, current time is : {current_time}"
        )

        # If e.g: wake up time = 6:00:00 and shutdown time = 20:00:00
        if (wake_up_time < shut_down_time) and (
            wake_up_time > current_time or current_time >= shut_down_time
        ):
            logging.info("Starting shutdown")
            System.shutdown()

        # If e.g: wake up time = 20:00:00 and shutdown time = 6:00:00
        elif current_time >= shut_down_time and current_time < wake_up_time:
            logging.info("Starting shutdown")
            System.shutdown()

    @log_execution_time("Creating the json message")
    def create_message(self, image_array, timestamp):
        try:
            battery_info = System.get_battery_info()
            logging.info(
                f"Battery temp: {battery_info['temperature']}°C, battery percentage: {battery_info['percentage']} %"
            )
            # timestamp is already an ISO format string, no need to format it
            message = {
                "timestamp": timestamp,
                "image": self.create_base64_image(image_array),
                "cpuTemp": System.get_cpu_temperature(),
                "batteryTemp": battery_info["temperature"],
                "batteryCharge": battery_info["percentage"]
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
        image.save(image_bytes, format="JPEG")
        image_data = image_bytes.getvalue()

        return pybase64.b64encode(image_data).decode("utf-8")

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

    def load_boot_state(self):
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            self.boot_shutdown_time = state.get('boot_shutdown_time')
            self.last_shutdown_time = state.get('last_shutdown_time')
        else:
            self.boot_shutdown_time = None
            self.last_shutdown_time = None

    def save_boot_state(self):
        state = {
            'boot_shutdown_time': self.boot_shutdown_time,
            'last_shutdown_time': self.last_shutdown_time,
        }
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f)
        except IOError as e:
            logging.error(f"Failed to save state file: {e}")

    def run_periodically(self, period):
        while True:
            waiting_time = self.run_with_time_measure(period)

            current_time = datetime.fromisoformat(RTC.get_time())

            # Dont reboot if we cant shut down, only sleep
            if self.last_shutdown_time is None:
                self.last_shutdown_time = current_time.isoformat()
                self.save_boot_state()
                logging.info("First run or state file was reset. Will measure boot time on next cycle.")
                System.reboot()

            if self.last_shutdown_time is not None:
                last_shutdown = datetime.fromisoformat(self.last_shutdown_time)
                boot_time = (current_time - last_shutdown).total_seconds()

                if boot_time <= self.max_boot_time:
                    self.boot_shutdown_time = boot_time
                    logging.info(f"Measured boot and shutdown time: {self.boot_shutdown_time} seconds")
                else:
                    logging.info(f"Long shutdown detected (duration: {boot_time} seconds). Not updating boot time.")

            if waiting_time > SHUTDOWN_THRESHOLD:
                shutdown_duration = waiting_time
                shutdown_duration -= self.boot_shutdown_time

                if shutdown_duration > 0:
                    wake_time = current_time + timedelta(seconds=shutdown_duration)

                    logging.info(f"Shutting down for {shutdown_duration} seconds")
                    logging.info(f"Scheduling wake-up for {wake_time}")

                    System.schedule_wakeup(wake_time)
                    self.last_shutdown_time = current_time.isoformat()
                    self.save_boot_state()
                    System.shutdown()
                else:
                    logging.info(f"Sleeping for {waiting_time} seconds")
                    time.sleep(waiting_time)
            elif waiting_time > 0:
                if self.mqtt.is_config_changed():
                    logging.info("Config has changed. Restarting script...")
                    sys.exit(1)

                logging.info(f"Sleeping for {waiting_time} seconds")
                time.sleep(waiting_time)
            else:
                logging.warning(f"Period time is set too low. Increase it by {abs(waiting_time)} seconds.")

            self.save_boot_state()

    def run_with_time_measure(self, period):
        start_time = RTC.get_time()
        self.run()
        end_time = RTC.get_time()
        # Some transformation is necessary because of the way we are getting the time from the RTC
        elapsed_time = (datetime.fromisoformat(end_time) - datetime.fromisoformat(start_time)).total_seconds()
        waiting_time = period - elapsed_time
        return max(waiting_time, 0)  # Ensure we don't return negative time
