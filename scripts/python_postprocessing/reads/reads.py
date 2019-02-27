import sys
from helpers.middleware import parse_mw_single_custom_file, aggregate_middleware_results, average_middleware_results
from helpers.middleware import print_mw_experiment_extended as append_mw_result
from helpers.memtier import parse_memtier_custom, MemtierResult, append_latencies
from helpers.memtier import append_data as append_memtier_result
from helpers.memtier import aggregate_memtier_results, average_memtier_results
from matplotlib.ticker import AutoMinorLocator

import numpy as np
from plotter import setup_plots, finish_plots
import os
import matplotlib.pyplot as plotter

run_list = [1, 2, 3]
mw_machine_list = [1, 2]
memtier_machine_list = [1]
memtier_instance_list = [1]

nof_multi_keys = [1, 3, 6, 9, 12]
percentiles = [10, 25, 50, 75, 90, 99]
x_tick_positions = np.linspace(1, 6, num=len(nof_multi_keys))


nof_startups = 2
nof_cooldowns = 2

nof_memtier_startups = 2
nof_memtier_cooldowns = 2

nof_plots = 6

summary_file_name = "reads/summary-plot-reads"



def print_middleware_results(experiment_folder):
    for sharded in ["false", "true"]:
        total_avg_results = []
        avg_singleMw_dict = get_fresh_mw_res_dict()
        for keys in nof_multi_keys:
            run_results = []
            singleMw_run_results_dict = get_fresh_mw_res_dict()
            for run in run_list:
                machine_results = []
                for machine_id in mw_machine_list:
                    filename_pattern = '{}/mw{}_i1_k{}_s{}_r{}.log'.format(experiment_folder, machine_id, keys, sharded, run)
                    mw_result = parse_mw_single_custom_file(filename_pattern)
                    mw_result.clean_trace(nof_startups, nof_cooldowns)
                    mw_result.average_mw_sum()
                    machine_results.append(mw_result)
                    singleMw_run_results_dict[machine_id].append(mw_result)

                #aggregate over mw's
                aggregated_mw_result = aggregate_middleware_results(machine_results)
                run_results.append(aggregated_mw_result)

            # average over the runs
            avg_singleMw_dict[1].append(average_middleware_results(singleMw_run_results_dict[1]))
            avg_singleMw_dict[2].append(average_middleware_results(singleMw_run_results_dict[2]))
            total_avg_results.append(average_middleware_results(run_results))

        for machine_id in mw_machine_list:
            append_mw_result("middleware {} result, sharded : {} ".format(machine_id, sharded), nof_multi_keys, "Nof Keys",  avg_singleMw_dict[machine_id], summary_file_name)

        append_mw_result("merged middleware result, sharded : {} ".format(sharded), nof_multi_keys, "Nof Keys",  total_avg_results, summary_file_name)



def print_memtier_results(title, memtier_results):
    get_latencies = [res.avg_get_latency for res in memtier_results]
    set_latencies = [res.avg_set_latency for res in memtier_results]

    get_percentiles = [res.avg_get_percentiles for res in memtier_results]
    set_percentiles = [res.avg_set_percentiles for res in memtier_results]

    append_latencies(title=title, keys=nof_multi_keys, get_latencies=get_latencies, set_latencies=set_latencies,
                     get_percentiles=get_percentiles, set_percentiles=set_percentiles, perc_nr=percentiles,
                     filename=summary_file_name)


def parse_and_merge_memtier_results(experiment_folder, sharded):
    merged_memtier_results = []
    for keys in nof_multi_keys:
        merged_memtier_result = MemtierResult("merged")
        memtier_results = []
        for run in run_list:
            for machine in memtier_machine_list:
                for instance in memtier_instance_list:
                    filename = "client{}_i{}_k{}_s{}_r{}.log".format(machine, instance, keys, sharded, run)
                    parsed_memtier = parse_memtier_custom(experiment_folder + "/" + filename)
                    parsed_memtier.clean_trace(nof_memtier_startups, nof_memtier_cooldowns).average_latency_ops_sum_windows()
                    memtier_results.append(parsed_memtier)

        merged_memtier_result.avg_get_latency = np.mean([res.avg_get_latency for res in memtier_results])
        merged_memtier_result.avg_set_latency = np.mean([res.avg_set_latency for res in memtier_results])

        merged_get_perc_list = []
        merged_set_perc_list = []
        for perc in percentiles:
            avg_get_perc = np.mean([res.get_get_percentile(perc) for res in memtier_results])
            merged_get_perc_list.append(avg_get_perc)
            avg_set_perc = np.mean([res.get_set_percentile(perc) for res in memtier_results])
            merged_set_perc_list.append(avg_set_perc)

        merged_memtier_result.avg_get_percentiles = merged_get_perc_list
        merged_memtier_result.avg_set_percentiles = merged_set_perc_list

        merged_memtier_results.append(merged_memtier_result)


    return merged_memtier_results


def plot_memtier_results(sharded_memtier_results, non_sharded_memtier_results, fliers=True):
    font = {'family': 'normal',
            'weight': 'normal',
            'size': 18}

    plotter.rc('font', **font)

    fig_merged_get, ax_mixed_get = plotter.subplots()
    plotter.title('Average Response Time of the GET requests for Non-Sharded and Sharded Middleware ')

    fig_merged_set, ax_mixed_set = plotter.subplots()
    plotter.title('Average Response Time of the Set requests for Non-Sharded and Sharded Middleware')

    flierprops = dict(marker='_', markerfacecolor='black', markersize=15,
                      linestyle='None')

    sharded=["Non-Sharded", "Sharded"]
    for shard_index, memtier_results in enumerate((non_sharded_memtier_results, sharded_memtier_results)):
        get_latencies = [res.avg_get_latency for res in memtier_results]
        set_latencies = [res.avg_set_latency for res in memtier_results]

        get_percentiles = [res.avg_get_percentiles for res in memtier_results]
        set_percentiles = [res.avg_set_percentiles for res in memtier_results]

        _99_get_perc_list = []
        _99_set_perc_list = []

        for i in range(0, len(get_percentiles)):
            if fliers:
                _99_get_perc_list.append(get_percentiles[i][-1])
                _99_set_perc_list.append(set_percentiles[i][-1])
            del get_percentiles[i][-1]
            del set_percentiles[i][-1]

        shard = sharded[shard_index]
        fig, ax = plotter.subplots()
        plotter.title('Avg. Response Time of the GET requests, {} Middleware'.format(shard))
        customized_box_plot(get_percentiles, ax, means=get_latencies, fliers=_99_get_perc_list, redraw=True,
                            notch=0, flierprops=flierprops, vert=1, whis=1.5, meanline=True, showmeans=True, positions=x_tick_positions, widths=0.5)
        set_axis_label()
        fig, ax = plotter.subplots()
        plotter.title('Avg. Response Time of the Set requests, {} Middleware'.format(shard))
        customized_box_plot(set_percentiles, ax, means=set_latencies, fliers=_99_set_perc_list, redraw=True,
                            notch=0, flierprops=flierprops, vert=1, whis=1.5, meanline=True, showmeans=True, positions=x_tick_positions, widths=0.5)
        set_axis_label()
        pos_mod = shard_index * 2 -1
        pos_mod *= 0.2

        bp = customized_box_plot(get_percentiles, ax_mixed_get, means=get_latencies, fliers=_99_get_perc_list, redraw=True,
                            fill_color='pink', notch=0, flierprops=flierprops, vert=1, whis=1.5, meanline=True, showmeans=True,
                            positions=[pos + pos_mod for pos in x_tick_positions], widths=0.3)

        bp = customized_box_plot(set_percentiles, ax_mixed_set, means=set_latencies, fliers=_99_set_perc_list, redraw=True,
                            fill_color='lightgreen', notch=0, flierprops=flierprops, vert=1, whis=1.5, meanline=True, showmeans=True,
                            positions=[pos + pos_mod for pos in x_tick_positions], widths=0.3)


    plotter.figure(fig_merged_get.number)
    plotter.xticks(x_tick_positions, ['{} keys'.format(k) for k in nof_multi_keys])
    set_axis_label()
    plotter.figure(fig_merged_set.number)
    plotter.xticks(x_tick_positions, ['{} keys'.format(k) for k in nof_multi_keys])
    set_axis_label()

    plotter.show()


def set_axis_label():
    plotter.xlabel("Number of Keys used in the Multiget Requests")
    plotter.ylabel("Average Response Time [ms]")


def get_fresh_mw_res_dict():
    res_dict = dict()
    res_dict[1] = []
    res_dict[2] = []
    return res_dict


def customized_box_plot(perc, axes, means, fliers, redraw = True, fill_color=None, *args, **kwargs):
    """
    Generates a customized boxplot based on the given percentile values
    """

    box_plot = axes.boxplot([[-9, -4, 2, 4, 9],]*len(nof_multi_keys), *args, **kwargs)
    # Creates len(percentiles) no of box plots

    min_y, max_y = float('inf'), -float('inf')

    for box_no, (q1_start,
                 q2_start,
                 q3_start,
                 q4_start,
                 q4_end) in enumerate(perc):

        # Lower cap
        box_plot['caps'][2*box_no].set_ydata([q1_start, q1_start])
        # xdata is determined by the width of the box plot

        # Lower whiskers
        box_plot['whiskers'][2*box_no].set_ydata([q1_start, q2_start])

        # Higher cap
        box_plot['caps'][2*box_no + 1].set_ydata([q4_end, q4_end])

        # Higher whiskers
        box_plot['whiskers'][2*box_no + 1].set_ydata([q4_start, q4_end])


        # Box
        box_plot['boxes'][box_no].set_ydata([q2_start,
                                             q2_start,
                                             q4_start,
                                             q4_start,
                                             q2_start])


        # Median
        box_plot['medians'][box_no].set_ydata([q3_start, q3_start])

        box_plot['means'][box_no].set_ydata([means[box_no], means[box_no]])

        if len(fliers) != 0:
            box_plot['fliers'][box_no].set(xdata=kwargs['positions'], ydata=fliers)
            max_y = max(q4_end, max_y, max(fliers))

        else:
            max_y = max(q4_end, max_y)

        #min_y = 0
        min_y = min(q1_start, min_y)

        # The y axis is rescaled to fit the new box plot completely with 10%
        # of the maximum value at both ends
        axes.set_ylim([min_y * 0.9, max_y * 1.1])
        #minor_locator = AutoMinorLocator(2)
        #axes.yaxis.set_minor_locator(minor_locator)
        axes.yaxis.grid(True, which='both')

        plotter.xticks(x_tick_positions, ['{} keys'.format(k) for k in nof_multi_keys])

    # If redraw is set to true, the canvas is updated.
    if redraw:
        axes.figure.canvas.draw()
        axes.set_xlim(left=0)

    return box_plot


def main():
    #exp_folder = os.path.abspath(sys.argv[1])
    exp_folder = "/home/siegli/Code/asl-17/experiment_outputs/useful/reads/reads_big_latency_16workers"

    print_middleware_results(exp_folder)

    sharded_results = parse_and_merge_memtier_results(exp_folder, "true")
    print_memtier_results("client result: Sharded Latencies averaged over 3 runs", sharded_results)
    non_sharded_results = parse_and_merge_memtier_results(exp_folder, "false")
    print_memtier_results("client result: Non-Sharded Latencies averaged over 3 runs", non_sharded_results)

    plot_memtier_results(sharded_results, non_sharded_results,  False)




if __name__ == "__main__":
    main()

#https://stackoverflow.com/questions/27214537/is-it-possible-to-draw-a-matplotlib-boxplot-given-the-percentile-values-insteadhttps://stackoverflow.com/questions/27214537/is-it-possible-to-draw-a-matplotlib-boxplot-given-the-percentile-values-instead