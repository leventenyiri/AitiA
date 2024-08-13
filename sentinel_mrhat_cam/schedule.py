from datetime import datetime, time
from datetime import timedelta
import os
import json
import logging
from .static_config import SHUTDOWN_THRESHOLD, DEFAULT_BOOT_SHUTDOWN_TIME, MAXIMUM_WAIT_TIME, STATE_FILE_PATH
from .system import System, RTC


class Schedule:
    """

    Helps manage the scheduling of operations in the app.py module. Its only used in the run_periodically method, where its important that
    we keep the given period between sending pictures. For this we have to measure the runtime of the script, how much time it takes for the device
    to shut down, and boot up. To know this we have to keep track of the last shutdown time, so we can calculate it.

    Attributes:
        state_file : str
            Path to the file storing the boot state.
        period : float)
            The period between operations.
        max_boot_time : float
            Maximum allowed boot time.
        shutdown_threshold : float
            Minimum waiting time required for shutdown.
        boot_shutdown_time : float
            Time taken for boot and shutdown process.
        last_shutdown_time : str
            ISO formatted string of the last shutdown time.
    """

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
        Check if the current time is within the operational hours defined in the configuration.

        If the current time is outside the operational hours, the system will initiate a shutdown.
        The time is in UTC.

        Parameters
        ----------
        wakeUpTime : str
            The wake-up time in "HH:MM:SS" format.
        shutDownTime : str
            The shutdown time in "HH:MM:SS" format.
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
        """
        Update the boot time based on the current time and last shutdown time.

        This method calculates the boot time, updates the last shutdown time,
        and determines if the system should shut down based on the period and threshold.

        Parameters
        ----------
        current_time : datetime
            The current time.

        Returns
        -------
        str
            A message describing the result of the update operation.
        """
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

    def should_shutdown(self, waiting_time):
        """
        Determine if the system should shut down based on the waiting time.

        Parameters
        ----------
        waiting_time : float
            The time difference between the period and the runtime of the script.

        Returns
        -------
        bool
            True if the system should shut down, False otherwise.
        """
        return waiting_time > self.shutdown_threshold

    def calculate_shutdown_duration(self, waiting_time):
        """
        Calculate the duration for which the system should be shut down.

        Parameters
        ----------
        waiting_time : float
            The time difference between the period and the runtime of the script.

        Returns
        -------
        float
            The duration for which the system should be shut down, cannot be negative.
        """
        shutdown_duration = waiting_time - self.boot_shutdown_time
        return max(shutdown_duration, 0)

    def get_wake_time(self, current_time, shutdown_duration):
        """
        Calculate the time at which the system should wake up.

        Parameters
        ----------
        current_time : datetime
            The current time.
        shutdown_duration : float
            The duration for which the system will be shut down.

        Returns
        -------
        datetime
            The time at which the system should wake up.
        """
        return current_time + timedelta(seconds=shutdown_duration)

    def load_boot_state(self):
        """
        Load the boot state from the state file.

        If the state file exists, it loads the boot_shutdown_time and last_shutdown_time.
        If the file doesn't exist, it sets default values.
        """
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
        """
        Save the current boot state to the state file.

        This method saves the boot_shutdown_time and last_shutdown_time to the state file.
        If saving fails, it logs an error message.
        """
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
        """
        Initiate system shutdown and schedule wake-up.

        This method calculates the shutdown duration, schedules the wake-up time,
        saves the boot state, and initiates system shutdown.

        Parameters
        ----------
        waiting_time : float
            The time difference between the period and the runtime of the script.
        end_time : datetime
            The time the transmission ended. Basically, the current time.
        """
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

    def manage_boot_data(self, end_time: datetime) -> None:
        """
        Manage boot data by loading the boot state, updating boot time, and saving the state.

        This method is typically called at the end of an operation cycle to update
        and persist boot-related information.

        Parameters
        ----------
        end_time : datetime
            The time the transmission ended. Basically, the current time.
        """
        self.load_boot_state()
        message = self.update_boot_time(end_time)
        logging.info(message)
        self.save_boot_state()
