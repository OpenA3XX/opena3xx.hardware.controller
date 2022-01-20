#!/bin/bash

sh -c "grep -qxF 'gpio=4=op,dh' /boot/config.txt || echo 'gpio=4=op,dh' >> /boot/config.txt"
sh -c "grep -qxF 'gpio=5=op,dh' /boot/config.txt || echo 'gpio=5=op,dh' >> /boot/config.txt"
sh -c "grep -qxF 'gpio=6=op,dh' /boot/config.txt || echo 'gpio=6=op,dh' >> /boot/config.txt"
sh -c "grep -qxF 'gpio=18=op,dh' /boot/config.txt || echo 'gpio=18=op,dh' >> /boot/config.txt"

chmod +x uninstall.sh

# Commented out the 'git clone' because we have already downloaded very recently at this stage.
# Updates can be added in again at a later date, near V1 release.
#git clone https://github.com/OpenA3XX/opena3xx.hardware.controller.git /home/pi/opena3xx.hardware.controller

cd /home/pi/opena3xx.hardware.controller

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
echo "Checking for updates, please wait"
spin &
SPIN_PID=$!
trap "kill -9 $SPIN_PID" `seq 0 15`

pip3 install -r requirements.txt

rm /lib/systemd/system/opena3xx-hardware-controller.service
chmod a+rwx /lib/systemd/system
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

chmod 644 /lib/systemd/system/opena3xx-hardware-controller.service
systemctl daemon-reload
systemctl enable opena3xx-hardware-controller.service

echo "Finished."
