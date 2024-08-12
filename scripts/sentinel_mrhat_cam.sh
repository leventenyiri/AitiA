#!/bin/bash

# Log file path
LOG_FILE="/home/admin/bash_script.log"

# Redirect all output to the log file
exec > >(tee -a "$LOG_FILE") 2>&1

echo "Starting bash script at $(date)"

# Set the working directory
cd /home/admin
echo "Current working directory: $(pwd)"

# Ensure the correct Python environment is used
export PATH="/usr/local/bin:$PATH"
echo "Python path: $(which python3)"
echo "Python version: $(python3 --version)"

# Print out environment variables
echo "Environment variables:"
env

# Configuration
RESTART_COUNT_FILE="/tmp/restart_count"

# Initialize restart count
if [ -f "$RESTART_COUNT_FILE" ]; then
    RESTART_COUNT=$(cat "$RESTART_COUNT_FILE")
else
    RESTART_COUNT=0
fi

# Main loop
while true; do
    start_time=$(date +%s)
    echo "Starting Python script at $(date)"
    # Run the Python script
    python3 -m sentinel_mrhat_cam.main
    EXIT_CODE=$?
    
    end_time=$(date +%s)
    runtime=$((end_time - start_time))
    echo "Python script exited with code $EXIT_CODE after $runtime seconds"

    # Handle different exit codes
    case $EXIT_CODE in
        0)
            echo "Script exited normally with code 0. Shutting down..."
            RESTART_COUNT=0
            echo "$RESTART_COUNT" > "$RESTART_COUNT_FILE"
            exit 0
            ;;
        1)
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
            ;;
        2)
            echo "Script exited with code 2. Rebooting system..."
            sudo reboot
            ;;
        *)
            echo "Script exited with unexpected code $EXIT_CODE. Rebooting system..."
            sudo reboot
            ;;
    esac
done