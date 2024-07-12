#!/bin/bash
set -e
scp $2 $1:/tmp/
modulefile="$(basename $2)"
modulename="${modulefile%.*}"
ssh $1 "sudo mv /tmp/'$modulefile' /lib/modules/\$(uname -r)/"
ssh $1 "if [[ -z \"\$(grep '$modulename' /etc/modules)\" ]];then sudo bash -c \"echo '$modulename' >> /etc/modules;echo 'options $modulename rpi_platform_generation=0'  > /etc/modprobe.d/snd.conf\";sudo depmod;sudo modprobe $modulename;fi"
ssh $1 "if [[ -z \"\$(grep -E '^dtparam=i2s=on' /boot/config.txt )\" ]];then sudo bash -c \"echo 'dtparam=i2s=on' >>  /boot/config.txt\";fi"
