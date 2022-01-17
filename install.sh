#!/bin/bash

# setup screen
DOWNLOADS="/home/pi/Downloads"
cd $DOWNLOADS
DIR="/home/pi/Downloads/LCD-show"
if [ ! -d "$DIR" ]; then
  # add autostart
  sudo echo "@/home/pi/dtfm/startscript.sh" > /etc/xdg/lxsession/LXDE-pi/autostart


  sudo apt-get update
  sudo apt-get upgrade
  # Take action if $DIR not exists. #
  echo "Setting up touchscreen..."
  sudo rm -rf LCD-show
  git clone https://github.com/goodtft/LCD-show.git
  chmod -R 755 LCD-show
  cd LCD-show/
  sudo ./LCD35-show 180
fi

#cd $DOWNLOADS
#if ! type conda &> /dev/null; then
#  # install anaconda
#  wget http://repo.continuum.io/miniconda/Miniconda3-latest-Linux-armv7l.sh
#  sudo md5sum Miniconda3-latest-Linux-armv7l.sh # (optional) check md5
#  sudo chmod 777 /bin/bash Miniconda3-latest-Linux-armv7l.sh
#  /bin/bash Miniconda3-latest-Linux-armv7l.sh -b -f # -> change default directory to /home/pi/miniconda3
#  echo "export PATH=\"/home/pi/miniconda3/bin:$PATH\"" >> /home/pi/.bashrc # add to path
#  #sudo reboot -h now
#  conda install -y anaconda-client
#  
#fi

cd ..

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
sudo apt-get install -y network-manager
sudo apt-get install -y libasound2-dev
sudo apt-get install -y libjack-dev
sudo apt-get install -y xdotool 
# only do these copies here. boot info for RPI

#to change hostname:
#sudo vim /etc/hosts
#sudo vim /etc/hostname


DIR="/home/pi/dtfm"
#sudo cp $DIR/random/cmdline.txt /boot/cmdline.txt
#sudo cp $DIR/random/config.txt /boot/config.txt

# configure autostart
mkdir -p /home/pi/.config/autostart/
sudo cp $DIR/random/dt01.desktop /home/pi/.config/autostart/
sudo chmod +x /home/pi/.config/autostart/*

#remove top panel
#Edit the file /etc/xdg/lxsession/LXDE-pi/autostart
#comment out the line @lxpanel --profile LXDE-pi with # symbol
    
# disable desktop wizard
sudo rm /etc/xdg/autostart/piwiz.desktop

chmod 777 $DIR/startscript.sh
#pwd
