from paho.mqtt import client as mqtt_client
from static_config import BROKER, CONFIGTOPIC, PORT

broker = BROKER
port = PORT
topic = CONFIGTOPIC


def connect_mqtt() -> mqtt_client.Client:
    def on_connect(client, userdata, flags, rc, properties=None):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print(f"Failed to connect, return code {rc}")

    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2)
    client.username_pw_set("er-edge-3c547181", "admin")
    client.enable_logger()
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def subscribe(client: mqtt_client.Client):
    def on_message(client, userdata, msg):
        print(f"Received message {msg.payload.decode()}")

    client.subscribe(topic)
    client.on_message = on_message


if __name__ == '__main__':
    client = connect_mqtt()
    subscribe(client)
    client.loop_forever()