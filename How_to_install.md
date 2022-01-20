These are some temporary instructions. They may not make sense until I write them up properly.
For now, they are just my reference notes.

1) Create Raspbian light install on SD card
2) Add 'ssh' and 'wpa_supplicant.conf' files to root folder of SD card.
    (Where wpa file has been updated with users own wireless settings)
3) connect to pi and run:
sudo apt-install git
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install python
sudo apt install python3-pip

git clone https://github.com/OpenA3XX/opena3xx.hardware.controller.git

Navigate to setup folder and run
sudo chmod +x setup.sh
./setup.sh

sudo reboot