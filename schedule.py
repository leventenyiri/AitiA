from datetime import datetime, timedelta
import os
import json
import logging
from static_config import SHUTDOWN_THRESHOLD, DEFAULT_BOOT_SHUTDOWN_TIME


class Schedule:
    def __init__(self, period):
        self.state_file = "state_file.json"
        self.period = period
        self.max_boot_time = 10800,  # 3 hours
        self.shutdown_threshold = SHUTDOWN_THRESHOLD
        self.boot_shutdown_time = None
        self.last_shutdown_time = None
        self.load_boot_state()

    def update_boot_time(self, current_time):
        if self.last_shutdown_time is None and (self.period > self.shutdown_threshold):
            return "First run or state file was reset. Will measure boot time on next cycle. Using default value for first shutdown period"

        last_shutdown = datetime.fromisoformat(self.last_shutdown_time)
        boot_time = (current_time - last_shutdown).total_seconds()

        if boot_time <= self.max_boot_time:
            self.boot_shutdown_time = boot_time
            return f"Measured boot and shutdown time: {self.boot_shutdown_time} seconds"
        else:
            return f"Long shutdown detected (duration: {boot_time} seconds). Not updating boot time."

    def calculate_waiting_time(self, elapsed_time):
        return max(self.period - elapsed_time, 0)

    def should_shutdown(self, waiting_time):
        return waiting_time > self.shutdown_threshold

    def calculate_shutdown_duration(self, waiting_time):
        shutdown_duration = waiting_time - self.boot_shutdown_time
        return max(shutdown_duration, 0)

    def get_wake_time(self, current_time, shutdown_duration):
        return current_time + timedelta(seconds=shutdown_duration)

    def load_boot_state(self):
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            self.boot_shutdown_time = state.get('boot_shutdown_time')
            self.last_shutdown_time = state.get('last_shutdown_time')
        else:
            self.boot_shutdown_time = DEFAULT_BOOT_SHUTDOWN_TIME  # This will get overwritten on the first shutdown-wake sequence
            self.last_shutdown_time = None

    def save_boot_state(self):
        state = {
            'boot_shutdown_time': self.boot_shutdown_time,
            'last_shutdown_time': self.last_shutdown_time,
        }
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f)
        except IOError as e:
            logging.error(f"Failed to save state file: {e}")
