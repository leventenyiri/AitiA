import logging
from static_config import LOGGING_TOPIC
from queue import Queue
import threading


class CustomLogger(logging.Logger):
    def __init__(self, name, mqtt_client):
        super().__init__(name)
        self.mqtt_client = mqtt_client
        self.log_queue = LogQueue()
        self.stop_event = threading.Event()
        self.publish_thread = threading.Thread(target=self.publish_loop, daemon=True)
        self.publish_thread.start()
        self.mqtt_lock = threading.Lock()

    def debug(self, message):
        super().debug(message)
        self.queue_log('DEBUG', message)

    def info(self, message):
        super().info(message)
        self.queue_log('INFO', message)

    def warning(self, message):
        super().warning(message)
        self.queue_log('WARNING', message)

    def error(self, message):
        super().error(message)
        self.queue_log('ERROR', message)

    def critical(self, message):
        super().critical(message)
        self.queue_log('CRITICAL', message)

    def queue_log(self, level, message):
        self.log_queue.add_log(level, message)

    def publish_loop(self):
        while not self.stop_event.is_set():
            self.process_log_queue()

    def process_log_queue(self):
        if not self.can_publish():
            self.stop_event.wait(timeout=5)
            return

        if not self.log_queue.wait_for_item(timeout=1):
            return

        self.publish_all_logs()

    def can_publish(self):
        return self.mqtt_client and self.mqtt_client.is_connected()

    def publish_all_logs(self):
        while not self.log_queue.is_empty():
            log_entry = self.log_queue.get_log()
            if log_entry:
                self.publish_log(log_entry)

    def publish_log(self, log_entry):
        level, message = log_entry
        mqtt_message = f"{level}|{message}"
        with self.mqtt_lock:
            try:
                self.mqtt_client.publish(LOGGING_TOPIC, mqtt_message)
            except Exception as e:
                self.logger.error(f"Failed to publish log: {e}")
                # Re-queue the log entry
                self.log_queue.add_log(level, message)

    def stop(self):
        self.stop_event.set()
        self.publish_thread.join()


class LogQueue:
    def __init__(self):
        self.queue = Queue()
        self.lock = threading.Lock()
        self.not_empty = threading.Event()

    def add_log(self, level, message):
        with self.lock:
            self.queue.put((level, message))
            self.not_empty.set()

    def get_log(self):
        with self.lock:
            if self.queue.empty():
                self.not_empty.clear()
                return None
            return self.queue.get()

    def is_empty(self):
        with self.lock:
            return self.queue.empty()

    def wait_for_item(self, timeout=None):
        return self.not_empty.wait(timeout)
