import subprocess
import time
import json
import logging
from picamera2 import Picamera2

# Config file data
config_path = 'config.json'

path = '/mnt/nfs_share/picture.jpg'
log_level = logging.DEBUG
log_path = 'Test.log'
quality = 95

class Log:
    def __init__(self, path, level):
        self.path = path
        self.level = level
        
    def start(self):
        logging.basicConfig(level=self.level, filename=self.path, filemode='w',
                            format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
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
        log_config = App.read_json_to_dict(config_path, ['Log'])
        
        # Pass the config data 
        self.log = Log(log_config['path'], log_config['level'])
        self.camera = Camera(camera_config['quality'], camera_config['path'])
    
    @staticmethod
    def read_json_to_dict(test, keys):
        with open(test, 'r') as file:
            data = json.load(file)
        return {key: data[key] for key in keys if key in data}
        
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
    
    app = App(config_path)
    
    app.log.start()
    app.mount_nfs()
    app.camera.start(quality)
    app.camera.capture()
    
    logging.info("Image saving time: " + str(time.time() - start_time) + " seconds")
    print("Image saved")
