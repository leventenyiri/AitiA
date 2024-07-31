import logging
import json


class Config:
    def __init__(self, path):
        self.path = path
        self.data = {}  # Empty dictionary to store settings
        self.load()  # Load the config file and merge with default values

    def load(self):
        # Define default values
        default_config = {
            "quality": "3K",
            "mode": "single-shot",
            "period": 50,
            "wake_up_time": "06:59:31",
            "shut_down_time": "22:00:00"
        }

        try:
            with open(self.path, "r") as file:
                new_config = json.load(file)
            # Use a deep merge function to combine loaded data with defaults
            self.data = Config.deep_merge(default_config, new_config)

        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in the config file: {self.path} - {str(e)}")
            exit(1)
        except FileNotFoundError as e:
            logging.error(f"Config file not found: {self.path} - {str(e)}")
            exit(1)
        except Exception as e:
            logging.error(f"Unexpected error loading config: {e}")
            exit(1)

    def deep_merge(default, update):
        """
        Recursively merge two dictionaries, preferring values from 'update',
        but only for keys that exist in 'default'.

        Parameters:
        default (dict): The default dictionary to merge with 'update'.
        update (dict): The dictionary to merge into 'default'.

        Returns:
        dict: The merged dictionary.
        """
        result = default.copy()
        # Finding common keys
        common_keys = set(default.keys()) & set(update.keys())
        # Iterate through common keys and merge nested dictionaries recursively
        for key in common_keys:
            if all(isinstance(d.get(key), dict) for d in (default, update)):
                result[key] = Config.deep_merge(default[key], update[key])
            else:
                result[key] = update[key]

        return result
