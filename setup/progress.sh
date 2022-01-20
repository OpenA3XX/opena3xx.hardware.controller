#!/bin/bash
# Keep checking if the process is running. And keep a count.
{
        percentage="0"
        while (true)
        do
            proc=$(ps aux | grep -v grep | grep -e "pip3")
            if [[ "$proc" == "" ]] && [[ "$percentage" -eq "0" ]];
            then
                # Nothing to do as the process was not running when we
                # started the script.
                break;
            elif [[ "$proc" == "" ]] && [[ "$percentage" -gt "0" ]];
            then
                # The process has finished. It is no longer running.
                # So slowly count the percentage down to 100%.
                sleep 2
                echo 98
                sleep 1
                echo 99
                sleep 1
                echo 100
                sleep 1
                break;
            elif [[ "51" -eq "$percentage" ]]
            then
                # The process is running and taking really long.
                # Instead of running up to # 100% we instead reach 50% and
                # reset the percentage count back to 30%.
                # Now that we are back at 30% we can start counting again.
                # We will keep looping here forever until the running process stops.
                percentage="30"
            fi
            sleep 1
            echo $percentage
            percentage=$(expr $percentage + 1)
        done
} | whiptail --title "OpenA3XX" --gauge "Installing required libraries..." 6 50 0
