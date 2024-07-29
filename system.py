import subprocess
import logging
from datetime import datetime
import pytz
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
    def sync():
        try:
            subprocess.run(['sudo', 'hwclock', '--systohc'], check=True)
            logging.info(f"RTC synced to system clock")
        except subprocess.CalledProcessError as e:
            logging.error(f"Error syncing RTC: {e}")

    def convert_timestamp(timestamp_line):
        try:
            timestamp_str = timestamp_line.split(': ', 1)[1].strip()
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
    def get_time():
        try:
            result = subprocess.run(['timedatectl'], capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"Error getting date from timedatectl: {result.stderr}")

            lines = result.stdout.splitlines()

            """Check if system clock synchronized to the NTP servers
            is_synced_line = next(line for line in lines if "System clock synchronized:" in line)
            is_synced = is_synced_line.split(': ', 1)[1].strip()
                if is_synced == "yes":  # in prod "no" !!!!
                # Try to sync system clock to the NTP servers again??
                logging.error("Couldn't sync system clock to the NTP servers, current time is not correct.")
                exit(2) """

            # Get the RTC time
            rtc_time_line = next(line for line in lines if "RTC time:" in line)
            rtc_datetime = RTC.convert_timestamp(rtc_time_line)

            # Get the time from the system clock
            utc_time_line = next(line for line in lines if "Universal time:" in line)
            utc_datetime = RTC.convert_timestamp(utc_time_line)

            # If the RTC time is different from the system clock, sync the RTC
            if rtc_datetime != utc_datetime:
                RTC.sync()

            return utc_datetime

        except Exception as e:
            logging.error(f"Error reading system time: {e}")
            return datetime.now(pytz.UTC).isoformat()
