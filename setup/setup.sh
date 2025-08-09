#!/bin/bash

GREEN='\033[0;32m'
BLUE='\033[1;34m'
RED='\033[0;31m'
NC='\033[0m'

# Start the installer
echo -e "${GREEN}Welcome to OpenA3XX! I'm just installing some required packages, please wait.${NC}"

# Print logo to terminal
sudo apt install figlet &> /dev/null
# sudo apt install lolcat &> /dev/null
sudo apt install lolcat
echo -e "${GREEN}OK, let's start the install!${NC}"

sudo apt-get update
sudo apt-get install -y python3-lgpio python3-libgpiod gpiod
Ensure the service user is in the gpio group: id; if not: sudo adduser pi gpio; reboot

figlet "OpenA3XX Hardware Controller" | /usr/games/lolcat -f

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
chmod +rwx start.sh

# Obtain the Board ID number from the user
echo -e "${GREEN}I need to know which board number this is please.${NC}"
echo -e "${GREEN}If this is the first board you're setting up, please enter ${BLUE}'1'${GREEN} below and hit ${BLUE}'Enter'${GREEN}. ${NC}"
echo -e "${GREEN}Otherwise, enter the next free board number in your setup, and then hit ${BLUE}'Enter'${GREEN}. ${NC}"
boardIDNum=""
while [[ ! $boardIDNum =~ ^[0-9]{1,4}$ ]] 
do
  echo -e "${GREEN}Please enter a number between ${RED}0${GREEN} and ${RED}9999 ${NC}"
  read boardIDNum
done
echo -e "${GREEN}Thanks! I'll make this board number ${BLUE} $boardIDNum ${GREEN} ! ${NC}"
echo "python3 /home/pi/opena3xx.hardware.controller/main.py --hardware-board-id=$boardIDNum" >> /home/pi/opena3xx.hardware.controller/start.sh

# Create and start the loading spinner
spin()
{
  spinner="/|\\-/|\\-"
  while :
  do
    for i in `seq 0 7`
    do
      echo -n "${spinner:$i:1}"
      echo -en "\010"
      sleep 1
    done
  done
}
echo -e "${GREEN}Checking for updates, ${RED}please wait!${GREEN} This may take some time, especially on first install.${NC}"
spin &
SPIN_PID=$!
trap "kill -9 $SPIN_PID" `seq 0 15`

# Install the required libraries
pip3 install -r requirements.txt

# Remove any existing version of the start up service (if it exists)
rm /lib/systemd/system/opena3xx-hardware-controller.service 2> /dev/null
#echo -e "${GREEN}If a ${BLUE}'No such file or directory'${GREEN} message is above, this is ok.${NC}"
echo "-"

# Write files to the startup to ensure the application runs automatically
echo -e "${GREEN}Writing startup files${NC}"

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
figlet "Install complete!" | /usr/games/lolcat -f
echo -e "${GREEN}Please now continue with the remaining install directions from the ${BLUE}'How To Install'${GREEN} document if you're following the step-by-step guide.${NC}"
