# AitiA

Detecting starling swarms.

## To-Do List

- [ ] **Camera used for testing**
  - Arducam 16 mpx Autofocus Camera
  - Camera setup: https://docs.arducam.com/Raspberry-Pi-Camera/Native-camera/16MP-IMX519/#hardware-connection
  - Libcamera documentation: https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf

- [ ] **Network folder sharing for communication with server**
    
- [ ] **Write python code**
  - Unit tests
  - Workflow, setup.py files
  - CI/CD?
  - MQTT tutorial: https://www.emqx.com/en/blog/how-to-use-mqtt-in-python
  - MQTT clients: https://www.emqx.com/en/mqtt-client-sdk?language=Python
    
- [ ] **Optimizing**
  - Power consumption: https://raspberrypi.stackexchange.com/questions/92138/power-rpi-from-a-battery-on-off-via-ui-or-sleep
  - Boot: https://forums.raspberrypi.com/viewtopic.php?t=241455 https://forums.raspberrypi.com/viewtopic.php?t=339114 https://forums.raspberrypi.com/viewtopic.php?f=29&t=25777
  - Right now running a light OS, weed out unnecessary processes (boot time around ~1min)
  - Goal: ~1week of runtime using a 5000mAh battery and solar panel

- [ ] **Case**
  - 3D printed
  - Lens shouldnt get foggy, account for weather

- [ ] **RTC**
      - Setup: https://forums.raspberrypi.com/viewtopic.php?t=85683&sid=cf6676b19d36bf0d5bb0709b0152a900

- [ ] **Random TODOS**
  - Measure the current drawn
  - Send information about the device (temperature, battery, ...)
  - Unit, integration testing
  - CI pipeline optimizing
  - Implementing periodic running
  - Optimizing the OS boot time

Roadmap:
https://github.com/users/borditamas/projects/2/views/4

Boot time measuring help:
https://www.freedesktop.org/software/systemd/man/latest/systemd-analyze.html
