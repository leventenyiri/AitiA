from datetime import datetime, time
from datetime import timedelta
import os
import json
import logging
from .static_config import SHUTDOWN_THRESHOLD, DEFAULT_BOOT_SHUTDOWN_TIME, MAXIMUM_WAIT_TIME, STATE_FILE_PATH
from .system import System, RTC


class Schedule:
    def __init__(self, period):
        self.state_file = STATE_FILE_PATH
        self.period = period
        self.max_boot_time = MAXIMUM_WAIT_TIME
        self.shutdown_threshold = SHUTDOWN_THRESHOLD
        self.boot_shutdown_time = None
        self.last_shutdown_time = None
        self.load_boot_state()

    def working_time_check(self, wakeUpTime, shutDownTime) -> None:
        """
        Checks if the current time is within the operational hours defined in the configuration.

        If the current time is outside the operational hours, the system will initiate a shutdown.
        The time is in UTC timezone.
        """
        wake_up_time: time = datetime.strptime(wakeUpTime, "%H:%M:%S").time()
        shut_down_time: time = datetime.strptime(shutDownTime, "%H:%M:%S").time()

        utc_time: datetime = datetime.fromisoformat(RTC.get_time())
        current_time: time = utc_time.time()

        logging.info(
            f"wake up time is : {wake_up_time}, shutdown time is : {shut_down_time}, current time is : {current_time}"
        )

        # If e.g: wake up time = 6:00:00 and shutdown time = 20:00:00
        if (wake_up_time < shut_down_time) and (wake_up_time > current_time or current_time >= shut_down_time):
            logging.info("Starting shutdown")
            System.shutdown()

        # If e.g: wake up time = 20:00:00 and shutdown time = 6:00:00
        elif current_time >= shut_down_time and current_time < wake_up_time:
            logging.info("Starting shutdown")
            System.shutdown()

    def update_boot_time(self, current_time):
        if self.last_shutdown_time is None and (self.period > self.shutdown_threshold):
            self.last_shutdown_time = current_time.isoformat()
            return "First run or state file was reset. Will measure boot time on next cycle. Using default value for first shutdown period"

        last_shutdown = datetime.fromisoformat(self.last_shutdown_time)
        boot_time = (current_time - last_shutdown).total_seconds()

        self.last_shutdown_time = current_time.isoformat()

        if (boot_time <= self.max_boot_time) and (self.period < self.shutdown_threshold):
            return "Period too small to shut down, sleeping in script..."

        if boot_time <= self.max_boot_time:
            self.boot_shutdown_time = boot_time
            return f"Measured boot and shutdown time: {self.boot_shutdown_time} seconds"
        else:
            return f"Long shutdown detected (duration: {boot_time} seconds). Not updating boot time. Current_time is :{current_time}, last_shutdown is: {last_shutdown}"

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
                logging.info("Opened state file")
            self.boot_shutdown_time = state.get('boot_shutdown_time')
            self.last_shutdown_time = state.get('last_shutdown_time')
            logging.info("Loaded boot and shutdown time from state file: boot_shutdown_time")
        else:
            logging.info("No state file found")
            # This will get overwritten on the first shutdown-wake sequence
            self.boot_shutdown_time = DEFAULT_BOOT_SHUTDOWN_TIME
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

    def shutdown(self, waiting_time: float, end_time: datetime) -> None:
        shutdown_duration = self.calculate_shutdown_duration(waiting_time)
        wake_time = self.get_wake_time(end_time, shutdown_duration)

        logging.info(f"Shutting down for {shutdown_duration} seconds")
        try:
            System.schedule_wakeup(wake_time)
            self.last_shutdown_time = end_time.isoformat()
            self.save_boot_state()
            System.shutdown()
        except Exception as e:
            logging.error(f"Failed to schedule wake-up: {e}")
