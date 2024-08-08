import logging
import json
import io
import threading
from typing import Dict, Any, Tuple
from PIL import Image
import pybase64
from datetime import datetime
import numpy as np
from .mqtt import MQTT
from .camera import Camera
from .app_config import Config
from .system import System, RTC
from .utils import log_execution_time
from .static_config import MINIMUM_WAIT_TIME, IMAGETOPIC, CONFIGACKTOPIC
from .schedule import Schedule
from .logger import Logger


class App:
    """
    Main application class for managing camera operations and MQTT communication.

    This class handles image capture, message creation, and periodic execution of
    tasks based on the provided configuration.

    Parameters
    ----------
    config_path : str
        Path to the configuration file.
    logger : Logger
        Logger instance for handling log messages.

    Attributes
    ----------
    config : Config
        Configuration object containing application settings.
    camera : Camera
        Camera object for capturing images.
    mqtt : MQTT
        MQTT client for message publishing.
    schedule : Schedule
        Schedule object for managing periodic tasks.
    logger : Logger
        Logger instance for handling log messages.
    lock : threading.Lock
        Lock for thread-safe operations.
    """

    def __init__(self, config_path: str, logger: Logger) -> None:
        """
        Initialize the App with configuration and logger.

        Parameters
        ----------
        config_path : str
            Path to the configuration file.
        logger : Logger
            Logger instance for handling log messages.
        """
        self.config = Config(config_path)
        self.camera = Camera(self.config.data)
        self.mqtt = MQTT()
        self.schedule = Schedule(period=self.config.data["period"])
        self.logger = logger
        self.lock = threading.Lock()

    def log_hardware_info(self, hardware_info: Dict[str, Any]) -> None:
        """
        Logs the hardware information to a file.

        Parameters
        ----------
        hardware_info (Dict[str, Any])

        """
        log_entry = ", ".join(f"{k}={v}" for k, v in hardware_info.items())
        with open("hardware_log.txt", "a") as log_file:
            log_file.write(f"{log_entry}\n")

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
            hardware_info: Dict[str, Any] = System.gather_hardware_info()
            logging.info(
                f"Battery temp: {battery_info['temperature']}°C, battery percentage: {battery_info['percentage']} %")
            message: Dict[str, Any] = {
                "timestamp": timestamp,
                "image": self.create_base64_image(image_array),
                "cpuTemp": System.get_cpu_temperature(),
                "batteryTemp": battery_info["temperature"],
                "batteryCharge": battery_info["percentage"]
            }

            # Log hardware info to a file for further analysis
            if hardware_info:
                self.log_hardware_info(hardware_info)

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
        """
        Start the application, initializing the schedule and camera.
        """
        self.schedule.working_time_check(self.config.data["wakeUpTime"], self.config.data["shutDownTime"])
        self.camera.start()

    def connect_mqtt(self) -> None:
        """
        Connect to the MQTT broker and initialize message receiving.
        """
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
            if self.logger.mqtt is None:
                self.logger.start_mqtt_logging()

            self.mqtt.publish(message, IMAGETOPIC)

        except Exception as e:
            logging.error(f"Error in run method: {e}")
            raise

    def run_always(self) -> None:
        while True:
            self.run()

    def acknowledge_config(self) -> None:
        """
        Acknowledge the receipt of a new configuration by publishing a confirmation message.
        """
        with self.lock:
            message: str = self.mqtt.config_confirm_message
        self.mqtt.publish(message, CONFIGACKTOPIC)
        logging.info("\nConfig received and acknowledged\n")
        self.mqtt.reset_config_received_event()

    def run_with_time_measure(self) -> Tuple[float, datetime]:
        """
        Run the image capture and send process, measuring the execution time.

        Returns
        -------
        Tuple[float, datetime]
            A tuple containing the waiting time until the next execution and the end time.
        """
        try:
            start_time: str = RTC.get_time()
            self.run()
            end_time: str = RTC.get_time()
            elapsed_time: float = (datetime.fromisoformat(end_time) -
                                   datetime.fromisoformat(start_time)).total_seconds()
            waiting_time: float = self.config.data["period"] - elapsed_time
        except Exception as e:
            logging.error(f"Error in run_with_time_measure method: {e}")
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
