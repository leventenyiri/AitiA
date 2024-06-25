import subprocess
import requests
import time
import logging

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

def emulated_camera():
    url = "http://192.168.0.108/capture"
    try:
        response = requests.get(url, stream = True, timeout = 1)
        response.raise_for_status()
        if response.status_code == 200:
            return response.content
        
    except requests.exceptions.RequestException as e:
        logging.error(e)
        exit(1)
        

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
    logging.basicConfig(level=logging.DEBUG, filename='client.log', filemode='w',
                        format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    logging.info("Start of the log")
    start_time = time.time()
    mount_nfs()
    logging.info("Mount time: " + str(time.time() - start_time) + " seconds")
    while(True):
            save_image(emulated_camera())
            logging.info("Image saving time: " + str(time.time() - start_time) + " seconds") 
            time.sleep(10)

        