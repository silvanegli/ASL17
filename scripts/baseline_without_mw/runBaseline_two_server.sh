#!/bin/bash
source ./functions.sh


time=60


#----------------------------------------------------------
output_dir="baseline_two_servers_$(date +"%Y-%m-%d-%H:%M")"
all_machines=("client1" "client2" "client3" "server1" "server2")
from=("client1" "client2" "client3")
to=("server1" "server2")


if check_if_machines_down ${all_machines[@]}; then
    ./startVms.sh aslvm1 aslvm2 aslvm3 aslvm6 aslvm7
    if [ "$?" == "1" ]; then
        echo "Starting VM's Failed!"
        exit 1
    fi
else
    echo "machines are already running !"
fi

wait_for_process_startup "ssh" ${all_machines[@]}

create_output_dir $output_dir ${all_machines[@]}

ping_test from to $output_dir

echo "running iperf tests"
iperf_test from to $output_dir

#vc=(1 4 8 12 16 20 24 28 32)
runs=(1 2 3)
vc=(1 4 8 12 16 20 24 28 32 40 48 56 64)

#vc=(1 10 32)
#runs=(1)
#vc=(1)
#runs=(1)

nof_exp_left=$((${#vc[@]} * ${#runs[@]}))

start_and_populate_servers 11211 "server1" "server2"

for run in "${runs[@]}"; do
    for c in "${vc[@]}"; do
        start_time=$(date +%s)

        exp_params="experiment: #client=${c} run=${run} write-only"

        echo "-----------------------------------------------------------------------------------"
        echo "$exp_params"
        echo "-----------------------------------------------------------------------------------"
        start_dstat "-alm -N eth0 $(($time/5))" "$output_dir" "$exp_params" "${all_machines[@]}"

        run_memtier "client1" "server1" 1 ${c} "1:0" "${output_dir}/client1_i1_c${c}_wo_r${run}.log" ${time}
        run_memtier "client1" "server2" 1 ${c} "1:0" "${output_dir}/client1_i2_c${c}_wo_r${run}.log" ${time}
        
		run_memtier "client2" "server1" 1 ${c} "1:0" "${output_dir}/client2_i1_c${c}_wo_r${run}.log" ${time}
        run_memtier "client2" "server2" 1 ${c} "1:0" "${output_dir}/client2_i2_c${c}_wo_r${run}.log" ${time}
        
		run_memtier "client3" "server1" 1 ${c} "1:0" "${output_dir}/client3_i1_c${c}_wo_r${run}.log" ${time}
        run_memtier "client3" "server2" 1 ${c} "1:0" "${output_dir}/client3_i2_c${c}_wo_r${run}.log" ${time}
       
        wait_for_jobs

        execute_on_list "sudo pkill dstat" ${all_machines[@]}
        wait_for_jobs

        exp_params="experiment: #client=${c} run=${run} read-only"
        echo "-----------------------------------------------------------------------------------"
        echo "$exp_params"
		echo "-----------------------------------------------------------------------------------"
        start_dstat "-alm -N eth0 $(($time/5))" "$output_dir" "$exp_params" "${all_machines[@]}"    
	
		run_memtier "client1" "server1" 1 ${c} "0:1" "${output_dir}/client1_i1_c${c}_ro_r${run}.log" ${time}
        run_memtier "client1" "server2" 1 ${c} "0:1" "${output_dir}/client1_i2_c${c}_ro_r${run}.log" ${time}
        
		run_memtier "client2" "server1" 1 ${c} "0:1" "${output_dir}/client2_i1_c${c}_ro_r${run}.log" ${time}
        run_memtier "client2" "server2" 1 ${c} "0:1" "${output_dir}/client2_i2_c${c}_ro_r${run}.log" ${time}
        
		run_memtier "client3" "server1" 1 ${c} "0:1" "${output_dir}/client3_i1_c${c}_ro_r${run}.log" ${time}
        run_memtier "client3" "server2" 1 ${c} "0:1" "${output_dir}/client3_i2_c${c}_ro_r${run}.log" ${time}
        
        wait_for_jobs
        execute_on_list "sudo pkill dstat" ${all_machines[@]}
        wait_for_jobs

        end_time=$(date +%s)
        runtime=$((end_time-start_time))
        let "nof_exp_left--"
        finish_time=$(date -d "$((runtime * nof_exp_left)) seconds")
        echo "-----------------------------------------------------------------------------------"
        echo "${nof_exp_left} experiments left. Last took: ${runtime} seconds. Estimated finish time: ${finish_time} "
        echo "-----------------------------------------------------------------------------------"
    done
done

echo "done with baseline for one server"
echo "getting result files from remote machines"
echo "-----------------------------------------------------------------------------------"

experiment_dir="/home/siegli/Code/asl-17/experiment_outputs"
local_result_dir="${experiment_dir}/${output_dir}"
mkdir $local_result_dir

scp siegli@client1:./$output_dir/* $local_result_dir
scp siegli@client2:./$output_dir/* $local_result_dir
scp siegli@client3:./$output_dir/* $local_result_dir
scp siegli@server1:./$output_dir/* $local_result_dir
scp siegli@server2:./$output_dir/* $local_result_dir

stop_memcached_servers "server1" "server2"
./stopVms.sh aslvm1 aslvm2 aslvm3 aslvm6 aslvm7

echo "creating zip file of client_outputs"
echo "-----------------------------------------------------------------------------------"
cd $experiment_dir
zip -r "${output_dir}.zip" $output_dir

