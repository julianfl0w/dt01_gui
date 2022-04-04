#!/bin/bash

export DISPLAY=:0

#DIR="/home/pi/dtfm"
#if [ ! -d "$DIR" ]; then
#  # Take action if $DIR not exists. #
#  echo "Downloading synth code..."
#  git clone https://github.com/julianfl0w/dt01_gui
#fi
#
#cd $DIR
#conda install -y anaconda-client
#conda config --add channels rpi
##conda install -y python=3.8
#conda create --name synth
#source activate synth
#conda install -y --file requirements.txt
#sudo apt-get install python3-venv 
#sudo apt-get install aptitude

#cd ~
#python3 -m venv dtfm
#cd dtfm
#source bin/activate
#cd $DOWNLOADS
#git clone https://github.com/tranter/raspberry-pi-qt-builds
#sudo bash raspberry-pi-qt-builds/build-qt.sh

 
#sudo apt-get install sip-dev
#sudo apt-cache search qt | grep -oE "(^(lib)?qt[^ ]*5[^ ]*)" > packages.txt
#cat packages.txt | xargs sudo aptitude install -y
#pip3 install --upgrade pip setuptools
#sudo apt-get install -y qtcreator python3-pyqt5
#sudo apt-get install pyqt5-dev
#python3 -m pip install --upgrade pip

sudo apt-get install -y onboard
#sudo apt-get install -y network-manager << BREAKS THE SYSTEM?
sudo apt-get install -y libasound2-dev
sudo apt-get install -y libjack-dev
sudo apt install -y python3-pyqt5
#sudo apt-get install -y xdotool 
# only do these copies here. boot info for RPI

#to change hostname:
#sudo vim /etc/hosts
#sudo vim /etc/hostname


DIR="/home/pi/dtfm"
#sudo cp $DIR/backend/random/cmdline.txt /boot/cmdline.txt
#sudo cp $DIR/backend/random/config.txt /boot/config.txt

# configure autostart
mkdir -p /home/pi/.config/autostart/
sudo cp $DIR/backend/random/dt01.desktop /home/pi/.config/autostart/
sudo chmod +x /home/pi/.config/autostart/*

#remove top panel
#Edit the file /etc/xdg/lxsession/LXDE-pi/autostart
#comment out the line @lxpanel --profile LXDE-pi with # symbol
    
# disable desktop wizard
sudo rm /etc/xdg/autostart/piwiz.desktop

chmod 777 $DIR/startscript.sh

pip install -r requirements_user.txt
sudo pip install -r requirements_sudo.txt

#pwd
