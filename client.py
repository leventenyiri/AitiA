from app import App
from utils import Logger, log_execution_time
from static_config import LOG_CONFIG_PATH, CONFIG_PATH
import logging


@log_execution_time("Application runtime")
def main():
    # Configuring and starting the logging
    logger = Logger(LOG_CONFIG_PATH)
    logger.start()

    # Instantiating the Camera and MQTT objects with the provided configuration file
    app = App(CONFIG_PATH)
    app.start()

    # The app is taking pictures nonstop
    if app.basic_config['mode'] == "always_on":
        app.run_always()
    # The app is sending the images periodically
    elif app.basic_config['mode'] == "periodic":
        app.run_periodically(app.basic_config['period'])
    # The app takes one picture then shuts down
    elif app.basic_config['mode'] == "single-shot":
        app.run()


if __name__ == "__main__":
    # Runs the application
    main()
    logging.info("Application has stopped\n")
