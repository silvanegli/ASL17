from helpers.memtier import parse_memtier_custom, MemtierResult, aggregate_memtier_results
from helpers.middleware import parse_mw_single_custom_file, MiddlewareResult
import matplotlib.pyplot as plotter
from matplotlib.ticker import AutoMinorLocator
import numpy as np
import os

write_only_summary_file = "/home/siegli/Code/asl-17/experiment_outputs/useful/2k_analysis/write-only-summary.csv"
read_only_summary_file = "/home/siegli/Code/asl-17/experiment_outputs/useful/2k_analysis/read-only-summary.csv"
mixed_summary_file = "/home/siegli/Code/asl-17/experiment_outputs/useful/2k_analysis/mixed-summary.csv"

memtier_machine_list = [1, 2, 3]

run_list = [1, 2, 3]
nof_servers = [2, 3]
nof_mws = [1, 2]
nof_workers = [8, 32]


def summarize_experiments(experiment_folder, payload, write_file):
    nof_files = 0
    for sign_servers, servers in zip([-1, 1], nof_servers):
        for sign_workers, workers in zip([-1, 1], nof_workers):
            for sign_mws, mws in zip([-1, 1], nof_mws):
                #calculate the 3 results
                exp_results = []
                for run in run_list:
                    run_results = []
                    for machine in memtier_machine_list:
                        for instance in range(1, mws + 1):
                            filename = "client{}_i{}_p{}_mwt{}_mw{}_s{}_run{}.log".format(machine, instance, payload, workers, mws, servers, run)
                            parsed_memtier = parse_memtier_custom(experiment_folder + "/" + filename)
                            parsed_memtier.clean_trace(4, 4)
                            parsed_memtier.average_latency_ops_sum_windows()
                            check_stdv(parsed_memtier)
                            run_results.append(parsed_memtier)
                            nof_files += 1

                    exp_results.append(aggregate_memtier_results(run_results))

                append_experiment_line(write_file, exp_results, sign_mws, sign_workers, sign_servers)

    print "Number of parsed files: " + str(nof_files)

def append_experiment_line(write_file, exp_results, sign_mws, sign_workers, sign_servers):
    if len(run_list) != len(exp_results):
        print 'errror nof results != nof runs'
        return

    with open(write_file, 'a') as f:
        sign_array = [1, sign_mws, sign_workers, sign_servers, sign_mws * sign_workers, sign_mws * sign_servers, sign_workers * sign_servers, sign_mws * sign_workers * sign_servers]
        tp_array = [int(run_res.total_avg_tps) for run_res in exp_results]
        rt_array = [round(run_res.total_avg_st, 2) for run_res in exp_results]
        exp_array = tp_array + [int(np.mean(tp_array))]  + rt_array + [round(np.mean(rt_array), 2)]

        data_array = sign_array + [" "] + exp_array

        data_string = ",".join(map(str, data_array))
        f.write(data_string + os.linesep)


def check_stdv(parsed_memtier):
    tp = parsed_memtier.total_avg_tps
    std_tp = parsed_memtier.err_tps
    rt = parsed_memtier.total_avg_st
    std_rt = parsed_memtier.err_st

    if std_tp / tp > 0.2:
        print "Warning high TP stdv: {} for {} in {}".format(std_tp, tp, parsed_memtier.path_to_file)

    if std_rt / rt > 0.2:
        print "Warning high RT stdv: {} for {} in {}".format(std_rt, rt, parsed_memtier.path_to_file)



def write_first_line(file):
    header = "I, M, W, S, MW, MS, WS, MWS, ,Tp1, Tp2, Tp3, MeanTP,Rt1, Rt2, Rt3, MeanRt"
    with open(file, 'w') as f:
        f.write(header + os.linesep)


def main():
    exp_folder = "/home/siegli/Code/asl-17/experiment_outputs/useful/2k_analysis/2k_experiment"
    write_first_line(write_only_summary_file)
    summarize_experiments(exp_folder, "1:0", write_only_summary_file)
    write_first_line(read_only_summary_file)
    summarize_experiments(exp_folder, "0:1", read_only_summary_file)
    write_first_line(mixed_summary_file)
    summarize_experiments(exp_folder, "1:1", mixed_summary_file)

if __name__ == "__main__":
    main()