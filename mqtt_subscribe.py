# python 3.11
import random
from paho.mqtt import client as mqtt_client
import base64
import time

broker = '192.168.0.108'
port = 1883
topic = "python/mqtt"

def connect_mqtt() -> mqtt_client.Client:
    def on_connect(client, userdata, flags, rc, properties=None):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print(f"Failed to connect, return code {rc}")

    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

# Path to save the received image
output_image_path = "received_image.jpg"
# Variable to store the time when the image is received
start_time = None

def subscribe(client: mqtt_client.Client):
    def on_message(client, userdata, msg):
        global start_time
        # Save the binary data to a file
        with open(output_image_path, "wb") as output_image:
            output_image.write(msg)
        print(f"Received and saved image as {output_image_path}")
        # Record the time when the image is received
        received_time = time.time()
        # Print the time taken to receive the image
        print(f"Time taken to receive: {received_time - start_time:.2f} seconds")

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