#!/bin/bash

source ./functions.sh

time=62 #TODO
output_dir="reads_$(date +"%Y-%m-%d-%H:%M")" #TODO
experiment_dir="/home/siegli/Code/asl-17/experiment_outputs"
local_result_dir="${experiment_dir}/${output_dir}"
all_machines=("client1" "client2" "client3" "mw1" "mw2" "server1" "server2" "server3")

nof_workers=16

runs=(1 2 3)
nof_multikeys=(1 3 6 9 12)
sharded=("false" "true")

###TODOS

nof_exp=$((${#nof_multikeys[@]} * ${#runs[@]} * ${#sharded[@]}))
nof_exp_left=$nof_exp


if check_if_machines_down ${all_machines[@]}; then
    ./startVms.sh aslvm1 aslvm2 aslvm3 aslvm4 aslvm5 aslvm6 aslvm7 aslvm8
	if [ "$?" == "1" ]; then
		echo "Starting VM's Failed!"
       	exit 1
	fi
else
	echo "machines are already running !"
fi



wait_for_process_startup "ssh" ${all_machines[@]}
shutdown_services ${all_machines[@]}


create_output_dir $output_dir "client1" "client2" "client3" "mw1" "mw2" "server1" "server2" "server3"

from=("mw1" "mw2" "client1" "client2" "client3")
to=("mw1" "mw2" "server1" "server2" "server3")
ping_test from to $output_dir

start_and_populate_servers 2222 "server1" "server2" "server3"

for shard in "${sharded[@]}"; do
    for run in "${runs[@]}"; do
        for keys in "${nof_multikeys[@]}"; do
            start_time=$(date +%s)
            exp_params="#keys: ${keys} sharded: ${shard} rund:${run}"
            mw_cmd_1="java -jar ./asl-17/dist/middleware-siegli.jar -l mw1 -p 11211 -s ${shard} -m server1:2222 server2:2222 server3:2222 -t $nof_workers"
            mw_cmd_2="java -jar ./asl-17/dist/middleware-siegli.jar -l mw2 -p 11211 -s ${shard} -m server1:2222 server2:2222 server3:2222 -t $nof_workers"
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
            echo "running clients"
            echo "-----------------------------------------------------------------------------------"
            cmd1="memtier_benchmark --protocol=memcache_text --expiry-range=35999-36000 --key-maximum=10000 --data-size=1024 --server=mw1 --port=11211 --test-time=${time} --clients=2 --threads=1 --multi-key-get=${keys}"
            cmd2="memtier_benchmark --protocol=memcache_text --expiry-range=35999-36000 --key-maximum=10000 --data-size=1024 --server=mw2 --port=11211 --test-time=${time} --clients=2 --threads=1 --multi-key-get=${keys}"


            echo "running command1: ${cmd1}"
            echo "running command2: ${cmd2}"

            ssh siegli@client1 "$cmd1 &> ./${output_dir}/client1_i1_k${keys}_s${shard}_r${run}.log"  &
            ssh siegli@client1 "$cmd2 &> ./${output_dir}/client1_i2_k${keys}_s${shard}_r${run}.log"  &
            
            ssh siegli@client2 "$cmd1 &> ./${output_dir}/client2_i1_k${keys}_s${shard}_r${run}.log"  &
            ssh siegli@client2 "$cmd2 &> ./${output_dir}/client2_i2_k${keys}_s${shard}_r${run}.log"  &
            
            ssh siegli@client3 "$cmd1 &> ./${output_dir}/client3_i1_k${keys}_s${shard}_r${run}.log"  &
            ssh siegli@client3 "$cmd2 &> ./${output_dir}/client3_i2_k${keys}_s${shard}_r${run}.log"  &
            wait_for_jobs

            execute_on_list "sudo pkill dstat" ${all_machines[@]}
            stop_and_collect_mw_statistics "mw1" "./${output_dir}/mw1_i1_k${keys}_s${shard}_r${run}.log" &
            stop_and_collect_mw_statistics "mw2" "./${output_dir}/mw2_i1_k${keys}_s${shard}_r${run}.log" &
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
done

echo "-----------------------------------------------------------------------------------"
echo "done with reads"
echo "-----------------------------------------------------------------------------------"

experiment_dir="/home/siegli/Code/asl-17/experiment_outputs"
local_result_dir="${experiment_dir}/${output_dir}"

get_experiment_logs $local_result_dir "./${output_dir}/*" client1 client2 client3 mw1 mw2 server1
create_zip_file "$experiment_dir" "$output_dir"

#stop_memcached_servers "server1" "server2"
#./stopVms.sh aslvm1 aslvm4 aslvm5 aslvm6

