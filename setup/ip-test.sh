#!/bin/bash

ip addr show wlan0 | grep -Po 'inet \K[\d.]+'

# Backup command
#ip -f inet addr show wlan0 | grep -Po 'inet \K[\d.]+'
