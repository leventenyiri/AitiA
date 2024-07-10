from app import App
from utils import Logger, log_execution_time
from config import LOG_CONFIG_PATH, CONFIG_PATH
import logging


@log_execution_time("Application runtime")
def main():
    logger = Logger(LOG_CONFIG_PATH)
    logger.start()

    app = App(CONFIG_PATH)
    app.start()

    try:
        # The app is taking pictures nonstop
        if app.basic_config['mode'] == "always_on":
            app.run_always()
        # The app is sending the images periodically and shuts down in between
        elif app.basic_config['mode'] == "periodic":
            app.run_periodically(app.basic_config['period'])
        # The app takes one picture then shuts down
        elif app.basic_config['mode'] == "single-shot":
            app.run()

    finally:
        app.mqtt.disconnect()


if __name__ == "__main__":

    main()
    logging.info("Aplication has stopped\n")

    # Run for 60 seconds
    # TODO get the run time from config
    # app.run_old(duration=60)
