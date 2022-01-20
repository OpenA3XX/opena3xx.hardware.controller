#!/bin/bash

ipAddr=$(ip -f inet addr show wlan0 | grep -Po 'inet \K[\d.]+')
sed -i '/opena3xx-peripheral-api-ip/s/: .*/: "'$ipAddr'",/' /home/pi/opena3xx.hardware.controller/configuration/configuration.json
