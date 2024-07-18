try:
    from libcamera import controls
    from picamera2 import Picamera2
except ImportError:
    Picamera2 = None
    controls = None
from utils import log_execution_time
import logging


class Camera:
    def __init__(self, cam_config, basic_config):
        # The best quality is set as default
        self.quality = 95
        self.cam = Picamera2()

        # Set the custom camera settings from the config file
        if basic_config['manual_camera_settings_on']:
            self.width = cam_config['width']
            self.height = cam_config['height']
            self.quality = cam_config['quality']

        # Set the premade settings
        elif basic_config['quality'] == "4K":
            self.width = 3840
            self.height = 2160
        elif basic_config['quality'] == "3K":
            self.width = 2560
            self.height = 1440
        elif basic_config['quality'] == "HD":
            self.width = 1920
            self.height = 1080
        # If the specified quality is not found, default to 3K quality
        else :
            self.width = 2560
            self.height = 1440
            logging.error(f"Invalid quality specified: {basic_config['quality']}. Defaulting to 3K quality.")

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
