grep -qxF 'gpio=4=op,dh' /boot/config.txt || echo 'gpio=4=op,dh' >> /boot/config.txt
grep -qxF 'gpio=5=op,dh' /boot/config.txt || echo 'gpio=5=op,dh' >> /boot/config.txt
grep -qxF 'gpio=6=op,dh' /boot/config.txt || echo 'gpio=6=op,dh' >> /boot/config.txt
grep -qxF 'gpio=18=op,dh' /boot/config.txt || echo 'gpio=18=op,dh' >> /boot/config.txt

git clone https://github.com/OpenA3XX/opena3xx.hardware.controller.git /home/pi/opena3xx.hardware.controller
cd /home/pi/opena3xx.hardware.controller
pip install -r requirements.txt

rm /lib/systemd/system/opena3xx.hardware.controller.service
echo "
[Unit]
Description=OpenA3XX Digital Hardware Controller Board
After=multi-user.target

[Service]
WorkingDirectory=/home/pi/
User=pi
ExecStart=sh /home/pi/opena3xx.hardware.controller/start.sh
Restart=always

[Install]
WantedBy=multi-user.target" >> /lib/systemd/system/opena3xx.hardware.controller.service
