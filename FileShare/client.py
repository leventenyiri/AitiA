import subprocess
import requests
import time
import logging
import os

def mount_nfs():
    while True:
        try:
            # Print current working directory and environment variables for debugging
            logging.info(f"Current working directory: {os.getcwd()}")
            logging.info(f"Environment: {os.environ}")

            # Run the mount command
            result = subprocess.run(['sudo', 'mount', '/mnt/nfs_share'],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True,
                                    check=True)
            logging.info(f"Command Output: {result.stdout}")
            logging.info(f"Command Error: {result.stderr}")

            # If mount was successful, break the loop
            if result.returncode == 0:
                logging.info("Mount successful.")
                break

        except subprocess.CalledProcessError as e:
            logging.error(f"An error occurred while mounting: {e}")
            logging.error(f"Error Output: {e.stderr}")

        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")

        logging.info("Retrying")

# def mount_nfs():
#     try:
#         ret = False
#         # Run the mount command
#         result = subprocess.run(['sudo', 'mount', '/mnt/nfs_share'],
#                                 stdout=subprocess.PIPE,
#                                 stderr=subprocess.PIPE,
#                                 text=True,
#                                 check=True)
#         logging.info(result.stdout)
#         logging.critical(result.stderr)
#         print("Command Output:", result.stdout)
#         print("Command Error:", result.stderr)
#         ret = True

#     except Exception as e:
#         print(f"An unexpected error occurred: {e}")
#         logging.critical(e.stderr)

#     return ret

def emulated_camera():
    url = "http://192.168.0.108/capture"
    try:
        response = requests.get(url, stream = True)
        response.raise_for_status()
        if response.status_code == 200:
            return response.content

    except Exception as e:
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
    logging.info("Mount time: " + str(time.time() - start_time) + "seconds")
    while(True):
            save_image(emulated_camera())
            logging.info("Image saving time: " + str(time.time() - start_time) + "seconds")
            time.sleep(10)