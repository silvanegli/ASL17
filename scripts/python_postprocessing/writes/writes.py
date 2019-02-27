import sys
from helpers.middleware import parse_mw_single_run, aggregate_middleware_results, average_middleware_results
from helpers.middleware import print_mw_experiment as append_mw_result
from helpers.memtier import parse_memtier_single_run_with_workers
from helpers.memtier import append_data as append_memtier_result
from helpers.memtier import aggregate_memtier_results, average_memtier_results
from plotter import setup_plots, finish_plots
import os
import matplotlib.pyplot as plotter

nof_Runs = 3
#to output individual runs
lower_run_id = 1
upper_run_id = 2


lower_mw_machine_id = 1
upper_mw_machine_id = 2

lower_memtier_machine_id = 1
upper_memtier_machine_id = 3

lower_memtier_instance_id = 1
upper_memtier_instance_id = 2

mw_instance_id = 2

nof_clients_per_thread = [1, 4, 8, 12, 16, 20, 24, 28 ,32]
nof_workers = [8, 16, 32, 64]


nof_clients_per_thread = [1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50]
nof_workers = [8, 16, 32, 64]



nof_clients = [c * (upper_memtier_machine_id - lower_memtier_machine_id + 1) *(upper_memtier_instance_id - lower_memtier_instance_id + 1) for c in nof_clients_per_thread]

nof_startups = 2
nof_cooldowns = 2

nof_memtier_startups = 2
nof_memtier_cooldowns = 2

nof_plots = 6



'''
--------------------- Single MW output ---------------------
'''


def plot_wo_results(experiment_folder, mw_id):
    for workers in nof_workers:
        avg_wo_results = []

        for clients in nof_clients_per_thread:
            wo_run_results = []
            for run in range(lower_run_id, upper_run_id + 1):
                mw_result = parse_mw_single_run(experiment_folder, 1, clients, workers, run, 'wo')
                mw_result.clean_trace(nof_startups, nof_cooldowns)
                mw_result.average_mw_sum()
                wo_run_results.append(mw_result)

            # average over the runs
            avg_wo_results.append(average_middleware_results(wo_run_results))

        plotter.figure(1)
        plotter.errorbar(nof_clients, [res.avg_mwt for res in avg_wo_results],
                         yerr=[res.std_mwt for res in avg_wo_results], fmt='o-',
                         label="{} MW Threads".format(workers),
                         capsize=3)
        plotter.figure(2)
        plotter.errorbar(nof_clients, [res.avg_tp for res in avg_wo_results],
                         yerr=[res.std_tp for res in avg_wo_results], fmt='o-',
                         label="{} MW Threads".format(workers),
                         capsize=3)

'''
--------------------- Merged MW output ---------------------
'''

def plot_merged_wo_results(experiment_folder):
    for workers in nof_workers:
        avg_wo_results = []
        avg_singleMw_dict = get_fresh_mw_res_dict()
        for clients in nof_clients_per_thread:
            wo_run_results = []
            singleMw_run_results_dict = get_fresh_mw_res_dict()
            for run in range(lower_run_id, upper_run_id + 1):
                wo_machine_results = []
                for machine_id in range(lower_mw_machine_id, upper_mw_machine_id + 1):
                    mw_result = parse_mw_single_run(experiment_folder, machine_id, clients, workers, run, 'wo')
                    mw_result.clean_trace(nof_startups, nof_cooldowns)
                    mw_result.average_mw_sum()
                    wo_machine_results.append(mw_result)
                    singleMw_run_results_dict[machine_id].append(mw_result)

                #aggregate over mw's
                aggregated_mw_result = aggregate_middleware_results(wo_machine_results)
                wo_run_results.append(aggregated_mw_result)

            # average over the runs
            avg_singleMw_dict[1].append(average_middleware_results(singleMw_run_results_dict[1]))
            avg_singleMw_dict[2].append(average_middleware_results(singleMw_run_results_dict[2]))
            avg_wo_results.append(average_middleware_results(wo_run_results))

        plotter.figure(5)
        plotter.errorbar(nof_clients, [res.avg_mwt for res in avg_wo_results],yerr=[res.std_mwt for res in avg_wo_results], fmt='o-', label="{} MW Threads".format(workers),capsize=3)
        plotter.figure(6)
        plotter.errorbar(nof_clients, [res.avg_tp for res in avg_wo_results],yerr=[res.std_tp for res in avg_wo_results], fmt='o-',label="{} MW Threads".format(workers),capsize=3)

        append_mw_result("w-o middleware 1 result worker: {} ".format(workers), nof_clients, avg_singleMw_dict[1],"writes/writes-summary-plot-data")
        append_mw_result("w-o middleware 2 result worker: {} ".format(workers), nof_clients, avg_singleMw_dict[2],"writes/writes-summary-plot-data")

        append_mw_result("w-o merged middleware result worker: {} ".format(workers), nof_clients, avg_wo_results,"writes/writes-summary-plot-data")




'''
---------------------  Memtier output ---------------------
'''


def plot_wo_memtier_results(experiment_folder):
    for workers in nof_workers:
        avg_wo_results = []

        for clients in nof_clients_per_thread:
            wo_run_results = []
            for run in range(lower_run_id, upper_run_id + 1):
                memtier_wo_results = []
                for machine in range(lower_memtier_machine_id, upper_memtier_machine_id + 1):
                    for instance in range(lower_memtier_instance_id, upper_memtier_instance_id + 1):
                        wo_parse = parse_memtier_single_run_with_workers(experiment_folder, machine, instance, clients, workers, run, 'wo').clean_trace(nof_memtier_startups, nof_memtier_cooldowns)
                        wo_parse.average_latency_ops_sum_windows()
                        memtier_wo_results.append(wo_parse)

                # aggregate over one run
                aggregated_wo_result = aggregate_memtier_results(memtier_wo_results)
                wo_run_results.append(aggregated_wo_result)

            # average over the runs
            avg_wo_results.append(average_memtier_results(wo_run_results))

        plotter.figure(3)
        plotter.errorbar(nof_clients, [res.total_avg_st for res in avg_wo_results], yerr=[res.err_st for res in avg_wo_results], fmt='o-', label="{} MW Threads".format(workers), capsize=3)
        plotter.figure(4)
        plotter.errorbar(nof_clients, [res.total_avg_tps for res in avg_wo_results], yerr=[res.err_tps for res in avg_wo_results], fmt='o-', label="{} MW Threads".format(workers), capsize=3)

        append_memtier_result("write-only memtier worker: {}".format(workers), nof_clients, avg_wo_results, "writes/writes-summary-plot-data")




def get_fresh_mw_res_dict():
    res_dict = dict()
    res_dict[1] = []
    res_dict[2] = []
    return res_dict


def main():
    experiment_folder = os.path.abspath(sys.argv[1])
    setup_plots(1, nof_clients, "MW{} result for a write-only payload".format(mw_instance_id), "#Virtual Clients", "Average Response Time [ms]")
    setup_plots(2, nof_clients, "MW{} result for a write-only payload".format(mw_instance_id) , "#Virtual Clients", "Transactions per Second")

    setup_plots(3, nof_clients, "Memtier result for a write-only payload", "#Virtual Clients", "Average Response Time [ms]")
    setup_plots(4, nof_clients, "Memtier result for a write-only payload", "#Virtual Clients", "Transactions per Second")

    setup_plots(5, nof_clients, "Summed MW result for a write-only payload", "#Virtual Clients", "Average Response Time [ms]")
    setup_plots(6, nof_clients, "Summed MW result for a write-only payload", "#Virtual Clients", "Transactions per Second")

    plot_wo_results(experiment_folder, mw_instance_id)
    plot_merged_wo_results(experiment_folder)
    plot_wo_memtier_results(experiment_folder)

    finish_plots(nof_plots)


if __name__ == "__main__":
    main()
