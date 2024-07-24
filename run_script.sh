#!/bin/bash

# Redirect all output to a log file
exec > >(tee -a /home/admin/MQTT/bash_script.log) 2>&1

echo "Starting bash script at $(date)"

# Function to read Python config
read_config() {
    python3 -c "from static_config import $1; print($1)"
}

# Read MQTT broker and port from config
BROKER=$(read_config "BROKER")
PORT=$(read_config "PORT")

check_mqtt() {
    nc -z -w 5 $BROKER $PORT
}

# Function to check MQTT broker connectivity with retries
check_mqtt_with_retry() {
    local max_attempts=12
    local attempt=1
    while [ $attempt -le $max_attempts ]; do
        echo "$(date '+%Y-%m-%d %H:%M:%S') - MQTT broker check attempt $attempt of $max_attempts"
        if check_mqtt; then
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 5
    done
    echo "$(date '+%Y-%m-%d %H:%M:%S') - MQTT broker check failed after $max_attempts attempts"
    return 1
}

echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting MQTT broker checks"
if ! check_mqtt_with_retry; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Failed to connect to MQTT broker. Exiting."
    exit 1
fi
echo "$(date '+%Y-%m-%d %H:%M:%S') - MQTT broker is reachable"

# Set the working directory
cd /home/admin/MQTT
echo "Current working directory: $(pwd)"

# Ensure the correct Python environment is used
export PATH="/usr/local/bin:$PATH"
echo "Python path: $(which python3)"
echo "Python version: $(python3 --version)"

# Set up logging directory with correct permissions
LOGDIR="/home/admin/MQTT/logs"
mkdir -p "$LOGDIR"
chown admin:admin "$LOGDIR"
echo "Log directory: $LOGDIR"
ls -l "$LOGDIR"

# Print out environment variables
echo "Environment variables:"
env

# Path to your Python script
PYTHON_SCRIPT="/home/admin/MQTT/client.py"
RESTART_COUNT_FILE="/tmp/restart_count"

if [ -f "$RESTART_COUNT_FILE" ]; then
    RESTART_COUNT=$(cat "$RESTART_COUNT_FILE")
else
    RESTART_COUNT=0
fi

env > /tmp/daemon_env.log

while true; do
    start_time=$(date +%s)
    echo "Starting Python script at $(date)"
    python3 $PYTHON_SCRIPT
    end_time=$(date +%s)

    runtime=$((end_time - start_time))
    EXIT_CODE=$?

    echo "Python script exited with code $EXIT_CODE after $runtime seconds"

    if [ $EXIT_CODE -eq 0 ]; then
        echo "Script exited normally with code 0. Shutting down..."
        RESTART_COUNT=0
        echo "$RESTART_COUNT" > "$RESTART_COUNT_FILE"
        exit 0
    elif [ $EXIT_CODE -eq 1 ]; then
        if [ $runtime -ge 600 ]; then
            echo "Script ran for 10+ minutes. Resetting restart count."
            RESTART_COUNT=0
        else
            RESTART_COUNT=$((RESTART_COUNT + 1))
        fi

        echo "$RESTART_COUNT" > "$RESTART_COUNT_FILE"

        if [ $RESTART_COUNT -ge 5 ]; then
            echo "Restarted 5 consecutive times. Rebooting system..."
            sudo reboot
        else
            echo "Script exited with code 1. Restarting Python script (Restart count: $RESTART_COUNT)..."
            continue
        fi
    elif [ $EXIT_CODE -eq 2 ]; then
        echo "Script exited with code 2. Rebooting system..."
        sudo reboot
    else
        echo "Script exited with unexpected code $EXIT_CODE. Rebooting system..."
        sudo reboot
    fi
done