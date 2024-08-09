import os
import logging

# Configuration file paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_CONFIG_PATH = os.path.join(SCRIPT_DIR, 'log_config.yaml')
CONFIG_PATH = os.path.join(SCRIPT_DIR, 'config.json')
TEMP_CONFIG_PATH = os.path.join(SCRIPT_DIR, 'temp_config.json')
STATE_FILE_PATH = os.path.join(SCRIPT_DIR, 'state_file.json')

# MQTT Configuration
# BROKER = "debian.local"
BROKER = "192.168.0.160"
PORT = 1883
IMAGETOPIC = "mqtt/rpi/image"
CONFIGACKTOPIC = "er-edge/confirm"
CONFIGSUBTOPIC = "settings/er-edge"
QOS = 2
USERNAME = "er-edge"
PASSWORD = "admin"

# App configuration
SHUTDOWN_THRESHOLD = 70  # in seconds
DEFAULT_BOOT_SHUTDOWN_TIME = 30  # in seconds
MINIMUM_WAIT_TIME = 5  # in seconds
MAXIMUM_WAIT_TIME = 10800  # 3 hours in seconds

# Log configuration
LOGGING_TOPIC = "er-edge/logging"
LOG_LEVEL = logging.DEBUG
