#!/bin/bash

#ip addr show wlan0 | grep -Po 'inet \K[\d.]+'

# Backup command
#ip -f inet addr show wlan0 | grep -Po 'inet \K[\d.]+'

#sed -e 's/\("opena3xx-peripheral-api-ip"\:\)\("\)\(value1\)/\1New\2/g' filename
#sed -e 's/\(key1\=\)\(Old\)\(value1\)/\1New\2/g' filename

ipAddr=$(ip -f inet addr show wlan0 | grep -Po 'inet \K[\d.]+')

sed -i '/opena3xx-peripheral-api-ip/s/: .*/: "$ipAddr",' /home/pi/opena3xx.hardware.controller/configuration/configuration.json

#sh -c "grep -qxF '"opena3xx-peripheral-api-ip": ' /home/pi/opena3xx.hardware.controller/configuration/configuration.json || echo | ip addr show wlan0 | grep -Po 'inet \K[\d.]+' >> /boot/config.txt"
