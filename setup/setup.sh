#!/bin/bash

echo "

   ____                                 ____ __   ____   __
  / __ \                         /\    |___ \\ \ / /\ \ / /
 | |  | | _ __    ___  _ __     /  \     __) |\ V /  \ V / 
 | |  | || '_ \  / _ \| '_ \   / /\ \   |__ <  > <    > <  
 | |__| || |_) ||  __/| | | | / ____ \  ___) |/ . \  / . \ 
  \____/ | .__/  \___||_| |_|/_/    \_\|____//_/ \_\/_/ \_\
  _    _ | |              _                                
 | |  | ||_|             | |                               
 | |__| |  __ _  _ __  __| |__      __ __ _  _ __  ___     
 |  __  | / _` || '__|/ _` |\ \ /\ / // _` || '__|/ _ \    
 | |  | || (_| || |  | (_| | \ V  V /| (_| || |  |  __/    
 |_|  |_| \__,_||_|   \__,_|  \_/\_/  \__,_||_|   \___|    
   _____               _                _  _               
  / ____|             | |              | || |              
 | |      ___   _ __  | |_  _ __  ___  | || |  ___  _ __   
 | |     / _ \ | '_ \ | __|| '__|/ _ \ | || | / _ \| '__|  
 | |____| (_) || | | || |_ | |  | (_) || || ||  __/| |     
  \_____|\___/ |_| |_| \__||_|   \___/ |_||_| \___||_|     
                                                           
                                                           

"

# Add the required pin data to the startup config.
sh -c "grep -qxF 'gpio=4=op,dh' /boot/config.txt || echo 'gpio=4=op,dh' >> /boot/config.txt"
sh -c "grep -qxF 'gpio=5=op,dh' /boot/config.txt || echo 'gpio=5=op,dh' >> /boot/config.txt"
sh -c "grep -qxF 'gpio=6=op,dh' /boot/config.txt || echo 'gpio=6=op,dh' >> /boot/config.txt"
sh -c "grep -qxF 'gpio=18=op,dh' /boot/config.txt || echo 'gpio=18=op,dh' >> /boot/config.txt"

# Add permissions to allow an uninstall later, should it be required.
chmod +x uninstall.sh

# Commented out the 'git clone' because we have already downloaded very recently at this stage.
# Updates can be added in again at a later date, near V1 release.
#git clone https://github.com/OpenA3XX/opena3xx.hardware.controller.git /home/pi/opena3xx.hardware.controller

# Change to the main software directory
cd /home/pi/opena3xx.hardware.controller

# Create and start the loading spinner
#spin()
#{
#  spinner="/|\\-/|\\-"
#  while :
#  do
#    for i in `seq 0 7`
#    do
#      echo -n "${spinner:$i:1}"
#      echo -en "\010"
#      sleep 1
#    done
#  done
#}
#echo "Checking for updates, please wait"
#spin &
#SPIN_PID=$!
#trap "kill -9 $SPIN_PID" `seq 0 15`

# Install the required libraries
chmod +x progress.sh
./progress.sh
pip3 install -r requirements.txt

# Remove any existing version of the start up service (if it exists)
rm /lib/systemd/system/opena3xx-hardware-controller.service
echo "If a 'Could not remove because it does not exist' message is above, this is ok."

# Set permissions to write the startup service to the system directory
chmod a+rwx /lib/systemd/system

# Write our service file, and put it in the system directory
echo "
[Unit]
Description=OpenA3XX Digital Hardware Controller Board
After=multi-user.target

[Service]
Type=idle
WorkingDirectory=/home/pi/
User=pi
ExecStart=sh /home/pi/opena3xx.hardware.controller/start.sh
Restart=always

[Install]
WantedBy=multi-user.target" >> /lib/systemd/system/opena3xx-hardware-controller.service

# Set read permissions for the newly created service, reload the daemon and then enable the newly created service
chmod 644 /lib/systemd/system/opena3xx-hardware-controller.service
systemctl daemon-reload
systemctl enable opena3xx-hardware-controller.service

# End the installer.
echo "Finished."
