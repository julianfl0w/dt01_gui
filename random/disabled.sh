sudo systemctl disable hciuart.service            
#sudo systemctl disable dev-mmcblk0p2.device       
sudo systemctl disable raspi-config.service       
#sudo systemctl disable udisks2.service            
sudo systemctl disable rpi-eeprom-update.service  
sudo systemctl disable man-db.service             
sudo systemctl disable apt-daily-upgrade.service  
sudo systemctl disable apt-daily.service          
sudo apt purge --remove plymouth