from .app import App
from .logger import Logger
from .static_config import LOG_CONFIG_PATH, CONFIG_PATH
import logging
import sys


def main():
    """
    Main entry point for the application.

    This function initializes the logger, creates an instance of the App class,
    and runs the application based on the configured mode.

    The application can run in three modes:
    1. "always-on": Continuously takes pictures and sends them.
    2. "periodic": Sends images periodically based on the configured schedule.
    3. "single-shot": Takes one picture, sends it, and then shuts down the pi.

    The function handles the initialization of logging, creates the App instance
    with the provided configuration, and manages the main execution loop based
    on the selected mode.
    In case of a SystemExit exception, it logs the exit reason, disconnects
    from MQTT, and exits the application with the provided exit code.

    Raises
    ------
    SystemExit
        If the application needs to exit due to an error or completion of its task.

    Notes
    -----
    This function is the entry point of the application when run as a script.
    It sets up all necessary components and manages the main execution flow.
    """

    # Configuring and starting the logging
    logger = Logger(LOG_CONFIG_PATH)
    logger.start_logging()

    # Instantiating the Camera and MQTT objects with the provided configuration file
    app = App(CONFIG_PATH, logger)
    app.start()

    try:
        # The app is taking pictures nonstop
        if app.config.data['mode'] == "always-on":
            app.run_always()
        # The app is sending the images periodically
        elif app.config.data['mode'] == "periodic":
            app.run_periodically()
        # The app takes one picture then shuts down
        elif app.config.data['mode'] == "single-shot":
            app.run()

    except SystemExit as e:
        logging.info(f"Exit code in main: {e.code}\n Exiting the application because: {e}")
        sys.exit(e.code)
    finally:
        app.mqtt.disconnect()
        logger.disconnect_mqtt()


if __name__ == "__main__":
    main()
