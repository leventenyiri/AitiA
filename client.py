import os
import time
import json
import logging
import logging.config
import yaml
from subprocess import CalledProcessError
try:
    from picamera2 import Picamera2
except ImportError:
    Picamera2 = None

# ----------------- Config file data ------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_CONFIG_PATH = os.path.join(SCRIPT_DIR, 'log_config.yaml')
CONFIG_PATH = os.path.join(SCRIPT_DIR, 'config.json')
# ------------------------------------------------------

class Logger:
    def __init__(self, filepath):
        self.filepath = filepath

    def start(self):
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"Log configuration file not found: {self.filepath}")
        with open(self.filepath, 'r') as f:
            config = yaml.safe_load(f)
        logging.config.dictConfig(config)
        logging.info("Logging started")

class Camera:
    def __init__(self, config):
        self.quality = config['quality']
        self.save_path = config['path']
        self.gain = config['gain']
        self.exposure = config['exposure']
        self.width = config['width']
        self.height = config['height']
        self.contrast = config['contrast']
        self.cam = Picamera2()

    def start(self):
        config = self.cam.create_still_configuration({"size": (self.width, self.height)})
        self.cam.configure(config)
        self.cam.options['quality'] = self.quality
        self.cam.set_controls({"ExposureTime": self.exposure, "AnalogueGain": self.gain, "Contrast": self.contrast})
        self.cam.start(show_preview=False)

    def capture(self):
        self.cam.capture_file(self.save_path)

class App:
    def __init__(self, config_path):
        self.camera_config = self._load_camera_config(config_path)
        self.camera = Camera(self.camera_config)

    @staticmethod
    def _load_camera_config(path):
        try:
            with open(path, 'r') as file:
                data = json.load(file)
            camera_config = data.get('Camera')
            if camera_config is None:
                raise KeyError("Key 'Camera' not found in the config file")
            return camera_config
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in the config file: {path} - {str(e)}")
            raise
        except FileNotFoundError as e:
            logging.error(f"Config file not found: {path} - {str(e)}")
            raise

if __name__ == "__main__":
    start_time = time.time()
    
    logger = Logger(LOG_CONFIG_PATH)
    logger.start()
    
    app = App(CONFIG_PATH)
    app.camera.start()
    app.camera.capture()
    
    logging.info(f"Image saving time: {time.time() - start_time} seconds")
    print("Image saved")
