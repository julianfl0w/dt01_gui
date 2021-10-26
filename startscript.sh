#!/bin/bash
# run sudo cp dt01.desktop /home/pi/.config/autostart/
# then 
# run chmod +x /home/pi/.config/autostart/*

export DISPLAY=:0

#parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
#cd "$parent_path"
sudo python3 /home/pi/dt01_gui/clearspi.py # start over the spi
sudo taskset 0x00000004 sudo python3 /home/pi/dt01_gui/startup.py &
export STARTED=1
python3 /home/pi/dt01_gui/kinetic.py &
#sudo taskset 0x00000004 sudo python3 startup.py &
