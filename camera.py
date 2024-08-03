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
    """
    A class to represent and manage the arducam 16 mpx autofocus camera.

    Parameters
    ----------
    config : dict
        Configuration dictionary specifying the camera settings.

    Attributes
    ----------
    quality : int
        The quality setting for image capture, with a default value of 95.
    cam : Picamera2
        The camera object, Picamera2 instance.
    width : int
        The width of the captured image based on the quality setting.
    height : int
        The height of the captured image based on the quality setting.
    """

    def __init__(self, config):
        """
        Initializes the Camera class with the given configuration.

        The constructor sets the image quality to 95 by default and initializes the
        camera object. It then configures the camera resolution based on the provided
        quality setting in the configuration dictionary. If an invalid quality setting
        is specified, it defaults to 3K quality and logs an error.

        Parameters
        ----------
        config : dict
            Configuration dictionary specifying the camera settings.
        """
        self.quality = 95
        self.cam = Picamera2()

        # Set the premade settings
        if config["quality"] == "4K":
            self.width = 3840
            self.height = 2160
        elif config["quality"] == "3K":
            self.width = 2560
            self.height = 1440
        elif config["quality"] == "HD":
            self.width = 1920
            self.height = 1080
        # If the specified quality is not found, default to 3K quality
        else:
            self.width = 2560
            self.height = 1440
            logging.error(f"Invalid quality specified: {config['quality']}. Defaulting to 3K quality.")

    def start(self):
        """
        Configures and starts the camera with the specified settings.

        This function sets up the camera configuration based on the width and height
        attributes, applies the quality setting, and sets the autofocus mode to continuous.
        Finally, it starts the camera.

        Parameters
        ----------
        None
        """
        config = self.cam.create_still_configuration({"size": (self.width, self.height)})
        self.cam.configure(config)
        self.cam.options["quality"] = self.quality
        self.cam.set_controls({"AfMode": controls.AfModeEnum.Continuous})
        self.cam.start(show_preview=False)

    @log_execution_time("Image capture time:")
    def capture(self):
        """
        Captures an image from the camera and returns it as numpy array.

        This function captures an image using the camera's current settings and returns
        the image data as a numpy array.

        Returns
        -------
        ndarray
            The captured image as a numpy array.
        """
        image = self.cam.capture_array()
        return image
