import logging
import json
import re
from mqtt import MQTT
from static_config import CONFIGTOPIC, MINIMUM_WAIT_TIME


class Config:
    def __init__(self, path):
        self.path = path
        self.data = {}  # Empty dictionary to store settings
        try:
            self.load()  # Load the config file and merge with default values
        # If there is an error during loading, publish an error message to the MQTT broker
        except Exception as e:
            logging.error(e)
            mqtt = MQTT()
            mqtt.connect()
            mqtt.publish(f"config-nok|{str(e)}", CONFIGTOPIC)
            mqtt.disconnect()

            # Load the default config
            self.data.update(Config.get_default_config())
            logging.error("Default config loaded")

    def load(self):
        try:
            with open(self.path, "r") as file:
                new_config = json.load(file)

            Config.validate_config(new_config)

            self.data.update(new_config)

        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in the config file: {str(e)}")
            raise
        except FileNotFoundError as e:
            logging.error(f"Config file not found: {self.path} - {str(e)}")
            raise
        except Exception as e:
            logging.error(e)
            raise

    @staticmethod
    def get_default_config():
        # Define the default config here, as a dictionary
        default_config = {
            "quality": "3K",
            "mode": "periodic",
            "period": 15,
            "wakeUpTime": "06:59:31",
            "shutDownTime": "22:00:00"
        }
        return default_config

    @staticmethod
    def validate_config(new_config):
        default_config = Config.get_default_config()

        if not isinstance(new_config, dict):
            raise TypeError("Config loaded from file is not a dictionary.")
        logging.debug(f"New config is dict")
        if default_config.keys() != new_config.keys():
            raise ValueError("Config keys do not match.")
        logging.debug(f"New config keys match")
        if new_config["quality"] not in ["4K", "3K", "HD"]:
            raise ValueError("Invalid quality specified in the config.")
        logging.debug(f"New config quality is valid")
        if new_config["mode"] not in ["periodic", "single-shot", "always-on"]:
            raise ValueError("Invalid mode specified in the config.")
        logging.debug(f"New config mode is valid")
        if new_config["mode"] == "periodic":
            if not isinstance(new_config["period"], int):
                raise TypeError("Period specified in the config is not an integer.")
            if new_config["period"] < MINIMUM_WAIT_TIME:
                raise ValueError("Period specified in the config is less than the minimum allowed wait time.")
        logging.debug(f"New config period is valid")
        # REGEX: hh:mm:ss
        time_pattern = re.compile(r'^(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d$')
        if bool(time_pattern.match(new_config["wakeUpTime"])) is False:
            raise TypeError("Invalid wake-up time format in the config.")
        if bool(time_pattern.match(new_config["shutDownTime"])) is False:
            raise TypeError("Invalid shut-down time format in the config.")
        logging.debug(f"New config times are valid")
