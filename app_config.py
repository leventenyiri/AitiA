import logging
import json
from mqtt import MQTT
from static_config import CONFIGTOPIC


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
            self.data.update(self.get_default_config())
            logging.error("Default config loaded")

    def load(self):
        default_config = self.get_default_config()
        try:
            with open(self.path, "r") as file:
                new_config = json.load(file)

            if not isinstance(new_config, dict):
                raise TypeError("Config loaded from file is not a dictionary.")

            # Check if the loaded config is valid
            if default_config.keys() != new_config.keys():
                raise ValueError("Config keys do not match the default config keys.")

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

    def get_default_config(self):
        # Define the default config here, as a dictionary
        default_config = {
            "quality": "3K",
            "mode": "periodic",
            "period": 15,
            "wakeUpTime": "06:59:31",
            "shutDownTime": "22:00:00"
        }
        return default_config
