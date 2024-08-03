import time
import logging
import logging.config
import yaml
import sys
from functools import wraps
from custom_logger import CustomLogger


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


class Logger:
    def __init__(self, filepath):
        self.filepath = filepath
        self.mqtt_client = None
        self.config = None

    def start(self):
        try:
            with open(self.filepath, 'r') as f:
                self.config = yaml.safe_load(f)

            from mqtt import MQTT
            mqtt = MQTT()
            mqtt.connect()
            self.mqtt_client = mqtt.get_client()

            custom_logger = CustomLogger('root', self.mqtt_client)
            logging.root = custom_logger
            logging.root.setLevel(logging.DEBUG)

            for handler_name, handler_config in self.config['handlers'].items():
                handler = self.setup_handler(handler_name, handler_config)
                custom_logger.addHandler(handler)

            logging.info("Logging started")
        except Exception as e:
            print(f"Error starting logger: {str(e)}")
            raise

    def setup_handler(self, handler_name, handler_config):
        handler_class = self.get_handler_class(handler_config.pop('class'))
        level = handler_config.pop('level', None)
        formatter_name = handler_config.pop('formatter', None)

        # Special handling for StreamHandler
        if handler_class == logging.StreamHandler:
            stream = handler_config.pop('stream', None)
            if stream == 'ext://sys.stdout':
                handler_config['stream'] = sys.stdout
            elif stream == 'ext://sys.stderr':
                handler_config['stream'] = sys.stderr

        handler = handler_class(**handler_config)

        if level:
            handler.setLevel(getattr(logging, level.upper(), logging.DEBUG))

        if formatter_name:
            formatter_config = self.config['formatters'][formatter_name]
            formatter = logging.Formatter(
                formatter_config['format'],
                datefmt=formatter_config.get('datefmt')
            )
            handler.setFormatter(formatter)

        return handler

    def get_handler_class(self, class_name):
        handler_classes = {
            'logging.StreamHandler': logging.StreamHandler,
            'logging.FileHandler': logging.FileHandler,
            'logging.handlers.RotatingFileHandler': logging.handlers.RotatingFileHandler,
        }
        handler_class = handler_classes.get(class_name)
        if handler_class is None:
            raise ValueError(f"Unsupported handler class: {class_name}")
        return handler_class
