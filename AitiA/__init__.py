"""
Welcome to the documentation. 🐦

[Project Homepage](https://github.com/Aitia-IIOT/sentinel-mrhat-cam)

# Sentinel MrHat Cam

## How it works?

### Overview

TODO

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
from .system import *
from .logger import *
from .mqtt import *
from .utils import *
from .schedule import *
from .app_config import *
from .camera import *
from .app import *
from .main import *
