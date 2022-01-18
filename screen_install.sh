#!/bin/bash

# setup screen
PIDIR="/home/pi/"
cd $PIDIR
DIR="/home/pi/Downloads/LCD-show"
if [ ! -d "$DIR" ]; then
  cd $PIDIR
  # add autostart
  sudo mkdir --parents /etc/xdg/lxsession/LXDE-pi
  sudo cp dtfm/backend/random/autostart /etc/xdg/lxsession/LXDE-pi/autostart


  sudo apt-get update
  #sudo apt-get upgrade
  # Take action if $DIR not exists. #
  echo "Setting up touchscreen..."
  git clone https://github.com/goodtft/LCD-show.git
  chmod -R 755 LCD-show
  cd LCD-show/
  sudo ./LCD35-show 180
fi
