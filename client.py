import os
import time
import json
import logging
import logging.config
import yaml
from subprocess import CalledProcessError
try:
    from libcamera import controls
    from picamera2 import Picamera2
    from paho.mqtt import client as mqtt_client
except ImportError:
    Picamera2 = None
    controls = None
    mqtt_client = None

# ----------------- Config file data ------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_CONFIG_PATH = os.path.join(SCRIPT_DIR, 'log_config.yaml')
CONFIG_PATH = os.path.join(SCRIPT_DIR, 'config.json')
BROKER = "192.168.0.108"
PORT = 1883
TOPIC = "mqtt/rpi/image"
# ------------------------------------------------------


class MQTT:
    def __init__(self):
        self.broker = BROKER
        self.topic = TOPIC
        self.port = PORT
        self.client
        
    def connect(self):
        def on_connect(client, userdata, flags, rc, properties=None):
            if rc == 0:
                logging.info("Connected to MQTT Broker!")
            else:
                print(f"Failed to connect, return code {rc}")

        client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2)
        client.on_connect = on_connect
        client.connect(self.broker, self.port)
        return client
    
    def publish(self, picture):
        start_time = time.time()
        msg_info = self.client.publish(self.topic, picture, qos=1)
        msg_info.wait_for_publish()
        time_taken = time.time() - start_time
        logging.info(f"Time taken to publish: {time_taken:.2f} seconds")
        if msg_info.is_published():
            logging.info(f"Message sent to topic {self.topic}")
        else:
            logging.error(f"Failed to send message to topic {self.topic}")




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
        self.save_dir = os.path.dirname(config['path']) or '.'
        self.gain = config['gain']
        self.exposure = config['exposure']
        self.width = config['width']
        self.height = config['height']
        self.contrast = config['contrast']
        self.cam = Picamera2()
        self.counter = 0

    def start(self):
        config = self.cam.create_still_configuration({"size": (self.width, self.height)})
        self.cam.configure(config)

        # Set up continuous autofocus
        self.cam.set_controls({"AfMode": controls.AfModeEnum.Continuous})

        self.cam.start(show_preview=False)

        # Allow some time for autofocus to settle
        time.sleep(2)

    def capture(self):
        os.makedirs(self.save_dir, exist_ok=True)
        filename = f"image_{self.counter:04d}.jpg"
        full_path = os.path.join(self.save_dir, filename)
        self.cam.capture_file(full_path)
        self.counter += 1
        return full_path

class App:
    def __init__(self, config_path):
        self.camera_config = self._load_camera_config(config_path)
        self.camera = Camera(self.camera_config)
        self.sub = MQTT()

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

    def run(self, duration):
        self.camera.start()
        end_time = time.time() + duration
        while time.time() < end_time:
            start_capture = time.time()
            image_path = self.camera.capture()
            capture_time = time.time() - start_capture
            logging.info(f"Image saved: {image_path}")
            logging.info(f"Image saving time: {capture_time:.2f} seconds")
            sleep_time = max(0, 1 - capture_time)
            time.sleep(sleep_time)

if __name__ == "__main__":
    logger = Logger(LOG_CONFIG_PATH)
    logger.start()

    app = App(CONFIG_PATH)

    # Run for 60 seconds (1 minute)
    app.run(duration=60)

    print("Image capture sequence completed")