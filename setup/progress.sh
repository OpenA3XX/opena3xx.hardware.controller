phases=( 
    'Checking in to Terminal'
    'Weighing lugagge'
    'Security & Passport control'
    'Now boarding'
)   

for i in $(seq 1 100); do  
    sleep 1.0

    if [ $i -eq 100 ]; then
        echo -e "XXX\n100\nReady for takeoff!\nXXX"
    elif [ $(($i % 25)) -eq 0 ]; then
        let "phase = $i / 25"
        echo -e "XXX\n$i\n${phases[phase]}\nXXX"
    else
        echo $i
    fi 
done | whiptail --title 'OpenA3XX Hardware Controller' --gauge "${phases[0]}" 6 60 0
