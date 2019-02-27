from helpers.memtier import parse_memtier_custom, MemtierResult
from helpers.middleware import parse_mw_single_custom_file, MiddlewareResult
import matplotlib.pyplot as plotter
from matplotlib.ticker import AutoMinorLocator
import numpy as np
import os, sys

run_list = [1, 2, 3]
mw_machine_list = [1]

memtier_machine_list = [1, 2, 3]
memtier_instance_list = [1]

key=12
lower_time_limit = 1
upper_time_limit = 10
#num_bins = 40
bucketsize=0.1

req_type = "both"
set_get_ratio = 1 / 3.

#graph
y_upper_lim = 0.15
x_upper_lim = 10
x_ticks = range(0, x_upper_lim, 1)
show_avg = False

buckets=np.arange(lower_time_limit, upper_time_limit + bucketsize, bucketsize)

def generate_middleware_histogram(experiment_folder, sharded):
    total_nof_req = 0
    merged_histogram = []
    for run in run_list:
        for machine_id in mw_machine_list:
            filename_pattern = '{}/mw{}_i1_k{}_s{}_r{}.log'.format(experiment_folder, machine_id, key, sharded, run)
            mw_result = parse_mw_single_custom_file(filename_pattern)
            new_hist = mw_result.worker_results[0].histogram
            merged_histogram = extend_middleware_samples(merged_histogram, new_hist, upper_time_limit)
            total_nof_req += mw_result.get_total_nof_req()

    print "Total nof req middlewares sharded={} : {}".format(sharded, total_nof_req)
    fig, ax = plotter.subplots()

    # the histogram of the data
    n, bins, patches = ax.hist(merged_histogram, bins=buckets, weights= np.ones_like(merged_histogram)/float(len(merged_histogram)))#, num_bins)#, normed=1)
    if show_avg:
        plotter.axvline(np.mean(merged_histogram), color='y', linestyle='dashed', linewidth=1)
        plotter.axvline(np.median(merged_histogram), color='r', linestyle='dashed', linewidth=1)
    # add a 'best fit' line
    #y = mlab.normpdf(bins, mu, sigma)
    #ax.plot(bins, y, '--')
    plotter.xticks(x_ticks)
    ax.set_ylim(top=y_upper_lim)
    ax.set_xlim(left=0)
    ax.set_xlim(right=x_upper_lim)
    ax.set_xlabel('Response Time [ms]')
    ax.set_ylabel('Relative Occurrence')
    ax.set_title(r'Histogram of Response Times measured on the Middleware, sharded={}'.format(sharded))

    # Tweak spacing to prevent clipping of ylabel
    #fig.tight_layout()


    return merged_histogram


def extend_middleware_samples(current_list, new_list, upper_limit):
    for (time, count) in new_list:
        if time >= upper_limit:
            break
        current_list.extend([time] * count)

    return current_list
'''
def merge_histograms(current_hist, new_hist):
    merge = []
    current_idx = 0
    new_idx = 0

    while current_idx < len(current_hist) or new_idx < new_hist:
        if current_idx >= len(current_hist):
            merge.extend(new_hist[new_idx:])
            break

        if new_idx >= len(new_hist):
            merge.extend(current_hist[current_idx:])
            break

        (curr_time, curr_count) = current_hist[current_idx]
        (new_time, new_count) = new_hist[new_idx]

        if curr_time == new_time:
            merge.append(tuple((curr_time, new_count + curr_count)))
            current_idx += 1
            new_idx += 1
        elif curr_time < new_time:
            merge.append(tuple((curr_time, curr_count)))
            current_idx += 1
        else:
            merge.append(tuple((new_time, new_count)))
            new_idx +=1



    return merge
'''


def generate_memtier_histogram(experiment_folder, sharded):
    merged_histogram = []
    total_nof_req = 0
    for run in run_list:
        for machine in memtier_machine_list:
            for instance in memtier_instance_list:
                filename = "client{}_i{}_k{}_s{}_r{}.log".format(machine, instance, key, sharded, run)
                parsed_memtier = parse_memtier_custom(experiment_folder + "/" + filename)
                total_nof_set = parsed_memtier.total_nof_requests * set_get_ratio
                total_nof_get = parsed_memtier.total_nof_requests * (1 - set_get_ratio)
                if req_type == 'both':
                    total_nof_req += total_nof_get + total_nof_set
                    merged_histogram = extend_memtier_samples(merged_histogram, parsed_memtier.set_histogram, upper_time_limit, total_nof_set)
                    merged_histogram = extend_memtier_samples(merged_histogram, parsed_memtier.get_histogram, upper_time_limit, total_nof_get)
                elif req_type == 'set':
                    merged_histogram = extend_memtier_samples(merged_histogram, parsed_memtier.set_histogram, upper_time_limit, total_nof_set)
                    total_nof_req += total_nof_set
                elif req_type == 'get':
                    total_nof_req += total_nof_get
                    merged_histogram = extend_memtier_samples(merged_histogram, parsed_memtier.get_histogram, upper_time_limit, total_nof_get)
                else:
                    print "Warning, unknown request type: {}".format(req_type)

    print "Total nof req clients sharded={} : {}".format(sharded, total_nof_req)

    fig, ax = plotter.subplots()

    # the histogram of the data
    n, bins, patches = ax.hist(merged_histogram, bins=buckets, weights= np.ones_like(merged_histogram)/float(len(merged_histogram)))#, num_bins)#, normed=1)
    if show_avg:
        plotter.axvline(np.mean(merged_histogram), color='y', linestyle='dashed', linewidth=1)
        plotter.axvline(np.median(merged_histogram), color='r', linestyle='dashed', linewidth=1)

    # add a 'best fit' line
    #y = mlab.normpdf(bins, mu, sigma)
    #ax.plot(bins, y, '--')
    plotter.xticks(x_ticks)
    ax.set_ylim(top=y_upper_lim)
    ax.set_xlim(left=0)
    ax.set_xlim(right=x_upper_lim)
    ax.set_xlabel('Response Time [ms]')
    ax.set_ylabel('Relative Occurrence')
    ax.set_title(r'Histogram of Response Times measured on the Clients, sharded={}'.format(sharded))

    # Tweak spacing to prevent clipping of ylabel
    #fig.tight_layout()



def extend_memtier_samples(current_list, new_list, upper_limit, total_counts):
    last_percentage = 0
    for (time, percentage) in new_list:
        if time >= upper_limit:
            break

        counts = int((percentage - last_percentage) * total_counts / 100)
        current_list.extend([time] * counts)
        last_percentage = percentage
    return current_list


def main():
    exp_folder = os.path.abspath(sys.argv[1])
    #exp_folder = "/home/siegli/Code/asl-17/experiment_outputs/useful/reads/reads_big_latency_16workers"

    font = {'family': 'normal',
            'weight': 'normal',
            'size': 18}

    plotter.rc('font', **font)


    generate_middleware_histogram(exp_folder, "true")
    generate_middleware_histogram(exp_folder, "false")

    generate_memtier_histogram(exp_folder, "true")
    generate_memtier_histogram(exp_folder, "false")

    plotter.show()

if __name__ == "__main__":
    main()
