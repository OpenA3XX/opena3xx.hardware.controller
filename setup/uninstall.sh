cd /home/pi

failed=false
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

sudo systemctl stop opena3xx-hardware-controller.service
if [ $? -eq 0 ]; then
   echo "${GREEN}Automatic start-up service stopped${NC}"
else
   echo "Failed to stop /lib/systemd/system/opena3xx-hardware-controller.service"
   failed=true
fi

sudo systemctl disable opena3xx-hardware-controller.service
if [ $? -eq 0 ]; then
   echo "${GREEN}Automatic start-up service disabled${NC}"
else
   echo "Failed to disable /lib/systemd/system/opena3xx-hardware-controller.service"
   failed=true
fi

sudo rm -rf opena3xx.hardware.controller
if [ $? -eq 0 ]; then
   echo "${GREEN}opena3xx.hardware.controller directory removed${NC}"
else
   echo "Failed to stop /lib/systemd/system/opena3xx-hardware-controller.service"
   failed=true
fi

sudo rm /lib/systemd/system/opena3xx-hardware-controller.service
if [ $? -eq 0 ]; then
   echo ""
else
   echo "Failed to stop /lib/systemd/system/opena3xx-hardware-controller.service"
   failed=true
fi

sudo systemctl daemon-reload
if [ $? -eq 0 ]; then
   echo "${GREEN}Daemon reloaded${NC}"
else
   echo "Failed to reload daemon"
   failed=true
fi

if [ $failed -eq true ]
then
    echo "There was an ${RED}error${NC} with the uninstall process. Please check the error message above."
    echo "If unable to manually resolve the problem, please contact a member of the OpenA3XX team."
else
    echo "${GREEN}OpenA3XX Hardware Controller uninstall successful${NC}"
fi
