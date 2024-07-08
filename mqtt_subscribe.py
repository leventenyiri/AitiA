# python 3.11
import random
from paho.mqtt import client as mqtt_client
import base64
import time
import logging
import json
from PIL import Image
import io
from datetime import datetime

broker = '192.168.0.103'
port = 1883
topic = "mqtt/rpi/image"
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler()])

def connect_mqtt() -> mqtt_client.Client:
    def on_connect(client, userdata, flags, rc, properties=None):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print(f"Failed to connect, return code {rc}")

    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2)
    client.enable_logger()
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

# Variable to store the time when the image is received
start_time = None

def subscribe(client: mqtt_client.Client):
    def on_message(client, userdata, msg):
        global start_time
        received_time = time.time()
        logging.info(f"Time taken to receive: {received_time - start_time:.2f} seconds")
        
        try:
            # Parse the JSON message
            payload = json.loads(msg.payload)
            
            # Extract timestamp and image data
            timestamp = payload['timestamp']
            image_base64 = payload['image']
            
            # Decode the Base64 image data
            image_data = base64.b64decode(image_base64)
            
            # Create a timestamp string for filenames
            time_string = datetime.fromtimestamp(timestamp).strftime("%Y%m%d_%H%M%S")
            
            # Save directly to a file
            output_image_path = f"image_{time_string}.jpg"
            with open(output_image_path, "wb") as f:
                f.write(image_data)
            logging.info(f"Received and saved image as {output_image_path}")
            
            # Load into a PIL Image object (for metadata or future processing if needed)
            image = Image.open(io.BytesIO(image_data))
            logging.info(f"Image size: {image.size}")
            
            logging.info(f"Image timestamp: {timestamp}")
            logging.info(f"Time received: {received_time}")
            logging.info(f"Delay: {received_time - timestamp:.2f} seconds")
            
        except Exception as e:
            logging.error(f"Failed to process image: {e}")

    client.subscribe(topic)
    client.on_message = on_message
    
def run():
    global start_time
    client = connect_mqtt()
    start_time = time.time()
    subscribe(client)
    client.loop_forever()

if __name__ == '__main__':
    run()