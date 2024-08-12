"""
Welcome to the documentation. 🐦

[Project Homepage](https://github.com/Aitia-IIOT/sentinel-mrhat-cam)

## How it works?

### Overview

TODO

## Login
#### Example of ssh using ip address:
Connect the device to the PC using the USB-C port on the Hat and use a program like PuTTY to communicate through serial port. Check the device manager to see which COM port the device uses. Inside PuTTY it should look like this:

![Image of PuTTY](https://github.com/bnyitrai03/rpizero_storage/blob/main/PuTTY.png?raw=true)

(On windows for the serial line just write COM...)

Baud rate: 115200

Click on Open, click inside the window and press Enter. After a while it will ask for the username and the password, during testing: 

Password: admin

Username: admin

![Image of login](https://github.com/bnyitrai03/rpizero_storage/blob/main/PuTTY_Login.png?raw=true)

Write hostname -I, and you will get the ip address.

![Hostname](https://github.com/bnyitrai03/rpizero_storage/blob/main/PuTTY_Hostname.png?raw=true)

You can now log in using this ip address like so:

```bash
ssh admin@192.168.0.103
```

#### Example of ssh using mDNS:

Once you have successfully connected to the device you will know its name, you can also use this to log in, you just have to put .local after the name.
```bash
ssh admin@er-edge-16b9ac84.local
```

#### Example of ssh using key based [login](https://github.com/EffectiveRange/devc-effectiverange/wiki/Configuring-SSH-targets):
In the linked tutorial the name the Host myhost, you can name it however you like.
```bash
ssh myhost
```

## Running the script

By default the script is running automatically as soon as the device has booted up. This is thanks to a daemon, which is starting a bash script on boot. The bash script starts the python script, handles additional logging, and restarts the script or the device based on exit codes from the python script.

If you dont want the script to start on boot, then you have to disable the daemon responsible for that.

```bash
sudo systemctl disable run-script.service

sudo reboot
```

To make it start on boot:

```bash
sudo systemctl enable run-script.service

sudo reboot
```

You can also start the script manually.

Make sure you are in the home/admin folder.
```bash
cd
```
Then run the bash script.
```bash
bash run_script.sh
```

As its running itt will create a bash_log.txt and a hardware_log.txt file in the home/admin folder on the Pi. The bash_log contains information about whats happening within the script and the hardware_log, as the name suggests lets us know about specifics of the hardware, like CPU temperature and battery voltage... 

If for some reason you want to run the python script straight up, you can do that too.
```bash
python3 -m sentinel_mrhat_cam.main
```

Be aware, that this way you will miss out on the bash_log and the hardware_log, it will also not handle the cases where the script exits with an exit code.


### Messaging

**Subscribe topic:** `{username}/config`

```
{
    "quality":"3K",
    "mode":"periodic",
    "period":60, // in sec
    "wakeUpTime":"06:00:00", // UTC
    "shutDownTime":"19:00:00" // UTC
}
```

- The device using a default configuration in case of config errors
- TODO more decription

**Publish topic:** `{username}/confirm`

`config-ok` OR `config-nok|{error desc}`

- TODO description

**Publish topic:** `{username}/image`

```
{
     "timestamp":"2024-07-11T18:52:05.179690+00:00",
     "image":"/9j/4AAQSkZJRgABAQAAAQAB...."
     "cpuTemp":35.6,
     "batteryTemp":48.5,
     "batteryCharge": 95
}
```

- TODO description

**Publish topic:** `{username}/log`

`log record text`

- TODO descriptions

## Hardware

![Prototype Schematic](https://github.com/bnyitrai03/rpizero_storage/blob/main/Protot%C3%ADpus%20rajz%20V1.3.png?raw=true)
"""

from .static_config import *
from .utils import *
from .logger import *
from .system import *
from .mqtt import *
from .schedule import *
from .app_config import *
from .camera import *
from .transmit import *
from .app import *
from .main import *
