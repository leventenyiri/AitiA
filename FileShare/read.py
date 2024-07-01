import time
import json
import logging

config_path = 'config.json'

class Log:
    def __init__(self, filepath, level):
        self.path = filepath
        self.level = level
        
    def start(self):
        # Configure costum logging
        
        file_handler = logging.FileHandler(self.path)
        log.addHandler(file_handler)
        log.setLevel(self.level)
        logging.info("Costum logging rules have been added")

class Camera:
    def __init__(self, quality, path):
        self.quality = quality
        self.path = path

class App:
    def __init__(self, config_path):
        # Read the config data to dictionaries
        camera_config = App.read_json_to_dict(config_path, ["Camera"])
        logging_config = App.read_json_to_dict(config_path, ["Log"])
        
        # Pass the config data 
        self.log = Log(logging_config["path"], logging_config["level"])
        self.camera = Camera(camera_config['quality'], camera_config['path'])
        
    @staticmethod
    def read_json_to_dict(path, keys):
        try:
            with open(path, 'r') as config:
                data = json.load(config)
            result = {}
            for key in keys:
                if key not in data:
                    logging.error(f"Key '{key}' not found in the config file")
                    raise KeyError(f"Key '{key}' not found in the config file")
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
    # Start the log
    logging.basicConfig(level=logging.DEBUG, filemode='w',
                            format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    log = logging.getLogger(__name__)
    logging.info("Start of the log")
    start_time = time.time()
    
    app = App(config_path)
    app.log.start()
