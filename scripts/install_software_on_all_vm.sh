#!/bin/bash
source ./functions.sh

if check_if_machines_down ${all[@]}; then
    ./startVms.sh aslvm1 aslvm2 aslvm3 aslvm4 aslvm5 aslvm6 aslvm7 aslvm8
    if [ "$?" == "1" ]; then
        echo "Starting VM's Failed!"
        exit 1
    fi
else
    echo "machines are already running !"
fi

wait_for_process_startup "ssh" ${all_machines[@]}

execute_on_all "sudo apt update -y"
execute_on_all "sudo apt install $1 -y"


./stopVms.sh aslvm1 aslvm2 aslvm3 aslvm4 aslvm5 aslvm6 aslvm7 aslvm8


