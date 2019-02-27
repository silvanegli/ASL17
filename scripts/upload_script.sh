#!/bin/bash

#for th in {1..3}; do
#    #add parameters to the command
#    scp setup_vm_memtier.sh siegliasl$th.westeurope.cloudapp.azure.com:
#    ssh siegli@siegliasl$th.westeurope.cloudapp.azure.com "sudo sh /home/siegli/setup_vm_memtier.sh" &
#done

#for th in {4..5}; do
    #add parameters to the command
#    scp setup_vm_mw.sh siegliasl$th.westeurope.cloudapp.azure.com:
#    ssh siegli@siegliasl$th.westeurope.cloudapp.azure.com "sudo sh /home/siegli/setup_vm_mw.sh" &
#done

#for th in {6..8}; do
    #add parameters to the command
#    scp setup_vm.sh siegliasl$th.westeurope.cloudapp.azure.com:
#    ssh siegli@siegliasl$th.westeurope.cloudapp.azure.com "sudo sh /home/siegli/setup_vm.sh" &
#done

for th in {1..8}; do
    #add parameters to the command
    #scp hosts siegliasl$th.westeurope.cloudapp.azure.com:
    #ssh siegli@siegliasl$th.westeurope.cloudapp.azure.com "sudo mv hosts /etc/hosts" &
    #ssh siegli@siegliasl$th.westeurope.cloudapp.azure.com "sudo apt-get update -y" 
    #ssh siegli@siegliasl$th.westeurope.cloudapp.azure.com "sudo apt-get autoremove -y" 
    #ssh siegli@siegliasl$th.westeurope.cloudapp.azure.com "sudo apt-get upgrade -y" &
    ssh siegli@siegliasl$th.westeurope.cloudapp.azure.com "sudo -- sh -c 'apt-get update; apt-get upgrade -y; apt-get dist-upgrade -y; apt-get autoremove -y; apt-get autoclean -y'" &
done
                                                    
