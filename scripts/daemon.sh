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
ExecStart=/bin/bash /home/admin/sentinel_mrhat_cam.sh
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF"

# Reload the systemd daemon
sudo systemctl daemon-reload

# Enable the service to start on boot (rather do this manually, enabling it right away could cause problems)
# sudo systemctl enable sentinel_mrhat_cam.service

# sudo systemctl disable sentinel_mrhat_cam.service

# Optional: Start the service immediately
# sudo systemctl start sentinel_mrhat_cam.service

echo "Service has been created successfully, enable it and reboot the system for the changes to take effect."