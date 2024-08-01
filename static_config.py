import os

# Configuration file paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_CONFIG_PATH = os.path.join(SCRIPT_DIR, 'log_config.yaml')
CONFIG_PATH = os.path.join(SCRIPT_DIR, 'config.json')
TEMP_CONFIG_PATH = os.path.join(SCRIPT_DIR, 'temp_config.json')

# MQTT Configuration
BROKER = "192.168.0.105"
PORT = 1883
PUBTOPIC = "mqtt/rpi/image"
CONFIGTOPIC = "er-edge/confirm"
SUBTOPIC = "settings/er-edge"
QOS = 2
USERNAME = "er-edge-3c547181"
PASSWORD = "admin"

# App configuration
SHUTDOWN_THRESHOLD = 60  # in seconds
DEFAULT_BOOT_SHUTDOWN_TIME = 30  # in seconds
MINIMUM_WAIT_TIME = 5  # in seconds
