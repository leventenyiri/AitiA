from datetime import datetime, time
from datetime import timedelta
import logging
from .static_config import TIME_TO_BOOT_AND_SHUTDOWN, SHUTDOWN_THRESHOLD
from .system import System, RTC
import pytz


class Schedule:
    def __init__(self, period):
        self.period = period

    def should_shutdown(self, waiting_time) -> bool:
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
        return waiting_time > SHUTDOWN_THRESHOLD

    def shutdown(self, waiting_time: float, current_time: datetime) -> None:
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
        wake_time = self.get_wake_time(current_time, shutdown_duration)

        logging.info(f"Shutting down for {shutdown_duration} seconds")
        try:
            System.schedule_wakeup(wake_time)
            System.shutdown()
        except Exception as e:
            logging.error(f"Failed to schedule wake-up: {e}")

    def calculate_shutdown_duration(self, waiting_time) -> float:
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
        shutdown_duration = waiting_time - TIME_TO_BOOT_AND_SHUTDOWN
        return max(shutdown_duration, 0)

    def get_wake_time(self, shutdown_duration) -> datetime:
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
        current_time_str = RTC.get_time()
        current_time = datetime.fromisoformat(current_time_str)

        # Ensure the datetime is timezone-aware
        if current_time.tzinfo is None:
            current_time = pytz.UTC.localize(current_time)

        return current_time + timedelta(seconds=shutdown_duration)

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
            System.schedule_wakeup(wake_up_time)
            System.shutdown()

        # If e.g: wake up time = 20:00:00 and shutdown time = 6:00:00
        elif current_time >= shut_down_time and current_time < wake_up_time:
            logging.info("Starting shutdown")
            System.schedule_wakeup(wake_up_time)
            System.shutdown()
