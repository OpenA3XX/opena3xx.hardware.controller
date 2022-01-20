cd /home/pi

sudo systemctl stop opena3xx-hardware-controller.service

sudo systemctl disable opena3xx-hardware-controller.service

sudo rm -rf opena3xx.hardware.controller

sudo rm /lib/systemd/system/opena3xx-hardware-controller.service

sudo systemctl daemon-reload