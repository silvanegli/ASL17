#!/bin/bash

source ./functions.sh

time=62
output_dir="baseline_two_mw_$(date +"%Y-%m-%d-%H:%M")"
experiment_dir="/home/siegli/Code/asl-17/experiment_outputs"
local_result_dir="${experiment_dir}/${output_dir}"
all_machines=("client1" "mw1" "mw2" "server1")

vc=(1 4 8 12 16 20 24 28 32)
runs=(1 2 3)
nof_workers=(8 16 32 64)

nof_exp=$((${#vc[@]} * ${#runs[@]} * ${#nof_workers[@]}))
nof_exp_left=$nof_exp


if check_if_machines_down ${all_machines[@]}; then
    ./startVms.sh aslvm1 aslvm4 aslvm5 aslvm6
	if [ "$?" == "1" ]; then
		echo "Starting VM's Failed!"
       	exit 1
	fi
else
	echo "machines are already running !"
fi



wait_for_process_startup "ssh" ${all_machines[@]}
shutdown_services ${all_machines[@]}


create_output_dir $output_dir "client1" "mw1" "mw2" "server1"

from=("mw1" "mw2" "client1")
to=("mw1" "mw2" "server1")
ping_test from to $output_dir

start_and_populate_servers 2222 "server1"


for run in "${runs[@]}"; do
    for c in "${vc[@]}"; do
        for workers in "${nof_workers[@]}"; do
            start_time=$(date +%s)
            exp_params="#client=${c} #workers=${workers} run=${run} write-only and afterwards read-only"
            mw_cmd_1="java -jar ./asl-17/dist/middleware-siegli.jar -l mw1 -p 11211 -s false -m server1:2222 -t ${workers}"
            mw_cmd_2="java -jar ./asl-17/dist/middleware-siegli.jar -l mw2 -p 11211 -s false -m server1:2222 -t ${workers}"
            echo "-----------------------------------------------------------------------------------"
            echo "-----------------------------------------------------------------------------------"
            echo "experiment $((nof_exp-nof_exp_left+1))/${nof_exp}: ${exp_params}"
            echo "-----------------------------------------------------------------------------------"
    
            echo "starting mws : ${mw_cmd}"
            ssh siegli@mw1 $mw_cmd_1 &
            disown #we don't want to wait for this job
            ssh siegli@mw2 $mw_cmd_2 &
            disown #we don't want to wait for this job
            start_dstat "-alm -N eth0 $(($time/10))" "$output_dir" "$exp_params" "${all_machines[@]}"

            wait_for_open_port 11211 "mw1" "mw2"
            
            echo "-----------------------------------------------------------------------------------"
            echo "running write-only  experiments"
            echo "-----------------------------------------------------------------------------------"
            run_memtier "client1" "mw1" 1 ${c} "1:0" "./${output_dir}/client1_i1_c${c}_wo_mwt${workers}_run${run}.log" ${time}
            run_memtier "client1" "mw2" 1 ${c} "1:0" "./${output_dir}/client1_i2_c${c}_wo_mwt${workers}_run${run}.log" ${time}
            wait_for_jobs
            stop_and_collect_mw_statistics "mw1" "./${output_dir}/mw1_i1_c${c}_wo_mwt${workers}_run${run}.log" &
            stop_and_collect_mw_statistics "mw2" "./${output_dir}/mw2_i1_c${c}_wo_mwt${workers}_run${run}.log" &
            wait_for_jobs 

            echo "restarting mws : ${mw_cmd}"
            ssh siegli@mw1 $mw_cmd_1 &
            disown #we don't want to wait for this job
            ssh siegli@mw2 $mw_cmd_2 &
            disown #we don't want to wait for this job
            wait_for_open_port 11211 "mw1" "mw2"        
        

            echo "-----------------------------------------------------------------------------------"
    		echo "running read-only  experiments"
            echo "-----------------------------------------------------------------------------------"
            run_memtier "client1" "mw1" 1 ${c} "0:1" "./${output_dir}/client1_i1_c${c}_ro_mwt${workers}_run${run}.log" ${time}
            run_memtier "client1" "mw2" 1 ${c} "0:1" "./${output_dir}/client1_i2_c${c}_ro_mwt${workers}_run${run}.log" ${time}
            wait_for_jobs
            stop_and_collect_mw_statistics "mw1" "./${output_dir}/mw1_i1_c${c}_ro_mwt${workers}_run${run}.log" &
            stop_and_collect_mw_statistics "mw2" "./${output_dir}/mw2_i1_c${c}_ro_mwt${workers}_run${run}.log" &
			wait_for_jobs

            execute_on_list "sudo pkill dstat" ${all_machines[@]}
            end_time=$(date +%s)
            runtime=$((end_time-start_time))
            let "nof_exp_left--"
            finish_time=$(date -d "$((runtime * nof_exp_left)) seconds")
            echo "-----------------------------------------------------------------------------------"
            echo "${nof_exp_left} experiments left. Last took: ${runtime} seconds. Estimated finish time: ${finish_time} "
            echo "-----------------------------------------------------------------------------------"
        done
    done
done

echo "-----------------------------------------------------------------------------------"
echo "done with baseline for two mw"
echo "-----------------------------------------------------------------------------------"

experiment_dir="/home/siegli/Code/asl-17/experiment_outputs"
local_result_dir="${experiment_dir}/${output_dir}"

get_experiment_logs $local_result_dir "./${output_dir}/*" client1 mw1 mw2 server1
create_zip_file "$experiment_dir" "$output_dir"

#stop_memcached_servers "server1" "server2"
#./stopVms.sh aslvm1 aslvm4 aslvm5 aslvm6

./stopVms aslvm5

