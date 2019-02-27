#!/bin/bash

all=("client1" "client2" "client3" "mw1" "mw2" "server1" "server2" "server3")
sep_line="------------------------------------------------------------------------"


function run_memtier() {
    local client=$1
    local server=$2
    local nof_threads=$3
    local nof_clients=$4
    local ratio=$5
    local out_file=$6
    local duration=$7
    local port=11211
    if [ ! -z "$8" ]; then
        port=$8
    fi


    cmd="memtier_benchmark --protocol=memcache_text --expiry-range=35999-36000 --key-maximum=10000 --data-size=1024 --ratio=${ratio} --server=${server} --port=${port} --test-time=${time} --clients=${nof_clients} --threads=${nof_threads}"

    echo "running command: ${cmd}"
    ssh siegli@${client} "${cmd} &> $out_file"  &
}

function ping_test() {
    local -n from_list=$1
    local -n to_list=$2
    local output_dir=$3

    echo "running ping tests"
    for src in "${from_list[@]}"; do
        for dest in "${to_list[@]}"; do
            echo "pinging ${dest} from ${src}"
            ssh siegli@${src} "printf '\n%s\n%s ----> %s\n%s\n' $sep_line $src $dest $sep_line >> ./${output_dir}/ping_${src}.txt" &
            ssh siegli@${src} "ping ${dest} -w 60 >> ./${output_dir}/ping_${src}.txt" &
        done
    done

    wait_for_jobs
}

function iperf_test() {
    local -n client_list=$1
    local -n server_list=$2
    local output_dir=$3
    local both=("${client_list[@]}" "${server_list[@]}")
    for server in "${server_list[@]}"; do
		ssh siegli@$server "iperf -s -B ${server} -i 5 >> ./${output_dir}/iperf_${server}.txt" &
        disown
    done

	wait_for_open_port 5001 "${server_list[@]}"

    for machine in "${both[@]}"; do
        ssh siegli@${machine} "printf '\n%s\n%s\n%s\n' $sep_line 'all-to-all' $sep_line >> ./${output_dir}/iperf_${machine}.txt"
	done

    echo "running parallel iperf tests"
    for client in "${client_list[@]}"; do
        for server in "${server_list[@]}"; do
            echo "iperfing ${server} from ${client}"
            ssh siegli@${client} "iperf -c ${server} -t 30 -i 5 >> ./${output_dir}/iperf_${client}.txt" &
        done
    done
    wait_for_jobs
    
	echo "running sequential iperf tests"
    for client in "${client_list[@]}"; do
        for server in "${server_list[@]}"; do
            echo "iperfing ${server} from ${client}"
            ssh siegli@${client} "printf '\n%s\n%s ----> %s\n%s\n' $sep_line $client $server $sep_line >> ./${output_dir}/iperf_${client}.txt"
            ssh siegli@${server} "printf '\n%s\n%s ----> %s\n%s\n' $sep_line $client $server $sep_line >> ./${output_dir}/iperf_${server}.txt"
            
			ssh siegli@${client} "iperf -c ${server} -t 10 -i 2  >> ./${output_dir}/iperf_${client}.txt"
        done
    done
	
	kill_and_wait_for_process_shutdown "iperf" "${server_list[@]}"
}


function start_dstat() {
	local params=$1
	local out_file="./$2/dstat_${machine}.txt"
	local experiment_params=$3	

    for machine in "${@:4}"; do
	    out_file="./$2/dstat_${machine}.txt"
		ssh siegli@$machine "printf '\n%s\n%s   | dstat params: %s\n%s\n' $sep_line \"$experiment_params\" \"$params\" $sep_line >> $out_file && dstat $params >> $out_file" &
        #ssh siegli@$machine "dstat $params >> $out_file" &
    	disown
	done
	#wait_for_process_startup "dstat" "${@:4}"
    sleep 3
}



function shutdown_services() {
    for machine in "$@"; do
        echo "getting status of: ${machine} and killing all running memcached and java processes"
        ssh siegli@$machine "landscape-sysinfo" &
        ssh siegli@$machine "sudo pkill java" &
        ssh siegli@$machine "sudo pkill memcached" &
    done
    sleep 5 
	wait_for_jobs
}

function execute_on_all() {
	for machine in "${all[@]}"; do
		echo "executing $1 on ${machine}"
		ssh siegli@$machine "$1" &
	done
    wait_for_jobs
}


function execute_on_list() {
    for machine in "${@:2}"; do
        echo "executing $1 on ${machine}"
        ssh siegli@$machine "$1" &
    done
}


function create_output_dir(){
    for machine in "${@:2}"; do
        echo "creating output dir $1 on ${machine}"
        ssh siegli@$machine "mkdir $1" &
    done
    wait_for_jobs
}


function stop_and_collect_mw_statistics() {
    local mw=$1
    local out_file=$2

    ssh siegli@$mw "sudo pkill java"
    wait_for_process_shutdown "java" $mw
    ssh siegli@$mw "cp ./logs/timing.log ${out_file}"
    echo "${mw} output in ${out_file}"
}

function start_and_populate_servers() {
    local port=$1

    for server in "${@:2}"; do
        echo "starting ${server}"
        ssh siegli@$server "memcached -l ${server}:${port} -t 1" &
        disown
    done
    sleep 5

    for server in "${@:2}"; do
        echo "populating ${server}"
        #ssh siegli@$server "memtier_benchmark --protocol=memcache_text --expiry-range=9999-10000 --key-maximum=10000 --data-size=1024 --ratio=1:0 --key-pattern=S:S --server=localhost --port=2222 --test-time=5 --clients=1 --threads=1 &> ./populate.txt" &
        ssh siegli@$server "memtier_benchmark --protocol=memcache_text --expiry-range=35999-36000 --key-maximum=10000 --data-size=1024 --ratio=1:0 --key-pattern=S:S --server=${server} --port=${port} --test-time=5 --clients=1 --threads=1 --hide-histogram" &
    done
    wait_for_jobs
    echo "starting and writing servers done"
}

function stop_memcached_servers() {
    for server in "$@"; do
        echo "stopping ${server}"
        ssh siegli@$server "sudo pkill memcached" &
    done
    wait_for_jobs
}

function get_experiment_logs() {
    local local_dir=$1
    local remote_files=$2
    
    mkdir $local_dir
    for machine in "${@:3}"; do
        echo "getting result files from machine: ${machine}"
        scp siegli@$machine:$remote_files $local_dir
    done
}

function create_zip_file() {
    local experiment_dir=$1
    local output_dir=$2
    echo "creating zip file of client_outputs"
    echo "-----------------------------------------------------------------------------------"
    cd $experiment_dir
    zip -r "${output_dir}.zip" $output_dir
    cd -
}

function check_if_machines_down() {
    #Attention: brainfuck 0 for true and 1 for false
    echo "check if machines are running..."
    for machine in "${@}"; do
        if [ ! $(ssh siegli@$machine "pgrep ssh -fo") ]; then
            echo "machine $machine not running"
            return 0
        fi
    done
    return 1
}

function wait_for_open_port() {
    for machine in "${@:2}"; do
        while [ ! $(ssh siegli@$machine "sudo netstat -tulpn | grep $1") ]; do
            echo "port $1 not yet open on ${machine} trying again..."
            sleep 1
        done
        echo "port $1 open on ${machine}"
    done
}

function wait_for_process_startup() {
    for machine in "${@:2}"; do
        while [ ! $(ssh siegli@$machine "pgrep $1 -fo") ]; do
			echo "$1 not yet running on ${machine} trying again..."
            sleep 1
        done
		echo "$1 running on ${machine}"
	done
}

function wait_for_process_shutdown() {
    for machine in "${@:2}"; do
        while [ $(ssh siegli@$machine "pgrep $1 -fo") ]; do
            echo "$1 still running on ${machine} trying again..."
            ssh siegli@$machine "sudo pkill $1"
        done
        echo "$1 shutdown on ${machine}"
    done
}

function kill_and_wait_for_process_shutdown() {
    for machine in "${@:2}"; do
        ssh siegli@$machine "sudo pkill $1"
        while [ $(ssh siegli@$machine "pgrep $1 -fo") ]; do
            echo "$1 still running on ${machine} trying again..."
            ssh siegli@$machine "sudo pkill $1"
			sleep 2
        done
        echo "$1 shutdown on ${machine}"
    done
}


function wait_for_jobs() {
    for job in `jobs -p`
    do
        echo "Waiting for job: $job to complete"
        wait $job
    done
}
