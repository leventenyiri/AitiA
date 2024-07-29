import subprocess
import logging
from datetime import datetime
import pytz
import time
try:
    from gpiozero import CPUTemperature
except ImportError:
    CPUTemperature = None


class System:
    @staticmethod
    def shutdown():
        logging.info("Pi has been shut down")
        subprocess.run(['sudo', 'systemctl', 'poweroff', '-no-block'], check=True)

    @staticmethod
    def get_cpu_temperature():
        cpu = CPUTemperature()
        return cpu.temperature

    @staticmethod
    def get_battery_info():
        try:
            # Battery info is path dependant!!!!
            result = subprocess.run(['upower', '-i', '/org/freedesktop/UPower/devices/battery_bq2562x_battery'],
                                    stdout=subprocess.PIPE, check=True)
            info = result.stdout.decode('utf-8')

            battery_info = {
                'temperature': None,
                'percentage': None
            }

            for line in info.splitlines():
                if "temperature:" in line:
                    battery_info['temperature'] = float(line.split(":")[1].strip().split()[0])
                if "percentage:" in line:
                    battery_info['percentage'] = float(line.split(":")[1].strip().replace('%', ''))

            return battery_info

        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to get battery info: {e}")
            exit(1)


class RTC:
    @staticmethod
    def sync_RTC_to_system():
        try:
            subprocess.run(['sudo', 'hwclock', '--systohc'], check=True)
            logging.info(f"RTC synced to system clock")
        except subprocess.CalledProcessError as e:
            logging.error(f"Error syncing RTC: {e}")

    @staticmethod
    def sync_system_to_ntp(max_retries=5, delay=2):
        for retry in range(max_retries):
            time.sleep(delay)
            lines = RTC.get_timedatectl()
            is_synced = RTC.find_line(lines, "System clock synchronized:")
            if is_synced == "yes":
                return True
            logging.warning(f"Failed to sync system to NTP, retrying ({retry+1}/{max_retries})")
            delay *= 2
        return False

    @staticmethod
    def convert_timestamp(timestamp_str):
        """Convert a timestamp string to ISO 8601 format."""
        try:
            # Remove the 'UTC' part if it exists
            parts = timestamp_str.split()
            # if the last element is 'UTC' remove it
            if parts[-1] == 'UTC':
                timestamp_str = ' '.join(parts[:-1])
            # Parse the timestamp while ignoring the weekday and timezone
            timestamp = datetime.strptime(timestamp_str, "%a %Y-%m-%d %H:%M:%S")
            # Localize to UTC
            timestamp = pytz.UTC.localize(timestamp)
            return timestamp.isoformat()
        except Exception as e:
            logging.error(f"Error parsing timestamp: {e}")
            exit(1)

    @staticmethod
    def get_timedatectl():
        """Get output from the 'timedatectl' command."""
        result = subprocess.run(['timedatectl'], capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Error getting date from timedatectl: {result.stderr}")
        return result.stdout.splitlines()

    @staticmethod
    def find_line(lines, target_string):
        """Find and return the line containing the target string."""
        found_line = next(line for line in lines if target_string in line)
        return found_line.split(': ', 1)[1].strip()

    @staticmethod
    def get_time():
        """Get the current time, ensuring synchronization with NTP and RTC."""
        try:
            # Get all the lines from timedatectl output
            lines = RTC.get_timedatectl()

            """  # Check if system clock synchronized to the NTP servers
            is_synced = RTC.find_line(lines, "System clock synchronized:")
            if is_synced == "no":
                # Try to sync system clock to the NTP servers again
                if not RTC.sync_system_to_ntp():
                    logging.error("Couldn't sync system clock to the NTP servers, current time is not correct.")
                    exit(1) """

            # Get the RTC time
            rtc_time_line = RTC.find_line(lines, "RTC time:")
            rtc_datetime = RTC.convert_timestamp(rtc_time_line)

            # Get the time from the system clock
            utc_time_line = RTC.find_line(lines, "Universal time:")
            utc_datetime = RTC.convert_timestamp(utc_time_line)

            # If the RTC time is different from the system clock, sync the RTC
            if rtc_datetime != utc_datetime:
                RTC.sync()

            return utc_datetime

        except Exception as e:
            logging.error(f"Error reading system time: {e}")
            return datetime.now(pytz.UTC).isoformat()
