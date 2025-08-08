#!/bin/bash
rsync -avz --exclude '__pycache__' ./ pi@192.168.0.23:/home/pi/Documents/opena3xx-debugging
#ssh pi@<pi-ip> "python3 /home/pi/myapp/main.py"