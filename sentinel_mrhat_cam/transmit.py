import logging
import json
import io
from typing import Dict, Any, Tuple
from PIL import Image
import pybase64
from datetime import datetime
import numpy as np
from .utils import log_execution_time
from .static_config import IMAGETOPIC, MINIMUM_WAIT_TIME
from .system import System, RTC
from .camera import Camera
from .mqtt import MQTT
from .schedule import Schedule
from .logger import Logger


class Transmit:
    def __init__(self, camera: Camera, logger: Logger, schedule: Schedule, mqtt: MQTT) -> None:
        self.camera = camera
        self.logger = logger
        self.schedule = schedule
        self.mqtt = mqtt

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
        # If there was an error during image capture, return an error message
        if image_array is None:
            return "Error: Image data is None"

        image: Image.Image = Image.fromarray(image_array)
        image_bytes: io.BytesIO = io.BytesIO()
        image.save(image_bytes, format="JPEG")
        image_data: bytes = image_bytes.getvalue()

        return pybase64.b64encode(image_data).decode("utf-8")

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
            battery_info: Dict[str, Any] = System.get_battery_info()
            hardware_info: Dict[str, Any] = System.gather_hardware_info()
            cpu_temp: float = System.get_cpu_temperature()

            logging.info(
                f"Battery temp: {battery_info['temperature']}°C, battery percentage: {battery_info['percentage']} %, CPU temp: {cpu_temp}°C")
            message: Dict[str, Any] = {
                "timestamp": timestamp,
                "image": self.create_base64_image(image_array),
                "cpuTemp": cpu_temp,
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
    def transmit_message(self) -> None:
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

    def transmit_message_with_time_measure(self) -> Tuple[float, datetime]:
        """
        Run the image capture and send process, measuring the execution time.

        Returns
        -------
        Tuple[float, datetime]
            A tuple containing the waiting time until the next execution and the end time.
        """
        try:
            start_time: str = RTC.get_time()
            self.transmit_message()
            end_time: str = RTC.get_time()
            elapsed_time: float = (datetime.fromisoformat(end_time) -
                                   datetime.fromisoformat(start_time)).total_seconds()
            waiting_time: float = self.schedule.period - elapsed_time
        except Exception as e:
            logging.error(f"Error in run_with_time_measure method: {e}")
        return max(waiting_time, MINIMUM_WAIT_TIME), datetime.fromisoformat(end_time)
