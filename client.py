# python 3.11
import time
from paho.mqtt import client as mqtt_client

broker = "192.168.0.103"
port = 1883
topic = "mqtt/rpi/image"

def connect_mqtt():
    def on_connect(client, userdata, flags, rc, properties=None):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print(f"Failed to connect, return code {rc}")

    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

def convert_image():
    with open("file.jpg",'rb') as file:
        filecontent = file.read()
        return bytearray(filecontent)

def publish(client):
    start_time = time.time()
    msg_info = client.publish(topic, convert_image(), qos=1)
    msg_info.wait_for_publish()
    end_time = time.time()
    time_taken = end_time - start_time
    print(f"Time taken to publish: {time_taken:.2f} seconds")
    if msg_info.is_published():
        print(f"Message sent to topic {topic}")
    else:
        print(f"Failed to send message to topic {topic}")

def run():
    client = connect_mqtt()
    client.loop_start()
    publish(client)
    client.loop_stop()
    client.disconnect()

if __name__ == '__main__':
    run()