import time
import logging
import logging.config
import yaml
import os
import subprocess
from gpiozero import CPUTemperature
from functools import wraps
from datetime import datetime


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


def get_cpu_temperature():
    cpu = CPUTemperature()
    return cpu.temperature


class RTC:
    @staticmethod
    def get_time():
        try:
            result = subprocess.run(['cat', '/sys/class/rtc/rtc0/time'], capture_output=True, text=True)
            time_str = result.stdout.strip()
            return datetime.strptime(time_str, '%H:%M:%S').time()
        except Exception as e:
            logging.error(f"Error reading RTC time: {e}")
            return None

    @staticmethod
    def set_time(time_to_set):
        try:
            time_str = time_to_set.strftime('%H:%M:%S')
            subprocess.run(['sudo', 'date', '-s', time_str], check=True)
            subprocess.run(['sudo', 'hwclock', '--systohc'], check=True)
            logging.info(f"RTC time set to {time_str}")
        except subprocess.CalledProcessError as e:
            logging.error(f"Error setting RTC time: {e}")


class Logger:
    def __init__(self, filepath):
        self.filepath = filepath

    def start(self):
        try:
            if not os.path.exists(self.filepath):
                raise FileNotFoundError(f"Log configuration file not found: {self.filepath}")
            with open(self.filepath, 'r') as f:
                config = yaml.safe_load(f)
            logging.config.dictConfig(config)
            logging.info("Logging started")
        except Exception as e:
            logging.error(e)
            exit(1)
