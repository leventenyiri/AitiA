import logging
import json
import io
from PIL import Image
import pybase64
from datetime import datetime
from mqtt import MQTT
from camera import Camera
from app_config import Config
from system import System, RTC
from utils import log_execution_time
from static_config import SHUTDOWN_THRESHOLD
import time
import sys
from schedule import Schedule


class App:
    def __init__(self, config_path):
        self.config = Config(config_path)
        self.camera = Camera(self.config.data)
        self.mqtt = MQTT()
        self.schedule = Schedule(
            state_file="state_file.json",
            period=self.config.data["period"],
            max_boot_time=10800,  # 3 hours
            shutdown_threshold=SHUTDOWN_THRESHOLD
        )

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

    def run_with_time_measure(self):
        start_time = RTC.get_time()
        self.run()
        end_time = RTC.get_time()
        # Some transformation is necessary because of the way we are getting the time from the RTC
        elapsed_time = (datetime.fromisoformat(end_time) - datetime.fromisoformat(start_time)).total_seconds()
        waiting_time = self.config.data["period"] - elapsed_time
        return max(waiting_time, 0), datetime.fromisoformat(end_time)  # Ensure we don't return negative time

    def run_periodically(self):
        while True:
            logging.info(f"Entered run_periodically")
            waiting_time, end_time = self.run_with_time_measure()
            logging.info(f"Survived run_with_time_measure")

            should_reboot, message = self.schedule.update_boot_time(end_time)
            logging.info(message)
            if should_reboot:
                self.schedule.save_boot_state()
                System.reboot()

            if self.schedule.should_shutdown(waiting_time):
                shutdown_duration = self.schedule.calculate_shutdown_duration(waiting_time)
                wake_time = self.schedule.get_wake_time(end_time, shutdown_duration)

                logging.info(f"Shutting down for {shutdown_duration} seconds")
                logging.info(f"Scheduling wake-up for {wake_time}")

                System.schedule_wakeup(wake_time)
                self.schedule.last_shutdown_time = end_time.isoformat()
                self.schedule.save_boot_state()
                System.shutdown()

            elif waiting_time > 0:
                if self.mqtt.is_config_changed():
                    logging.info("Config has changed. Restarting script...")
                    sys.exit(1)

                logging.info(f"Sleeping for {waiting_time} seconds")
                time.sleep(waiting_time)
            else:
                logging.warning(f"Period time is set too low. Increase it by {abs(waiting_time)} seconds.")
