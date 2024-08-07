import logging
import logging.config
import yaml
import os
import threading
from queue import Queue, Empty
from multiprocessing.pool import ThreadPool
from .static_config import LOGGING_TOPIC, LOG_LEVEL


class Logger(logging.Handler):
    def __init__(self, filepath):
        super().__init__()
        self.filepath = filepath
        self.log_queue = Queue()
        self.mqtt = None
        self.start_event = threading.Event()
        self.pool = ThreadPool()

    def start_logging(self):
        try:
            if not os.path.exists(self.filepath):
                raise FileNotFoundError(f"Log configuration file not found: {self.filepath}")
            with open(self.filepath, 'r') as f:
                config = yaml.safe_load(f)
            logging.config.dictConfig(config)
            # Add the MQTT handler to the root logger
            self.create_handler()
            logging.info("Logging started")

        except ImportError as e:
            print(f"Import error: {e}")
            print("This might be due to missing modules or incorrect import statements.")
        except AttributeError as e:
            print(f"Attribute error: {e}")
            print("This might be due to missing attributes or methods in the MQTTHandler class.")
        except TypeError as e:
            print(f"Type error: {e}")
            print("This might be due to incorrect method signatures or argument types.")
        except Exception as e:
            print(f"Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            exit(1)

    def create_handler(self):
        # Manually create and add the MQTT handler
        self.setLevel(LOG_LEVEL)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.setFormatter(formatter)
        logging.getLogger().addHandler(self)

    def start_mqtt_logging(self):
        from .mqtt import MQTT
        self.mqtt = MQTT()
        self.mqtt.connect()
        self.start_event.set()
        print("MQTT logging started")

    def emit(self, record):
        try:
            msg = self.format(record)
            self.log_queue.put(msg)
            print(f"Queue number increased: {self.log_queue.qsize()}")
            if self.start_event.is_set():
                self.pool.apply_async(self.publish_loop, args=(msg, LOGGING_TOPIC))
        except Exception as e:
            print(f"Error in Logger emit: {e}")

    def publish_loop(self, msg, topic):
        while not self.log_queue.empty():
            try:
                msg = self.log_queue.get(timeout=1)
                print(f"Queue number decreased: {self.log_queue.qsize()}")
                self.mqtt.client.publish(topic, msg)
            except Empty:
                return
            except Exception as e:
                print(f"Error in Logger publish loop: {e}")

    def close(self):
        super().close()

    def disconnect_mqtt(self):
        print("Closing logger")
        self.start_event.clear()
        self.pool.close()
        self.pool.join()
        if self.mqtt.is_connected():
            self.mqtt.disconnect()
        super().close()
