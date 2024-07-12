# Utility scripts for testing

to execute a `shutdown`  do
```bash
sudo ./shutdown_now
```
this will put the BQ IC in ship mode after 10 seconds or after the
charger is pulled out (battery required)  and also halts the PI
The PI can be restarted by pressing the BQQON button for ~3 seconds
(only when battery present for now)

to execute a `power-off` operation do
```bash
sudo ./shutdown_now shut
```
this will power off the system, and the only way to restart is to unplug and plug back 
the charger (again, only if operating from battery)
