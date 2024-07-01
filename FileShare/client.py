import subprocess
import time
import io
import logging
from picamera2 import Picamera2
from libcamera import controls

########## Config file data ###########
path = '/mnt/nfs_share/picture.jpg'
log_level = logging.DEBUG
log_path = 'Test.log'
quality = 95
#####################################

class Log:
    def __init__(self, path, level):
        self.path = path
        self.level = level
        
    def start(self):
        logging.basicConfig(level=self.level, filename=self.path, filemode='w',
                        format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        logging.info("Start of the log")

class Camera:
    def __init__(self, quality, path):
        self.quality = quality
        self.path = path
        self.cam = Picamera2()  
    
    def start(self, quality):
        config = picam2.create_still_configuration()
        picam2.configure(config)
        # JPEG quality level: 0 - 95
        picam2.options["quality"] = quality
        # Use NULL preview
        picam2.start(show_preview = False)
        time.sleep(2)
        
    def capture(self):
        picam2.capture_file(self.path)
        
class App:
    def __init__(self):
        self.log = Log(log_path, log_level)
        self.camera = Camera(quality, path)
        
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
    
    picam2 = Picamera2()
    
    # Need to replace to a deserialazable class/object
    app = App(log_path, log_level, quality, path)
    
    app.log.start()
    app.mount_nfs()
    app.camera.start()
    app.camera.capture()
    
    logging.info("Image saving time: " + str(time.time() - start_time) + " seconds")
    print(f"Image saved")