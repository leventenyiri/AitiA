from app import App
from utils import Logger
from static_config import LOG_CONFIG_PATH, CONFIG_PATH
import logging
import sys


def main():
    # Configuring and starting the logging
    logger = Logger(LOG_CONFIG_PATH)
    logger.start()
    logging.info("Application started")

    # Instantiating the Camera and MQTT objects with the provided configuration file
    app = App(CONFIG_PATH)
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
        logging.info(f"Exit code in main: {e.code}")
        app.mqtt.disconnect()
        sys.exit(e.code)


if __name__ == "__main__":
    main()

    logging.info("Application has stopped\n")
