import logging
import json
import io
import threading
from typing import Dict, Any, Tuple
from PIL import Image
import pybase64
from datetime import datetime, time
import numpy as np
from AitiA.mqtt import MQTT
from AitiA.camera import Camera
from AitiA.app_config import Config
from AitiA.system import System, RTC
from AitiA.utils import log_execution_time
from AitiA.static_config import MINIMUM_WAIT_TIME, IMAGETOPIC, CONFIGTOPIC
from AitiA.schedule import Schedule


class App:
    def __init__(self, config_path: str) -> None:
        self.config = Config(config_path)
        self.camera = Camera(self.config.data)
        self.mqtt = MQTT()
        self.schedule = Schedule(period=self.config.data["period"])
        self.lock = threading.Lock()

    def working_time_check(self) -> None:
        """
        Checks if the current time is within the operational hours defined in the configuration.

        If the current time is outside the operational hours, the system will initiate a shutdown.
        The time is in UTC timezone.
        """
        wake_up_time: time = datetime.strptime(
            self.config.data["wakeUpTime"], "%H:%M:%S"
        ).time()
        shut_down_time: time = datetime.strptime(
            self.config.data["shutDownTime"], "%H:%M:%S"
        ).time()

        utc_time: datetime = datetime.fromisoformat(RTC.get_time())
        current_time: time = utc_time.time()

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
    def create_message(self, image_array: np.ndarray, timestamp: str) -> str:
        """
        Creates a JSON message containing image data, timestamp, CPU temperature, battery temperature,
        and battery charge percentage.

        Parameters
        ----------
        image_array : numpy.ndarray
            The image data as a numpy array.
        timestamp : str
            The timestamp in ISO 8601 format.

        Returns
        -------
        str
            A JSON string containing the image data and system information.

        Raises
        ------
        Exception
            If an error occurs during the creation of the message.
        """
        try:
            battery_info: Dict[str, float] = System.get_battery_info()
            logging.info(
                f"Battery temp: {battery_info['temperature']}°C, battery percentage: {battery_info['percentage']} %")
            message: Dict[str, Any] = {
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

    def create_base64_image(self, image_array: np.ndarray) -> str:
        """
        Converts a numpy array representing an image into a base64-encoded JPEG string.

        Parameters
        ----------
        image_array : numpy.ndarray
            The image data as a numpy array.

        Returns
        -------
        str
            The base64-encoded string representation of the JPEG image.
        """

        image: Image.Image = Image.fromarray(image_array)
        image_bytes: io.BytesIO = io.BytesIO()
        image.save(image_bytes, format="JPEG")
        image_data: bytes = image_bytes.getvalue()

        return pybase64.b64encode(image_data).decode("utf-8")

    @log_execution_time("Starting the app")
    def start(self) -> None:
        self.working_time_check()
        self.camera.start()

    def connect_mqtt(self) -> None:
        self.mqtt.connect()
        self.mqtt.init_receive()

    def get_message(self) -> str:
        """
        Captures an image using the camera, retrieves the current timestamp, and creates a JSON message containing
        the image data and system information.

        Returns
        -------
        str
            A JSON string containing the image data, timestamp, CPU temperature, battery temperature,
            and battery charge percentage.
        """
        image_raw: np.ndarray = self.camera.capture()
        timestamp: str = RTC.get_time()
        message: str = self.create_message(image_raw, timestamp)
        return message

    @log_execution_time("Taking a picture and sending it")
    def run(self) -> None:
        """
        Captures an image, creates a message with the image data, timestamp, CPU temperature,
        battery temperature, and battery charge percentage, and sends it over MQTT.

        If the MQTT client is not connected, it will attempt to connect in a blocking way.

        Raises
        ------
        Exception
            If an error occurs during the execution of the function.
        """
        try:
            message: str = self.get_message()

            if not self.mqtt.client.is_connected():
                self.connect_mqtt()

            self.mqtt.publish(message, IMAGETOPIC)

        except Exception as e:
            logging.error(f"Error in run method: {e}")
            raise

    def run_always(self) -> None:
        while True:
            self.run()

    def acknowledge_config(self) -> None:
        self.lock.acquire()
        message: str = self.mqtt.config_confirm_message
        self.lock.release()
        self.mqtt.publish(message, CONFIGTOPIC)
        logging.info("\nConfig received and acknowledged\n")
        self.mqtt.reset_config_received_event()

    def run_with_time_measure(self) -> Tuple[float, datetime]:
        start_time: str = RTC.get_time()
        self.run()
        end_time: str = RTC.get_time()
        elapsed_time: float = (datetime.fromisoformat(end_time) - datetime.fromisoformat(start_time)).total_seconds()
        waiting_time: float = self.config.data["period"] - elapsed_time
        return max(waiting_time, 0), datetime.fromisoformat(end_time)

    def run_periodically(self) -> None:
        """
        Periodically takes pictures and sends them over MQTT, based on the period it will
        either shut down between sending two pictures, or just sleep within the script.
        """
        while True:
            self.schedule.load_boot_state()
            waiting_time: float
            end_time: datetime
            waiting_time, end_time = self.run_with_time_measure()
            waiting_time = max(waiting_time, MINIMUM_WAIT_TIME)

            message: str = self.schedule.update_boot_time(end_time)
            logging.info(message)
            self.schedule.save_boot_state()

            if self.schedule.should_shutdown(waiting_time):
                shutdown_duration: float = self.schedule.calculate_shutdown_duration(waiting_time)
                wake_time: datetime = self.schedule.get_wake_time(end_time, shutdown_duration)

                logging.info(f"Shutting down for {shutdown_duration} seconds")

                try:
                    System.schedule_wakeup(wake_time)
                    self.schedule.last_shutdown_time = end_time.isoformat()
                    self.schedule.save_boot_state()
                    System.shutdown()
                except Exception as e:
                    logging.error(f"Failed to schedule wake-up: {e}")

            elif waiting_time > 0:
                logging.info(f"Sleeping for {waiting_time} seconds")
                config_received: bool = self.mqtt.config_received_event.wait(timeout=waiting_time)
                if config_received:
                    self.config.load()
                    self.acknowledge_config()
                    continue

            else:
                logging.warning(f"Period time is set too low. The minimum is {MINIMUM_WAIT_TIME} seconds.")
