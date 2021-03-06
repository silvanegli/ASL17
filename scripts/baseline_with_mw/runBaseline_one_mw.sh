#!/bin/bash

source ./functions.sh

time=62
output_dir="baseline_one_mw_usage_test$(date +"%Y-%m-%d-%H:%M")"
experiment_dir="/home/siegli/Code/asl-17/experiment_outputs"
local_result_dir="${experiment_dir}/${output_dir}"
all_machines=("client1" "mw1" "server1")

if check_if_machines_down ${all_machines[@]}; then
    ./startVms.sh aslvm1 aslvm4 aslvm6
	if [ "$?" == "1" ]; then
		echo "Starting VM's Failed!"
       	exit 1
	fi
else
	echo "machines are already running !"
fi



wait_for_process_startup "ssh" ${all_machines[@]}
shutdown_services ${all_machines[@]}


create_output_dir $output_dir "client1" "mw1" "server1"

from=("mw1" "client1")
to=("mw1" "server1")
ping_test from to $output_dir

vc=(1 4 8 12 16 20 24 28 32 48)
runs=(1 2 3)
nof_workers=(8 16 32 64)

nof_exp=$((${#vc[@]} * ${#runs[@]} * ${#nof_workers[@]}))
nof_exp_left=$nof_exp

start_and_populate_servers 2222 "server1"


for run in "${runs[@]}"; do
    for c in "${vc[@]}"; do
        for workers in "${nof_workers[@]}"; do
            start_time=$(date +%s)
	
        	exp_params="#client=${c} #workers=${workers} run=${run} write-only and afterwards read-only"
            mw_cmd="java -jar ./asl-17/dist/middleware-siegli.jar -l mw1 -p 11211 -s false -m server1:2222 -t ${workers}"
            echo "-----------------------------------------------------------------------------------"
            echo "-----------------------------------------------------------------------------------"
            echo "experiment $((nof_exp-nof_exp_left+1))/${nof_exp}: ${exp_params}"
            echo "-----------------------------------------------------------------------------------"
    
            echo "starting mw : ${mw_cmd}"
            ssh siegli@mw1 $mw_cmd &
            disown #we don't want to wait for this job
	        start_dstat "-alm -N eth0 $(($time/10))" "$output_dir" "$exp_params" "${all_machines[@]}"

            wait_for_open_port 11211 "mw1" 
           
            echo "-----------------------------------------------------------------------------------"
            echo "running write-only  experiments"
            echo "-----------------------------------------------------------------------------------"
            run_memtier "client1" "mw1" 2 ${c} "1:0" "./${output_dir}/client1_i1_c${c}_wo_mwt${workers}_run${run}.log" ${time}
            wait_for_jobs
            stop_and_collect_mw_statistics "mw1" "./${output_dir}/mw1_i1_c${c}_wo_mwt${workers}_run${run}.log"
       		 
        
        
            echo "starting mw again : ${mw_cmd}"
            ssh siegli@mw1 $mw_cmd &
            disown
            wait_for_open_port 11211 "mw1" 

            echo "-----------------------------------------------------------------------------------"
    		echo "running read-only  experiments"
            echo "-----------------------------------------------------------------------------------"
            run_memtier "client1" "mw1" 2 ${c} "0:1" "./${output_dir}/client1_i1_c${c}_ro_mwt${workers}_run${run}.log" ${time}
            wait_for_jobs
            stop_and_collect_mw_statistics "mw1" "./${output_dir}/mw1_i1_c${c}_ro_mwt${workers}_run${run}.log"

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
echo "done with baseline for one mw"
echo "-----------------------------------------------------------------------------------"

experiment_dir="/home/siegli/Code/asl-17/experiment_outputs"
local_result_dir="${experiment_dir}/${output_dir}"

get_experiment_logs $local_result_dir "./${output_dir}/*" client1 mw1 server1
create_zip_file "$experiment_dir" "$output_dir"

stop_memcached_servers "server1"
./stopVms.sh aslvm1 aslvm4 aslvm6

