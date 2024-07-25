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


class RTC:
    @staticmethod
    def get_time():
        try:
            result = subprocess.run(['timedatectl'], capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"Error getting date from timedatectl: {result.stderr}")

            lines = result.stdout.splitlines()
            utc_time_line = next(line for line in lines if "Universal time:" in line)
            utc_time_str = utc_time_line.split(': ', 1)[1].strip()

            utc_datetime = datetime.strptime(utc_time_str, "%a %Y-%m-%d %H:%M:%S UTC")
            utc_datetime = pytz.UTC.localize(utc_datetime)

            return utc_datetime.isoformat()

        except Exception as e:
            logging.error(f"Error reading system time: {e}")
            return datetime.now(pytz.UTC).isoformat()

    # Time syncing problem???
    @staticmethod
    def set_time(time_to_set):
        try:
            time_str = time_to_set.strftime('%H:%M:%S')
            subprocess.run(['sudo', 'date', '-s', time_str], check=True)
            subprocess.run(['sudo', 'hwclock', '--systohc'], check=True)
            logging.info(f"RTC time set to {time_str}")
        except subprocess.CalledProcessError as e:
            logging.error(f"Error setting RTC time: {e}")
