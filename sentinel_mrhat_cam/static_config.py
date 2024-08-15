import os
import logging

# Configuration file paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_CONFIG_PATH = os.path.join(SCRIPT_DIR, 'log_config.yaml')
CONFIG_PATH = os.path.join(SCRIPT_DIR, 'config.json')
TEMP_CONFIG_PATH = os.path.join(SCRIPT_DIR, 'temp_config.json')
STATE_FILE_PATH = os.path.join(SCRIPT_DIR, 'state_file.json')

# MQTT Configuration
BROKER = "debian.local"
# BROKER = "192.168.0.102"
PORT = 1883
IMAGETOPIC = "mqtt/rpi/image"
CONFIGACKTOPIC = "er-edge/confirm"
CONFIGSUBTOPIC = "config/er-edge"
QOS = 2
USERNAME = "er-edge"
PASSWORD = "admin"

# App configuration
"""
if  `period` < **SHUTDOWN_THRESHOLD** :
    The device won't shut down, instead it will wait in the script.

if  `period` > **SHUTDOWN_THRESHOLD** :
    The device shuts down in between picture taking.
"""
SHUTDOWN_THRESHOLD = 70
"""
This is the default time in seconds that, the he Pi takes to shutdown, and then to boot again.
"""
DEFAULT_BOOT_SHUTDOWN_TIME = 30
"""
This is the minimum value for `period` in seconds.
"""
MINIMUM_WAIT_TIME = 5
"""
This is the maximum value for `period` in seconds.
"""
MAXIMUM_WAIT_TIME = 10800

# Log configuration
LOGGING_TOPIC = "er-edge/logging"
LOG_LEVEL = logging.DEBUG
