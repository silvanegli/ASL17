import sys
from helpers.middleware import parse_mw_single_run, average_middleware_results, aggregate_middleware_results
from helpers.memtier import parse_memtier_single_run_with_workers, average_memtier_results
from helpers.middleware import print_mw_experiment as append_mw_result
from helpers.memtier import append_data as append_memtier_result
from plotter import finish_plots, setup_plots
import os
import matplotlib.pyplot as plotter


nof_Runs = 3
#to output individual runs
lower_run_id = 1
upper_run_id = 1


nof_clients_per_thread = [1, 4, 8, 12, 16, 20, 24, 28, 32]
nof_clients_per_thread = [32, 40, 52, 64]

nof_clients = [c * 2 for c in nof_clients_per_thread]
nof_workers = [64] # 128]
#nof_workers = [64]
nof_startups = 4
nof_cooldowns = 4

nof_memtier_startups = 4
nof_memtier_cooldowns = 4

nof_plots = 8


def plot_wo_results(experiment_folder):
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

        append_mw_result("w-o middleware result worker: {} ".format(workers), nof_clients, avg_wo_results,
                         "baseline_with_mw/one-mw-plot-data")


def plot_ro_results(experiment_folder):
    for workers in nof_workers:
        avg_ro_results = []

        for clients in nof_clients_per_thread:
            ro_run_results = []
            for run in range(lower_run_id, upper_run_id + 1):
                mw_result = parse_mw_single_run(experiment_folder, 1, clients, workers, run, 'ro')
                mw_result.clean_trace(nof_startups, nof_cooldowns)
                mw_result.average_mw_sum()
                ro_run_results.append(mw_result)

            # average over the runs
            avg_ro_results.append(average_middleware_results(ro_run_results))

        plotter.figure(3)
        plotter.errorbar(nof_clients, [res.avg_mwt for res in avg_ro_results],
                         yerr=[res.std_mwt for res in avg_ro_results], fmt='o-', label="{} MW Threads".format(workers),
                         capsize=3)
        plotter.figure(4)
        plotter.errorbar(nof_clients, [res.avg_tp for res in avg_ro_results],
                         yerr=[res.std_tp for res in avg_ro_results], fmt='o-', label="{} MW Threads".format(workers),
                         capsize=3)

        append_mw_result("r-o middleware result worker: {} ".format(workers), nof_clients, avg_ro_results, "baseline_with_mw/one-mw-plot-data")


def plot_wo_memtier_results(experiment_folder):
    for workers in nof_workers:
        avg_wo_results = []

        for clients in nof_clients_per_thread:
            wo_run_results = []
            for run in range(lower_run_id, upper_run_id + 1):
                wo_parse = parse_memtier_single_run_with_workers(experiment_folder, 1, 1, clients, workers, run, 'wo').clean_trace(nof_memtier_startups, nof_memtier_cooldowns)
                wo_parse.average_latency_ops_sum_windows()
                wo_run_results.append(wo_parse)

            # average over the runs
            avg_wo_results.append(average_memtier_results(wo_run_results))


        plotter.figure(5)
        plotter.errorbar(nof_clients, [res.total_avg_st for res in avg_wo_results],
                         yerr=[res.err_st for res in avg_wo_results], fmt='o-', label="{} MW Threads".format(workers),
                         capsize=3)
        plotter.figure(6)
        plotter.errorbar(nof_clients, [res.total_avg_tps for res in avg_wo_results],
                         yerr=[res.err_tps for res in avg_wo_results], fmt='o-', label="{} MW Threads".format(workers),
                         capsize=3)

        append_memtier_result("write-only memtier worker: {}".format(workers), nof_clients, avg_wo_results, "baseline_with_mw/one-mw-plot-data")


def plot_ro_memtier_results(experiment_folder):
    for workers in nof_workers:
        avg_ro_results = []

        for clients in nof_clients_per_thread:
            ro_run_results = []
            for run in range(lower_run_id, upper_run_id + 1):
                ro_parse = parse_memtier_single_run_with_workers(experiment_folder, 1, 1, clients, workers, run, 'ro').clean_trace(nof_memtier_startups, nof_memtier_cooldowns)
                ro_parse.average_latency_ops_sum_windows()
                ro_run_results.append(ro_parse)

            # average over the runs
            avg_ro_results.append(average_memtier_results(ro_run_results))

        plotter.figure(7)
        plotter.errorbar(nof_clients, [res.total_avg_st for res in avg_ro_results], yerr=[res.err_st for res in avg_ro_results], fmt='o-', label="{} MW Threads".format(workers), capsize=3)
        plotter.figure(8)
        plotter.errorbar(nof_clients, [res.total_avg_tps for res in avg_ro_results],
                         yerr=[res.err_tps for res in avg_ro_results], fmt='o-', label="{} MW Threads".format(workers),
                         capsize=3)
        
        append_memtier_result("read-only memtier worker: {}".format(workers), nof_clients, avg_ro_results, "baseline_with_mw/one-mw-plot-data")


def main():
    experiment_folder = os.path.abspath(sys.argv[1])
    setup_plots(1, nof_clients,"MW result for a write-only payload", "#Virtual Clients",  "Average Response Time [ms]")
    setup_plots(2, nof_clients,"MW result for a write-only payload", "#Virtual Clients", "Transactions per Second")
    setup_plots(3, nof_clients,"MW result for a read-only payload", "#Virtual Clients", "Average Response Time [ms]")
    setup_plots(4, nof_clients,"MW result for a read-only payload", "#Virtual Clients", "Transactions per Second")

    setup_plots(5, nof_clients,"Memtier result for a write-only payload", "#Virtual Clients",  "Average Response Time [ms]")
    setup_plots(6, nof_clients,"Memtier result for a write-only payload", "#Virtual Clients",  "Transactions per Second")
    setup_plots(7, nof_clients,"Memtier result for a read-only payload", "#Virtual Clients",  "Average Response Time [ms]")
    setup_plots(8, nof_clients,"Memtier result for a read-only payload", "#Virtual Clients",  "Transactions per Second")

    plot_ro_results(experiment_folder)
    plot_wo_results(experiment_folder)
    plot_ro_memtier_results(experiment_folder)
    plot_wo_memtier_results(experiment_folder)

    finish_plots(8)


if __name__ == "__main__":
    main()
