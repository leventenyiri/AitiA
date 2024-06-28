import subprocess
import time
import io
import logging
from picamera2 import Picamera2
from libcamera import controls

picam2 = Picamera2()

def configure_camera():
    config = picam2.create_still_configuration()
    picam2.configure(config)
    # JPEG quality level: 0 - 95
    picam2.options["quality"] = 95
    # Use NULL preview
    picam2.start(show_preview = False)
    time.sleep(2)
    #picam2.set_controls({"AfMode": controls.AfModeEnum.Continuos}) #Auto
    # Start the focusing asynchronously
    #focusing = picam2.autofocus_cycle(wait=False)

def mount_nfs():
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
        
def save_image(image_data):
    path = '/mnt/nfs_share/picture.jpg'
    
    try:
        # Save the image to the NFS share
        with open(path, 'wb') as f:
            f.write(image_data)
            print(f"Image saved to {path}")
            logging.info(f"Image saved to {path}")
            
    except FileNotFoundError as e: 
        logging.critical(e)
        exit(1)
        

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, filename='NFS_client.log', filemode='w',
                        format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    logging.info("Start of the log")
    #configure_camera()
    start_time = time.time()
    mount_nfs()
    logging.info("Mount time: " + str(time.time() - start_time) + " seconds")
    while(True):
            #focusing = picam2.autofocus_cycle(wait=False)
            #image_stream = io.BytesIO()
            #metadata = picam2.capture_metadata()
            #logging.info(metadata["ExposureTime"], metadata["AnalogueGain"])
            
            #if(picam2.wait(focusing)):
            #picam2.capture_file(image_stream, format='jpeg')
            #image_data = image_stream.getvalue()
            #save_image(image_data)
            picam2.capture_file('/mnt/nfs_share/picture.jpg')
            logging.info("Image saving time: " + str(time.time() - start_time) + " seconds") 
            print(f"Image saved")
            #else:
                #logging.error("Couldn't focus!")
                
            time.sleep(10)
