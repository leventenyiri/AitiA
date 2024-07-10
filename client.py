import os
import logging
import logging.config
import yaml
from app import App
from config import LOG_CONFIG_PATH, CONFIG_PATH


class Logger:
    def __init__(self, filepath):
        self.filepath = filepath

    def start(self):
        try:
            if not os.path.exists(self.filepath):
                raise FileNotFoundError(f"Log configuration file not found: {self.filepath}")
            with open(self.filepath, 'r') as f:
                config = yaml.safe_load(f)
            logging.config.dictConfig(config)
            logging.info("Logging started")
        except Exception as e:
            logging.error(e)
            exit(1)


if __name__ == "__main__":

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

    print("Image capture and publish sequence completed")
    # Run for 60 seconds
    # TODO get the run time from config
    # app.run_old(duration=60)
