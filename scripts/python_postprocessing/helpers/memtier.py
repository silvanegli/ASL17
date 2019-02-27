import glob
import numpy as np
import re
import os


class MemtierAggregationWindwow:
    def __init__(self):
        self.ops = -1
        self.latency = -1

    def __str__(self):
        # data_points = '[' + '; '.join("%s" %datapoint for datapoint in self.data_points) + ']'
        attrs = vars(self)
        # attrs.__setitem__('data_points', data_points)
        return ''.join("%s: %s\n" % item for item in sorted(attrs.items()))


class MemtierResult:
    def __init__(self, path):
        self.path_to_file = path
        self.aggregation_windows = []
        self.total_nof_requests = -1
        self.total_avg_tps = -1
        self.total_avg_st = -1
        self.err_tps = -1
        self.err_st  = -1

        self.avg_get_latency = -1
        self.avg_set_latency = -1
        self.get_histogram = []
        self.set_histogram = []

        self.avg_get_percentiles = []
        self.avg_set_percentiles = []


    # remove startup and cooldown of the sum trace
    def clean_trace(self, nof_startups, nof_cooldowns):
        self.aggregation_windows = self.aggregation_windows[nof_startups:-nof_cooldowns]
        return self

    def average_latency_ops_sum_windows(self):
        avg_tps = np.mean([wdw.ops for wdw in self.aggregation_windows])
        err_tps = np.std([wdw.ops for wdw in self.aggregation_windows])
        avg_st = np.mean([wdw.latency for wdw in self.aggregation_windows])
        err_st = np.std([wdw.latency for wdw in self.aggregation_windows])
        self.total_avg_tps = avg_tps
        self.total_avg_st = avg_st
        self.err_tps = err_tps
        self.err_st  = err_st

        return avg_tps, err_tps, avg_st, err_st

    def get_get_percentile(self, percentile):
        for (latency, percentage) in self.get_histogram:
            if percentage >= percentile:
                weight = (percentile - prev_percentage) / (percentage - prev_percentage)
                return prev_latency + weight * (latency - prev_latency)
            else:
                prev_latency = latency
                prev_percentage = percentage

    def get_set_percentile(self, percentile):
        for (latency, percentage) in self.set_histogram:
            if percentage >= percentile:
                weight = (percentile - prev_percentage) / (percentage - prev_percentage)
                return prev_latency + weight * (latency - prev_latency)
            else:
                prev_latency = latency
                prev_percentage = percentage


def parse_memtier_single_run_with_workers(directory, client_nr, instance_nr, nof_clients, nof_workers, runId, write_or_readonly):
    filename_pattern = '{}/client{}_i{}_c{}_{}_mwt{}_run{}.log'.format(directory, client_nr, instance_nr, nof_clients, write_or_readonly, nof_workers, runId)
    print(filename_pattern)
    run_filenames = glob.glob(filename_pattern)

    if len(run_filenames) == 0:
        print"File: {} not found".format(filename_pattern)
        return

    with open(run_filenames[0]) as mw_run:
        memtier_result = MemtierResult(filename_pattern)

        pattern = re.compile("\[RUN.*secs\]")

        for line in mw_run:
            if pattern.match(line):
                windows = line.split("\r")[:-1]
                for wdw in windows:
                    wdw_split = wdw.split()
                    agg_wdow = MemtierAggregationWindwow()
                    agg_wdow.ops = float(wdw_split[9])
                    agg_wdow.latency = float(wdw_split[16])
                    memtier_result.aggregation_windows.append(agg_wdow)

    return memtier_result


def parse_memtier_single_run(directory, client_nr, instance_nr, nof_clients, runId, write_or_readonly):
    filename_pattern = '{}/mw{}_i{}_c{}_{}_r{}.log'.format(directory, client_nr, instance_nr, nof_clients, write_or_readonly, runId)
    print(filename_pattern)
    run_filenames = glob.glob(filename_pattern)

    with open(run_filenames[0]) as mw_run:
        memtier_result = MemtierResult(filename_pattern)

        pattern = re.compile("\[RUN.*secs\]")

        for line in mw_run:
            if pattern.match(line):
                windows = line.split("\r")[:-1]
                for wdw in windows:
                    wdw_split = wdw.split()
                    agg_wdow = MemtierAggregationWindwow()
                    agg_wdow.ops = float(wdw_split[9])
                    agg_wdow.latency = float(wdw_split[16])
                    memtier_result.aggregation_windows.append(agg_wdow)

    return memtier_result


def parse_memtier_custom(filename):
    with open(filename) as mw_run:
        memtier_result = MemtierResult(filename)

        wdw_pattern = re.compile("\[RUN.*secs\]")
        set_hist_pattern = re.compile("SET")
        get_hist_pattern = re.compile("GET")
        set_latency_pattern = re.compile("Sets")
        get_latency_pattern = re.compile("Gets")

        for line in mw_run:
            if wdw_pattern.match(line):
                windows = line.split("\r")[:-1]
                for wdw in windows:
                    wdw_split = wdw.split()
                    agg_wdow = MemtierAggregationWindwow()
                    agg_wdow.ops = float(wdw_split[9])
                    agg_wdow.latency = float(wdw_split[16])
                    memtier_result.aggregation_windows.append(agg_wdow)
                    current_nof_ops = int(wdw_split[7])
                    memtier_result.total_nof_requests = current_nof_ops

            elif set_latency_pattern.match(line):
                summary = line.split()
                memtier_result.avg_set_latency = float(summary[4])

            elif get_latency_pattern.match(line):
                summary = line.split()
                memtier_result.avg_get_latency = float(summary[4])

            elif set_hist_pattern.match(line):
                hist_entry = line.split()
                hist_tuple = (float(hist_entry[1]), float(hist_entry[2]))
                memtier_result.set_histogram.append(hist_tuple)

            elif get_hist_pattern.match(line):
                hist_entry = line.split()
                hist_tuple = (float(hist_entry[1]), float(hist_entry[2]))
                memtier_result.get_histogram.append(hist_tuple)

    return memtier_result



def average_memtier_results(memtier_results):
    merged_result = MemtierResult("merge")

    merged_result.total_avg_tps = np.mean([res.total_avg_tps for res in memtier_results])
    merged_result.total_avg_st = np.mean([res.total_avg_st for res in memtier_results])


    merged_result.err_tps = np.std([res.total_avg_tps for res in memtier_results])
    merged_result.err_st = np.std([res.total_avg_st for res in memtier_results])


    merged_result.err_tps = np.sqrt(np.mean([np.square(res.err_tps) for res in memtier_results]))
    merged_result.err_st = np.sqrt(np.mean([np.square(res.err_st) for res in memtier_results]))

    return merged_result


def aggregate_memtier_results(memtier_results):
    merged_result = MemtierResult("aggreation")

    merged_result.total_avg_tps = np.sum([res.total_avg_tps for res in memtier_results])
    merged_result.total_avg_st = np.mean([res.total_avg_st for res in memtier_results])


    merged_result.err_tps = np.std([res.total_avg_tps for res in memtier_results])
    merged_result.err_st = np.std([res.total_avg_st for res in memtier_results])


    merged_result.err_tps = np.sqrt(np.mean([np.square(res.err_tps) for res in memtier_results]))
    merged_result.err_st = np.sqrt(np.mean([np.square(res.err_st) for res in memtier_results]))



    return merged_result


def print_data(title, clients, memtier_points, filename):
    format_i="%12i"
    format_f="%12.2f"
    nof_c = len(clients)
    path="/home/siegli/Code/asl-17/experiment_outputs/useful/" + filename +".txt"
    with open(path, 'w') as f:
        writeline("-------------------------------------------------------------------------------------------------", f)
        writeline(title, f)
        writeline("-------------------------------------------------------------------------------------------------", f)
        writeline("Service Time (ms) with errors", f)
        writeline(format_i*nof_c % tuple(clients), f)
        writeline(format_f*nof_c % tuple([res.total_avg_st for res in memtier_points]), f)
        writeline(format_f*nof_c % tuple([res.err_st for res in memtier_points]), f)
        writeline("Troughput (req/sec) with errors", f)
        writeline(format_i*nof_c % tuple(clients), f)
        writeline(format_f*nof_c % tuple([res.total_avg_tps for res in memtier_points]), f)
        writeline(format_f*nof_c % tuple([res.err_tps for res in memtier_points]), f)

def append_data(title, clients, memtier_points, filename):
    format_i="%12i"
    format_f="%12.2f"
    nof_c = len(clients)
    path="/home/siegli/Code/asl-17/experiment_outputs/useful/" + filename +".txt"
    with open(path, 'a') as f:
        writeline("-------------------------------------------------------------------------------------------------", f)
        writeline(title, f)
        writeline("-------------------------------------------------------------------------------------------------", f)
        writeline("Service Time (ms) with errors", f)
        writeline(format_i*nof_c % tuple(clients), f)
        writeline(format_f*nof_c % tuple([res.total_avg_st for res in memtier_points]), f)
        writeline(format_f*nof_c % tuple([res.err_st for res in memtier_points]), f)
        writeline("Troughput (req/sec) with errors", f)
        writeline(format_i*nof_c % tuple(clients), f)
        writeline(format_f*nof_c % tuple([res.total_avg_tps for res in memtier_points]), f)
        writeline(format_f*nof_c % tuple([res.err_tps for res in memtier_points]), f)


def append_latencies(title, keys, get_latencies, get_percentiles, set_latencies, set_percentiles, perc_nr, filename):
    format_i="%12i"
    format_f="%12.2f"
    nof_c = len(keys)
    path="/home/siegli/Code/asl-17/experiment_outputs/useful/" + filename +".txt"
    with open(path, 'a') as f:
        writeline("-------------------------------------------------------------------------------------------------", f)
        writeline(title, f)
        writeline("-------------------------------------------------------------------------------------------------", f)
        writeline("Latencies and Percentiles for GET requests", f)
        writeline("--------", f)
        writeline("Nof Keys  " + format_i*nof_c % tuple(keys), f)
        writeline("Avg.RT Get" + format_f*nof_c % tuple(get_latencies), f)
        for idx, perc in enumerate(perc_nr):
            writeline("{}-Perc   ".format(perc) + format_f * nof_c % tuple([key_perc_list[idx] for key_perc_list in get_percentiles]), f)

        writeline("Latencies and Percentiles for SET requests", f)
        writeline("--------", f)
        writeline("Nof Keys  " + format_i*nof_c % tuple(keys), f)
        writeline("Avg.RT Set" + format_f*nof_c % tuple(set_latencies), f)
        for idx, perc in enumerate(perc_nr):
            writeline("{}-Perc   ".format(perc) + format_f * nof_c % tuple([key_perc_list[idx] for key_perc_list in set_percentiles]), f)





def writeline(string, file):
    file.write(string + os.linesep)

def main():
    mem_res = parse_memtier_custom("/home/siegli/Code/asl-17/experiment_outputs/reads_2017-12-12-17:42/client1_i1_k3_strue_r1.log")
    _25_perc = mem_res.get_set_percentile(25)
    _50_perc = mem_res.get_set_percentile(50)
    _75_perc = mem_res.get_set_percentile(75)
    _99_perc = mem_res.get_set_percentile(99)

    _25_perc = mem_res.get_get_percentile(25)
    _50_perc = mem_res.get_get_percentile(50)
    _75_perc = mem_res.get_get_percentile(75)
    _99_perc = mem_res.get_get_percentile(99)

if __name__ == "__main__":
    main()