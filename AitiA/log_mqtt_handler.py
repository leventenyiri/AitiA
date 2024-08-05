import logging
import threading
from queue import Queue, Empty
from AitiA.static_config import LOGGING_TOPIC


class MQTTHandler(logging.Handler):
    def __init__(self):
        from AitiA.mqtt import MQTT
        super().__init__s()
        self.mqtt_client = MQTT()
        self.mqtt_client.connect()
        self.log_queue = Queue()
        self.stop_event = threading.Event()
        self.log_event = threading.Event()
        self.publish_thread = threading.Thread(target=self._publish_loop)
        self.publish_thread.daemon = True
        self.run = True
        self.log_event.set()
        self.publish_thread.start()

    def emit(self, record):
        try:
            # This format is needed
            msg = self.format(record)
            self.log_queue.put(msg)
            self.log_event.set()
        except Exception as e:
            print(f"Error in MQTTHandler emit: {e}")
            exit(1)

    def _publish_loop(self):
        while self.run:
            while self.log_event.is_set():
                try:
                    msg = self.log_queue.get(timeout=1)
                    self.mqtt_client.publish(msg, LOGGING_TOPIC)
                except Empty:
                    self.log_event.clear()
                except Exception as e:
                    print(f"Error in MQTTHandler publish loop: {e}")
                    exit(1)

            self.log_event.wait()

    def close(self):
        self.run = False
        self.stop_event.set()
        self.publish_thread.join(timeout=5)
        self.mqtt_client.disconnect()
        super().close()
