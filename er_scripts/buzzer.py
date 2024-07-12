#!/usr/bin/env python

try:
    import gpiozero  # type: ignore
except ImportError:
    from unittest.mock import MagicMock

    class DigitalOutputDeviceMock:
        on = MagicMock()
        off = MagicMock()
        blink = MagicMock()

    class gpiozero:
        DigitalOutputDevice = MagicMock(return_value=DigitalOutputDeviceMock())

pin = gpiozero.DigitalOutputDevice(
            12, active_high=True, initial_value=False
        )
import time
import sys
import datetime

freq = float(sys.argv[1])
period = 1/freq
duty = int(sys.argv[2])
#pin.on()
#exit()
last = datetime.datetime.now()
currperiod = period
cnt = 4
while True:
  now  =datetime.datetime.now()
  if (now - last).seconds > 0.5:
     last = now
     currperiod = currperiod / 2
     cnt -= 1
     if not cnt:
       currperiod = period
       cnt = 4
  pin.on()
  time.sleep(currperiod*duty/100)
  pin.off()
  time.sleep(currperiod*(100-duty)/100)
