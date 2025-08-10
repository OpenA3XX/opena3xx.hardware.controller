#!/bin/bash
fswatch -o . | while read f; do
  rsync -avz \
    --exclude '__pycache__' \
    --exclude '.git' \
    --exclude '.gitignore' \
    --exclude '.gitattributes' \
    --exclude '.idea' \
    --exclude '.vscode' \
    ./ pi@192.168.0.23:/home/pi/Documents/opena3xx-debugging
done