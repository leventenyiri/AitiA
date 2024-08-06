import logging
import logging.config
import logging.handlers
import yaml
import os
import threading
from queue import Queue, Empty
from .static_config import LOGGING_TOPIC


class Logger(logging.Handler):
    def __init__(self, filepath):
        super().__init__()
        self.filepath = filepath
        self.log_queue = Queue()
        self.log_event = threading.Event()
        self.publish_thread = threading.Thread(target=self.publish_loop)
        # self.publish_thread.daemon = True
        self.run = False
        logging.info("Logger initialized")

    def start_mqtt_logging(self):
        logging.info("MQTT logging is about to start")
        from .mqtt import MQTT
        self.mqtt = MQTT()
        self.mqtt.connect()
        self.run = True
        self.publish_thread.start()
        logging.info("MQTT logging started")

    def start_logging(self):
        try:
            if not os.path.exists(self.filepath):
                raise FileNotFoundError(f"Log configuration file not found: {self.filepath}")
            with open(self.filepath, 'r') as f:
                config = yaml.safe_load(f)
            logging.config.dictConfig(config)

            """ # Manually create and add the MQTT handler
            mqtt_handler = MQTTHandler()
            mqtt_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s -%(name)s - %(levelname)s - %(message)s')
            mqtt_handler.setFormatter(formatter)
            # Add the MQTT handler to the root logger
            logging.getLogger().addHandler(mqtt_handler)
            print("Log config from dict has loaded")
            """
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

    def emit(self, record):
        try:
            # This format is needed
            msg = self.format(record)
            self.log_queue.put(msg)
            if self.run:
                self.log_event.set()
        except Exception as e:
            print(f"Error in MQTTHandler emit: {e}")
            exit(1)

    def publish_loop(self):
        logging.info("Publish thread started")
        while self.run:
            while self.log_event.is_set():
                try:
                    msg = self.log_queue.get(timeout=1)
                    self.mqtt.client.publish(msg, LOGGING_TOPIC)
                except Empty:
                    self.log_event.clear()
                except Exception as e:
                    print(f"Error in MQTTHandler publish loop: {e}")
                    exit(1)

            self.log_event.wait(4)

    def close(self):
        # self.run = False
        # self.publish_thread.join(timeout=6)
        # self.mqtt.disconnect()
        super().close()
