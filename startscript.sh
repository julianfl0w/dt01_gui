# run sudo cp dt01.desktop /home/pi/.config/autostart/
# then 
# run chmod +x /home/pi/.config/autostart/*
export DISPLAY=:0
python3 /home/pi/dt01_gui/kinetic.py &
