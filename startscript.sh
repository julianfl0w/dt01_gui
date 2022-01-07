#!/bin/bash
# for autostart: 
# sudo echo "@/home/pi/dt_fm/startscript.sh" > /etc/xdg/lxsession/LXDE-pi/autostart

sudo killall python3

export DISPLAY=:0

#parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
#cd "$parent_path"
sudo python3 /home/pi/dt_fm/clearspi.py # start over the spi
export XAUTHORITY=/home/pi/.Xauthority
sudo taskset 0x00000004 sudo python3 /home/pi/dt_fm/patch.py &
python3 /home/pi/dt_fm/qt_layout.py &
export STARTED=1
