import time
import json
import logging
import logging.config
import yaml
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
log_path = os.path.join(script_dir, 'log_config.yaml')
config_path = os.path.join(script_dir, 'config.json')


class Log:
    def __init__(self, filepath):
        self.path = filepath

    def start(self):
        if not os.path.exists(log_path):
            raise FileNotFoundError(f"Log configuration file not found: {log_path}")
        with open(log_path, 'r') as f:
            config = yaml.safe_load(f)
        logging.config.dictConfig(config)
        logging.info("Start of the log")


class Camera:
    def __init__(self, quality, path):
        self.quality = quality
        self.path = path


class App:
    def __init__(self, config_path):
        # Read the config data to dictionaries
        camera_config = App.read_json_to_dict(config_path, ["Camera"])
        # Pass the config data
        self.camera = Camera(camera_config['quality'], camera_config['path'])

    @staticmethod
    def read_json_to_dict(path, keys):
        try:
            with open(path, 'r') as config:
                data = json.load(config)
            result = {}
            for key in keys:
                if key not in data:
                    msg = f"Key '{key}' not found in the config file"
                    logging.error(msg)
                    raise KeyError(msg)
                result[key] = data[key]
            # Flatten the result dictionary for easier access
            return {k: v for d in result.values() for k, v in d.items()}
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON in the config file: {path}")
            raise ValueError(f"Invalid JSON in the config file: {path}")
        except FileNotFoundError:
            logging.error(f"Config file not found: {path}")
            raise FileNotFoundError(f"Config file not found: {path}")


if __name__ == "__main__":
    log = Log(log_path)
    log.start()
    start_time = time.time()

    app = App(config_path)
