from source.camera import Camera
import unittest
from unittest.mock import patch, MagicMock

Picamera2 = MagicMock()
controls = MagicMock()


class TestCamera(unittest.TestCase):
    def setUp(self):
        self.cam_config = {
            'width': 1280,
            'height': 720,
            'quality': 90
        }
        self.basic_config = {
            'manual_camera_settings_on': False
        }

    @patch('camera.Picamera2', Picamera2)
    @patch('camera.controls', controls)
    def test_init_manual_settings(self):
        self.basic_config['manual_camera_settings_on'] = True
        camera = Camera(self.cam_config, self.basic_config)

        self.assertEqual(camera.width, 1280)
        self.assertEqual(camera.height, 720)
        self.assertEqual(camera.quality, 90)

    @patch('camera.Picamera2', Picamera2)
    @patch('camera.controls', controls)
    def test_init_3k_settings(self):
        self.basic_config['quality'] = '3K'
        camera = Camera(self.cam_config, self.basic_config)

        self.assertEqual(camera.width, 2560)
        self.assertEqual(camera.height, 1440)
        self.assertEqual(camera.quality, 95)

    @patch('logging.error')
    @patch('camera.Picamera2', Picamera2)
    @patch('camera.controls', controls)
    def test_init_invalid_settings(self, mock_logging_error):
        self.basic_config['quality'] = 'invalid'
        camera = Camera(self.cam_config, self.basic_config)

        self.assertEqual(camera.width, 2560)
        self.assertEqual(camera.height, 1440)
        self.assertEqual(camera.quality, 95)
        mock_logging_error.assert_called_once_with("Invalid quality specified: invalid. Defaulting to 3K quality.")
