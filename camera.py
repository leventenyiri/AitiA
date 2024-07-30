from unittest.mock import MagicMock
try:
    from libcamera import controls
    from picamera2 import Picamera2
except ImportError:
    Picamera2 = MagicMock()
    controls = MagicMock()
from utils import log_execution_time
import logging


class Camera:
    def __init__(self, config):
        # The best quality is set as default
        self.quality = 95
        self.cam = Picamera2()

        # Set the premade settings
        if config['quality'] == "4K":
            self.width = 3840
            self.height = 2160
        elif config['quality'] == "3K":
            self.width = 2560
            self.height = 1440
        elif config['quality'] == "HD":
            self.width = 1920
            self.height = 1080
        # If the specified quality is not found, default to 3K quality
        else:
            self.width = 2560
            self.height = 1440
            logging.error(f"Invalid quality specified: {config['quality']}. Defaulting to 3K quality.")

    def start(self):
        config = self.cam.create_still_configuration({"size": (self.width, self.height)})
        self.cam.configure(config)
        self.cam.options["quality"] = self.quality
        self.cam.set_controls({"AfMode": controls.AfModeEnum.Continuous})
        self.cam.start(show_preview=False)

    @log_execution_time("Image capture time:")
    def capture(self):
        image = self.cam.capture_array()
        return image
