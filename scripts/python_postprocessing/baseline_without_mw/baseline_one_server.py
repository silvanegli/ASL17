import sys
import json
from collections import defaultdict
from plotter import setup_plots, finish_plots
import numpy as np
from helpers.memtier import parse_memtier_single_run, aggregate_memtier_results, average_memtier_results, print_data
import os
import matplotlib.pyplot as plotter
from matplotlib.ticker import AutoMinorLocator



#to output individual runs
lower_run_id = 1
upper_run_id = 3

lower_machine_id = 1
upper_machine_id = 3

#nof_clients_per_thread = [1, 4, 8, 12, 16, 20, 24, 28, 32]
#nof_clients_per_thread = [36, 40, 44, 48, 52, 56, 60, 64]
nof_clients_per_thread = [1, 4, 8, 12, 16, 20, 24, 28, 32, 40, 48, 56, 64]
nof_clients = [c * 2 * (upper_machine_id - lower_machine_id + 1) for c in nof_clients_per_thread]

nof_memtier_startups = 3
nof_memtier_cooldowns = 3


#--------------
# for worker analysis
#--------------
lower_run_id = 1
upper_run_id = 3
lower_machine_id = 3
upper_machine_id = 3
nof_clients_per_thread = [1, 2, 4, 8, 16] #, 32]
nof_clients = [c * 8 for c in nof_clients_per_thread]
nof_memtier_startups = 3
nof_memtier_cooldowns = 3


def plot_memtier_results(experiment_folder):
    #avg_ro_results = []
    avg_wo_results = []

    for clients in nof_clients_per_thread:
        wo_run_results = []
        #ro_run_results = []

        for run in range(lower_run_id, upper_run_id + 1):
            memtier_wo_results = []
            #memtier_ro_results = []
            for machine in range(lower_machine_id, upper_machine_id + 1):
                wo_parse = parse_memtier_single_run(experiment_folder, machine, 1, clients, run, 'wo').clean_trace(nof_memtier_startups, nof_memtier_cooldowns)
                #ro_parse = parse_memtier_single_run(experiment_folder, machine, 1, clients, run, 'ro').clean_trace(nof_memtier_startups, nof_memtier_cooldowns)
                wo_parse.average_latency_ops_sum_windows()
                #ro_parse.average_latency_ops_sum_windows()
                memtier_wo_results.append(wo_parse)
                #memtier_ro_results.append(ro_parse)


            #aggregate over one run
            #aggregated_ro_result = aggregate_memtier_results(memtier_ro_results)
            aggregated_wo_result = aggregate_memtier_results(memtier_wo_results)
            wo_run_results.append(aggregated_wo_result)
            #ro_run_results.append(aggregated_ro_result)

        #average over the runs
        #avg_ro_results.append(average_memtier_results(ro_run_results))
        avg_wo_results.append(average_memtier_results(wo_run_results))



    plotter.figure(1)
    plotter.errorbar(nof_clients, [res.total_avg_tps for res in avg_wo_results], yerr=[res.err_tps for res in avg_wo_results], fmt='ro-', label="write-only requests", capsize=3)
    #plotter.errorbar(nof_clients, [res.total_avg_tps for res in avg_ro_results], yerr=[res.err_tps for res in avg_ro_results], fmt='go-', label="read-only requests", capsize=3)

    #plotter.plot(nof_clients, [1000 * clients / res.total_avg_st for res, clients in zip(avg_wo_results, nof_clients)], linestyle='-', color="lightcoral", marker='o', label="w-o interactive law")
    #plotter.plot(nof_clients, [1000 * clients / res.total_avg_st for res, clients in zip(avg_ro_results, nof_clients)], linestyle='-', color="lightgreen", marker='o', label="r-o interactive law")

    plotter.figure(2)
    plotter.errorbar(nof_clients, [res.total_avg_st for res in avg_wo_results], yerr=[res.err_st for res in avg_wo_results],
                     fmt='ro-', label="write-only requests", capsize=3)
    #plotter.errorbar(nof_clients, [res.total_avg_st for res in avg_ro_results], yerr=[res.err_st for res in avg_ro_results],
     #                fmt='go-', label="read-only requests", capsize=3)

    print_data("write-only data", nof_clients, avg_wo_results, "baseline_without_mw/write-only-one-server")
    #print_data("read-only data", nof_clients, avg_ro_results, "baseline_without_mw/read-only-one-server")


def main():
    experiment_folder = os.path.abspath(sys.argv[1])
    setup_plots(1, nof_clients, "Transactions per Second relative to #Virtual Clients", "#Virtual Clients", "Transactions per Second")
    setup_plots(2, nof_clients, "Avg. Response time relative to #Virtual Clients", "#Virtual Clients", "Average Response Time [ms]")

    plotter.figure(2)


    plot_memtier_results(experiment_folder)
    finish_plots(2)

if __name__ == "__main__":
    main()
