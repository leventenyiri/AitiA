import time
import logging
import logging.config
import logging.handlers
# import yaml
# import os
from functools import wraps


def log_execution_time(operation_name=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            execution_time = end_time - start_time

            if operation_name:
                log_message = f"{operation_name} ({func.__name__}) took {execution_time:.6f} seconds"
            else:
                log_message = f"{func.__name__} took {execution_time:.6f} seconds"

            logging.info(log_message)
            return result
        return wrapper
    return decorator


""" class Logger:
    def __init__(self, filepath):
        self.filepath = filepath

    def start(self):
        try:
            if not os.path.exists(self.filepath):
                raise FileNotFoundError(f"Log configuration file not found: {self.filepath}")
            with open(self.filepath, 'r') as f:
                config = yaml.safe_load(f)
            logging.config.dictConfig(config)

            # Manually create and add the MQTT handler
            mqtt_handler = MQTTHandler()
            mqtt_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s -%(name)s - %(levelname)s - %(message)s')
            mqtt_handler.setFormatter(formatter)
            # Add the MQTT handler to the root logger
            logging.getLogger().addHandler(mqtt_handler)
            print("Log config from dict has loaded")

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
 """
