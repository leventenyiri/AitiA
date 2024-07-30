# AitiA

Detecting starling swarms.

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Fleventenyiri%2FAitiA%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/leventenyiri/AitiA/blob/python-coverage-comment-action-data/htmlcov/index.html)

## To-Do List

- [ ] **Camera**
  - Arducam 16 mpx Autofocus Camera
  - Camera setup: https://docs.arducam.com/Raspberry-Pi-Camera/Native-camera/16MP-IMX519/#hardware-connection
  - Libcamera documentation: https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf
     
- [ ] **MQTT**
  - Tutorial: https://www.emqx.com/en/blog/how-to-use-mqtt-in-python
  - Clients: https://www.emqx.com/en/mqtt-client-sdk?language=Python

- [ ] **RTC**
  - Setup: https://forums.raspberrypi.com/viewtopic.php?t=85683&sid=cf6676b19d36bf0d5bb0709b0152a900

- [ ] **Workflow**
  - Unit tests -> Integration tests -> Sytem tests
  - Workflow, setup.py files
  - CI
    
- [ ] **Optimizing**
  - Power consumption: https://raspberrypi.stackexchange.com/questions/92138/power-rpi-from-a-battery-on-off-via-ui-or-sleep https://www.cnx-software.com/2021/12/09/raspberry-pi-zero-2-w-power-consumption/
  - Boot: https://forums.raspberrypi.com/viewtopic.php?t=241455 https://forums.raspberrypi.com/viewtopic.php?t=339114 https://forums.raspberrypi.com/viewtopic.php?f=29&t=25777 https://www.freedesktop.org/software/systemd/man/latest/systemd-analyze.html

  - Right now running a light OS, weed out unnecessary processes (boot time around ~1min)
  - Goal: ~1week of runtime using a 5000mAh battery and solar panel

- [ ] **Case**
  - 3D printed
  - Lens shouldnt get foggy, account for weather

- [ ] **Random TODOS**
  - Unit, integration testing ✅
  - Implementing periodic running: -> with shut down, and without shut down ✅
  - Optimizing the OS boot time ✅
  - If RTC and internal time doesn't match ask for time set
  - Improving bash script
  - Add extra data to the published message (battery charge level, battery temperature) ✅
  - Packaging the software -> creating the Raspberry os image
    
- [ ] **Effective Range dependencies**
  - RTC wake up API
  - shutdown API
  - battery charging driver ✅
  - 3D case and battery case
  - battery warning-level monitoring script -> change device mode if the battery is to low
  - battery costumization

Roadmap:
https://github.com/users/borditamas/projects/2/views/4

Storage repo:
https://github.com/bnyitrai03/rpizero_storage

🚫 Need to invert the logic for syncing the RTC in prod !4!!!
