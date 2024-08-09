import logging
from typing import Tuple
from datetime import datetime
from .mqtt import MQTT
from .camera import Camera
from .app_config import Config
from .utils import log_execution_time
from .static_config import CONFIGACKTOPIC, CONFIG_PATH
from .schedule import Schedule
from .logger import Logger
from .transmit import Transmit
import threading


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
        self.transmit = Transmit()

    @log_execution_time("Starting the app")
    def start(self) -> None:
        """
        Start the application, initializing the schedule and camera.
        """

        self.transmit = Transmit(self.camera, self.logger, self.schedule)
        self.schedule.working_time_check(self.config.data["wakeUpTime"], self.config.data["shutDownTime"])
        self.camera.start()

    @log_execution_time("Taking a picture and sending it")
    def run(self) -> None:
        self.transmit.transmit_message()

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
        self.transmit.transmit_message_with_time_measure()

    def run_periodically(self) -> None:
        self.transmit.transmit_message_periodically()
