from mock_autogen import PytestMocker
from camera import Camera

PytestMocker(Camera).mock_everything().generate()


""" def test_camera_init():

    # Arrange: todo
    basic_config = {
        "quality": "4K",
        "mode": "single-shot",
        "period": 100,
        "manual_camera_settings_on": False
    }
    cam_config = {
        "quality": 95,
        "width": 3840,
        "height": 2160
    } """
