import logging
from .mqtt import MQTT
from .camera import Camera
from .app_config import Config
from .utils import log_execution_time
from .static_config import CONFIGACKTOPIC, MINIMUM_WAIT_TIME
from .schedule import Schedule
from .logger import Logger
from .transmit import Transmit


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
        self.transmit = Transmit(self.camera, self.logger, self.schedule)

    @log_execution_time("Starting the app")
    def start(self) -> None:
        """
        Start the application, initializing the schedule and camera.
        """
        self.schedule.working_time_check(self.config.data["wakeUpTime"], self.config.data["shutDownTime"])
        self.camera.start()

    @log_execution_time("Taking a picture and sending it")
    def run(self) -> None:
        self.transmit.transmit_message()

    def run_always(self) -> None:
        while True:
            self.run()

    def run_periodically(self) -> None:
        """
        Periodically takes pictures and sends them over MQTT, based on the period it will
        either shut down between sending two pictures, or just sleep within the script.
        """
        try:
            while True:
                self.schedule.load_boot_state()
                waiting_time, end_time = self.transmit.transmit_message_with_time_measure()
                waiting_time = max(waiting_time, MINIMUM_WAIT_TIME)

                message = self.schedule.update_boot_time(end_time)
                logging.info(message)
                self.schedule.save_boot_state()

                if self.schedule.should_shutdown(waiting_time):
                    self.schedule.shutdown(waiting_time, end_time)
                elif waiting_time > 0:
                    logging.info(f"Sleeping for {waiting_time} seconds")
                    config_received = self.mqtt.config_received_event.wait(timeout=waiting_time)

                    # If a new configuration was received, update the app's configuration and acknowledge it
                    if config_received:
                        self.config.load()
                        self.acknowledge_config()
        except Exception as e:
            logging.error(f"An error occurred while running the periodic loop: {e}")
            import traceback
            traceback.print_exc()
            exit(1)

    def acknowledge_config(self) -> None:
        """
        Acknowledge the receipt of a new configuration by publishing a confirmation message.
        """
        message = self.mqtt.config_confirm_message
        self.mqtt.publish(message, CONFIGACKTOPIC)
        logging.info("\nConfig received and acknowledged\n")
        self.mqtt.reset_config_received_event()
