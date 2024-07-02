import subprocess
import time
import json
import logging
import logging.config
import yaml
import os
try:
    from picamera2 import Picamera2
except ImportError:
    Picamera2 = None

# ----------------- Config file data ------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
log_path = os.path.join(script_dir, 'log_config.yaml')
config_path = os.path.join(script_dir, 'config.json')
# ------------------------------------------------------


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
    def __init__(self, quality, save_path):
        self.quality = quality
        self.save_path = save_path
        self.cam = Picamera2()

    def start(self, quality):
        config = self.cam.create_still_configuration()
        self.cam.configure(config)
        # JPEG quality level: 0 - 95
        self.cam.options['quality'] = quality
        # Use NULL preview
        self.cam.start(show_preview=False)
        time.sleep(2)

    def capture(self):
        self.cam.capture_file(self.path)


class App:
    def __init__(self, config_path):
        # Read the config data to dictionaries
        camera_config = App.read_json_to_dict(config_path, ['Camera'])
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

    def mount_nfs(self):
        while True:
            try:
                # Run the mount command
                result = subprocess.run(['sudo', 'mount', '/mnt/nfs_share'],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        text=True,
                                        check=True)

                # If mount was successful, break the loop
                if result.returncode == 0:
                    logging.info("Mount successful.")
                    break

            except subprocess.CalledProcessError as e:
                logging.critical(f"An error occurred while mounting: {e}")
                logging.critical(f"Error Output: {e.stderr}")
                exit(1)

            except Exception as e:
                logging.critical(f"An error occurred while mounting: {e}")
                exit(1)

            time.sleep(1)
            logging.info("Retrying...")


if __name__ == "__main__":
    start_time = time.time()
    log = Log(log_path)
    log.start()

    app = App(config_path)

    app.mount_nfs()
    app.camera.start()
    app.camera.capture()

    logging.info("Image saving time: " + str(time.time() - start_time) + " seconds")
    print("Image saved")
