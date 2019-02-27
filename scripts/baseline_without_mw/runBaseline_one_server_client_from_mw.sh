#!/bin/bash
source ./functions.sh

time=62


#----------------------------------------------------------
output_dir="baseline_one_server_from_two_mw_$(date +"%Y-%m-%d-%H:%M")"
all_machines=("mw1" "mw2" "server1")

create_output_dir $output_dir ${all_machines[@]}


runs=(1 2 3)
vc=(1 2 4 8 16)

nof_exp_left=$((${#vc[@]} * ${#runs[@]}))

start_and_populate_servers 11211 "server1"

for run in "${runs[@]}"; do
    for c in "${vc[@]}"; do
        start_time=$(date +%s)
        exp_params="experiment: #client=${c} run=${run} two mw"
        echo "-----------------------------------------------------------------------------------"
        echo "-----------------------------------------------------------------------------------"
        echo "Running $exp_params with two mw"
        echo "-----------------------------------------------------------------------------------"
        start_dstat "-alm -N eth0 $(($time/5))" "$output_dir" "$exp_params" "${all_machines[@]}"

        cmd1="./memtier_benchmark-master/memtier_benchmark --protocol=memcache_text --expiry-range=35999-36000 --key-maximum=10000 --data-size=1024 --ratio=1:0 --server=server1 --test-time=62 --clients=$c --threads=8 --hide-histogram --port=11211 &> ./${output_dir}/mw1_i1_c${c}_wo_r${run}.log"
        cmd2="./memtier_benchmark-master/memtier_benchmark --protocol=memcache_text --expiry-range=35999-36000 --key-maximum=10000 --data-size=1024 --ratio=1:0 --server=server1 --test-time=62 --clients=$c --threads=8 --hide-histogram --port=11211 &> ./${output_dir}/mw2_i1_c${c}_wo_r${run}.log"
        cmd3="./memtier_benchmark-master/memtier_benchmark --protocol=memcache_text --expiry-range=35999-36000 --key-maximum=10000 --data-size=1024 --ratio=1:0 --server=server1 --test-time=62 --clients=$c --threads=8 --hide-histogram --port=11211 &> ./${output_dir}/mw3_i1_c${c}_wo_r${run}.log"
        ssh siegli@mw1 "$cmd1" &
        ssh siegli@mw2 "$cmd2" & 
        wait_for_jobs    
        execute_on_list "sudo pkill dstat" ${all_machines[@]}
        wait_for_jobs
        exp_params="experiment: #client=${c} run=${run} one mw"
        start_dstat "-alm -N eth0 $(($time/5))" "$output_dir" "$exp_params" "${all_machines[@]}"

        echo "Running $exp_params with one mw"
        ssh siegli@mw2 "$cmd3"

        execute_on_list "sudo pkill dstat" ${all_machines[@]}
        wait_for_jobs

        end_time=$(date +%s)
        runtime=$((end_time-start_time))
        echo $runtime
        let "nof_exp_left--"
        finish_time=$(date -d "$((runtime * nof_exp_left)) seconds")
        echo "-----------------------------------------------------------------------------------"
        echo "${nof_exp_left} experiments left. Estimated finish time: ${finish_time} "
        echo "-----------------------------------------------------------------------------------"
    done
done

echo "done with baseline for one server"
echo "getting result files from remote machines"
echo "-----------------------------------------------------------------------------------"


experiment_dir="/home/siegli/Code/asl-17/experiment_outputs"
local_result_dir="${experiment_dir}/${output_dir}"
mkdir $local_result_dir

scp siegli@mw1:./$output_dir/* $local_result_dir
scp siegli@mw2:./$output_dir/* $local_result_dir


#stop_memcached_servers "server1"
#./stopVms.sh aslvm1 aslvm2 aslvm3 aslvm6

echo "creating zip file of client_outputs"
echo "-----------------------------------------------------------------------------------"
cd $experiment_dir
zip -r "${output_dir}.zip" $output_dir

