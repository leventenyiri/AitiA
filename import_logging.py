import logging.config
import os

# logging.config.dictConfig(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log_config.yaml'))

logging.basicConfig(level=logging.DEBUG)

log_data = {
    "timestamp": "datetime.now().isoformat()",
    "cpu_temp": "cpu_temp",
    "battery_percentage": 1,
    "battery_voltage_now": 10,
    "battery_voltage_avg": 100,
    "battery_current_now": 1000000,
    "battery_current_avg": 1000000,
    "charger_voltage_now": 1000000,
    "charger_current_now": 1000000
}

logging.info(f"{log_data}")
