cd /home/pi

figlet "OpenA3XX Uninstaller" | /usr/games/lolcat -f

failed=false
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

sudo systemctl stop opena3xx-hardware-controller.service 2> /dev/null
if [ $? -eq 0 ]; then
   echo "${GREEN}Automatic start-up service stopped${NC}"
else
   echo "${RED}Failed to stop /lib/systemd/system/opena3xx-hardware-controller.service${NC}"
   failed=true
fi

sudo systemctl disable opena3xx-hardware-controller.service 2> /dev/null
if [ $? -eq 0 ]; then
   echo "${GREEN}Automatic start-up service disabled${NC}"
else
   echo "${RED}Failed to disable /lib/systemd/system/opena3xx-hardware-controller.service${NC}"
   failed=true
fi

sudo rm -rf opena3xx.hardware.controller 2> /dev/null
if [ $? -eq 0 ]; then
   echo "${GREEN}opena3xx.hardware.controller directory removed${NC}"
else
   echo "${RED}Failed to remove opena3xx.hardware.controller directory${NC}"
   failed=true
fi

sudo rm /lib/systemd/system/opena3xx-hardware-controller.service 2> /dev/null
if [ $? -eq 0 ]; then
   echo "${GREEN}Automatic start-up service removed${NC}"
else
   echo "${RED}Failed to remove /lib/systemd/system/opena3xx-hardware-controller.service${NC}"
   failed=true
fi

sudo systemctl daemon-reload 2> /dev/null
if [ $? -eq 0 ]; then
   echo "${GREEN}Daemon reloaded${NC}"
else
   echo "${RED}Failed to reload daemon${NC}"
   failed=true
fi

if [ $failed = true ]
then
    echo "There was an ${RED}error${NC} with the uninstall process. Please check the error message above."
    echo "Uninstall may still have been successful, please check relevant folders. If in doubt, reflash SD card with new install/image."
    echo "If unable to manually resolve the problem, please contact a member of the OpenA3XX team."
else
    echo "${GREEN}OpenA3XX Hardware Controller uninstall successful${NC}"
fi

figlet "Uninstall complete!" | /usr/games/lolcat -f
