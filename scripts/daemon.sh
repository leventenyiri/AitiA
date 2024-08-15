#!/bin/bash

# Define the service file path
SERVICE_FILE="/etc/systemd/system/sentinel_mrhat_cam.service"

# Create the service file with the necessary content
sudo bash -c "cat > $SERVICE_FILE <<EOF
[Unit]
Description=Run Script Daemon

[Service]
Type=simple
User=admin
ExecStart=/bin/bash /usr/lib/python3/dist-packages/sentinel_mrhat_cam/scripts/sentinel_mrhat_cam.sh
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF"

# Reload the systemd daemon
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable sentinel_mrhat_cam.service

# Optional: Start the service immediately
# sudo systemctl start sentinel_mrhat_cam.service

echo "Service has been created and enabled successfully, reboot the system for the changes to take effect."