import glob, os
import numpy as np

class AggregationWindwow:
    def __init__(self):
        self.nof_gets = -1
        self.nof_multi_gets = -1
        self.nof_sets = -1
        self.nof_empty_resp = -1
        self.nof_req = -1
        self.avg_tp = -1
        self.avg_ql = -1
        self.avg_qwt = -1
        self.avg_st = -1
        self.avg_mwt = -1

        self.avg_st_get = -1
        self.avg_st_mul_get = -1
        self.avg_st_set = -1

        self.avg_pt_get = -1
        self.avg_pt_mul_get = -1
        self.avg_pt_set = -1

        self.avg_nof_read_get = -1
        self.avg_nof_read_mul_get = -1
        self.avg_nof_read_set = -1

        self.avg_nof_multi_keys = -1

    def __str__(self):
        # data_points = '[' + '; '.join("%s" %datapoint for datapoint in self.data_points) + ']'
        attrs = vars(self)
        # attrs.__setitem__('data_points', data_points)
        return ''.join("%s: %s\n" % item for item in sorted(attrs.items()))


class WorkerResult:
    def __init__(self, worker_name):
        self.name = worker_name
        self.windows = []
        self.histogram = []


class MiddlewareResult:

    def __init__(self, path):
        self.path_to_file = path
        self.worker_results = []

        self.total_nof_req = -1

        self.avg_nof_gets = -1
        self.avg_nof_multi_gets = -1
        self.avg_nof_sets = -1
        self.avg_nof_empty_resp = -1

        self.avg_nof_req = -1
        self.std_nof_req = -1

        self.avg_tp = -1
        self.std_tp = -1

        self.avg_ql = -1
        self.std_ql = -1

        self.avg_qwt = -1
        self.std_qwt = -1

        self.avg_st = -1
        self.std_st = -1

        self.avg_mwt = -1
        self.std_mwt = -1

        self.avg_st_get = -1
        self.avg_st_mul_get = -1
        self.avg_st_set = -1

        self.avg_pt_get = -1
        self.avg_pt_mul_get = -1
        self.avg_pt_set = -1

        self.avg_nof_read_get = -1
        self.avg_nof_read_mul_get = -1
        self.avg_nof_read_set = -1

        self.avg_nof_multi_keys = -1

    def get_total_nof_req(self):
        summary_worker = self.worker_results[0]
        return sum([wdw.nof_req for wdw in summary_worker.windows])

    # remove startup and cooldown of the sum trace
    def clean_trace(self, nof_startups, nof_cooldowns):
        sum_result = self.worker_results[0]
        sum_result.windows = sum_result.windows[nof_startups:-nof_cooldowns]


    def average_mw_sum(self):
        sum_result = self.worker_results[0]

        self.avg_nof_gets = np.mean([wdw.nof_gets for wdw in sum_result.windows])
        self.avg_nof_multi_gets = np.mean([wdw.nof_multi_gets for wdw in sum_result.windows])
        self.avg_nof_sets = np.mean([wdw.nof_sets for wdw in sum_result.windows])
        self.avg_nof_empty_resp = np.mean([wdw.nof_empty_resp for wdw in sum_result.windows])

        self.avg_nof_req = np.mean([wdw.nof_req for wdw in sum_result.windows])
        self.std_nof_req = np.std([wdw.nof_req for wdw in sum_result.windows])

        self.avg_tp = np.mean([wdw.avg_tp for wdw in sum_result.windows])
        self.std_tp = np.std([wdw.avg_tp for wdw in sum_result.windows])

        self.avg_ql = np.mean([wdw.avg_ql for wdw in sum_result.windows])
        self.std_ql = np.std([wdw.avg_ql for wdw in sum_result.windows])

        self.avg_qwt = np.mean([wdw.avg_qwt for wdw in sum_result.windows])
        self.std_qwt = np.std([wdw.avg_qwt for wdw in sum_result.windows])

        self.avg_st = np.mean([wdw.avg_st for wdw in sum_result.windows])
        self.std_st = np.std([wdw.avg_st for wdw in sum_result.windows])

        self.avg_mwt = np.mean([wdw.avg_mwt for wdw in sum_result.windows])
        self.std_mwt = np.std([wdw.avg_mwt for wdw in sum_result.windows])

        self.avg_st_get = np.mean([wdw.avg_st_get for wdw in sum_result.windows])
        self.avg_st_mul_get = np.mean([wdw.avg_st_mul_get for wdw in sum_result.windows])
        self.avg_st_set = np.mean([wdw.avg_st_set for wdw in sum_result.windows])

        self.avg_pt_get = np.mean([wdw.avg_pt_get for wdw in sum_result.windows])
        self.avg_pt_mul_get = np.mean([wdw.avg_pt_mul_get for wdw in sum_result.windows])
        self.avg_pt_set = np.mean([wdw.avg_pt_set for wdw in sum_result.windows])

        self.avg_nof_read_get = np.mean([wdw.avg_nof_read_get for wdw in sum_result.windows])
        self.avg_nof_read_mul_get = np.mean([wdw.avg_nof_read_mul_get for wdw in sum_result.windows])
        self.avg_nof_read_set = np.mean([wdw.avg_nof_read_set for wdw in sum_result.windows])

        self.avg_nof_multi_keys = np.mean([wdw.avg_nof_multi_keys for wdw in sum_result.windows])


def aggregate_middleware_results(mw_results):
    merged_result = MiddlewareResult("aggregation")

    merged_result.avg_nof_gets = np.sum([res.avg_nof_gets for res in mw_results])
    merged_result.avg_nof_multi_gets = np.sum([res.avg_nof_multi_gets for res in mw_results])
    merged_result.avg_nof_sets = np.sum([res.avg_nof_sets for res in mw_results])
    merged_result.avg_nof_empty_resp = np.sum([res.avg_nof_empty_resp for res in mw_results])

    #other way -----------------------------------------------------------------
    merged_result.avg_nof_req = np.sum([res.avg_nof_req for res in mw_results])
    merged_result.std_nof_req = np.std([res.avg_nof_req for res in mw_results])

    merged_result.avg_tp = np.sum([res.avg_tp for res in mw_results])
    merged_result.std_tp = np.std([res.avg_tp for res in mw_results])

    merged_result.avg_ql = np.mean([res.avg_ql for res in mw_results])
    merged_result.std_ql = np.std([res.avg_ql for res in mw_results])

    merged_result.avg_qwt = np.mean([res.avg_qwt for res in mw_results])
    merged_result.std_qwt = np.std([res.avg_qwt for res in mw_results])

    merged_result.avg_st = np.mean([res.avg_st for res in mw_results])
    merged_result.std_st = np.std([res.avg_st for res in mw_results])

    merged_result.avg_mwt = np.mean([res.avg_mwt for res in mw_results])
    merged_result.std_mwt = np.std([res.avg_mwt for res in mw_results])


    #other way-----------------------------------------------------------
    merged_result.avg_nof_req = np.sum([res.avg_nof_req for res in mw_results])
    merged_result.std_nof_req = np.sqrt(np.mean([np.square(res.std_nof_req) for res in mw_results]))

    merged_result.avg_tp = np.sum([res.avg_tp for res in mw_results])
    merged_result.std_tp = np.sqrt(np.mean([np.square(res.std_tp) for res in mw_results]))

    merged_result.avg_ql = np.mean([res.avg_ql for res in mw_results])
    merged_result.std_ql = np.sqrt(np.mean([np.square(res.std_ql) for res in mw_results]))

    merged_result.avg_qwt = np.mean([res.avg_qwt for res in mw_results])
    merged_result.std_qwt = np.sqrt(np.mean([np.square(res.std_qwt) for res in mw_results]))

    merged_result.avg_st = np.mean([res.avg_st for res in mw_results])
    merged_result.std_st = np.sqrt(np.mean([np.square(res.std_st) for res in mw_results]))

    merged_result.avg_mwt = np.mean([res.avg_mwt for res in mw_results])
    merged_result.std_mwt = np.sqrt(np.mean([np.square(res.std_mwt) for res in mw_results]))
    #-------------------------------------------------------------
    merged_result.avg_st_get = np.mean([res.avg_st_get for res in mw_results])
    merged_result.avg_st_mul_get = np.mean([res.avg_st_mul_get for res in mw_results])
    merged_result.avg_st_set = np.mean([res.avg_st_set for res in mw_results])

    merged_result.avg_pt_get = np.mean([res.avg_pt_get for res in mw_results])
    merged_result.avg_pt_mul_get = np.mean([res.avg_pt_mul_get for res in mw_results])
    merged_result.avg_pt_set = np.mean([res.avg_pt_set for res in mw_results])

    merged_result.avg_nof_read_get = np.mean([res.avg_nof_read_get for res in mw_results])
    merged_result.avg_nof_read_mul_get = np.mean([res.avg_nof_read_mul_get for res in mw_results])
    merged_result.avg_nof_read_set = np.mean([res.avg_nof_read_set for res in mw_results])

    merged_result.avg_nof_multi_keys = np.mean([res.avg_nof_multi_keys for res in mw_results])

    return merged_result



def average_middleware_results(mw_results):
    merged_result = MiddlewareResult("average")

    merged_result.avg_nof_gets = np.mean([res.avg_nof_gets for res in mw_results])
    merged_result.avg_nof_multi_gets = np.mean([res.avg_nof_multi_gets for res in mw_results])
    merged_result.avg_nof_sets = np.mean([res.avg_nof_sets for res in mw_results])
    merged_result.avg_nof_empty_resp = np.mean([res.avg_nof_empty_resp for res in mw_results])


    #other way -----------------------------------------------------------------
    merged_result.avg_nof_req = np.mean([res.avg_nof_req for res in mw_results])
    merged_result.std_nof_req = np.std([res.avg_nof_req for res in mw_results])

    merged_result.avg_tp = np.mean([res.avg_tp for res in mw_results])
    merged_result.std_tp = np.std([res.avg_tp for res in mw_results])

    merged_result.avg_ql = np.mean([res.avg_ql for res in mw_results])
    merged_result.std_ql = np.std([res.avg_ql for res in mw_results])

    merged_result.avg_qwt = np.mean([res.avg_qwt for res in mw_results])
    merged_result.std_qwt = np.std([res.avg_qwt for res in mw_results])

    merged_result.avg_st = np.mean([res.avg_st for res in mw_results])
    merged_result.std_st = np.std([res.avg_st for res in mw_results])

    merged_result.avg_mwt = np.mean([res.avg_mwt for res in mw_results])
    merged_result.std_mwt = np.std([res.avg_mwt for res in mw_results])

    #other way -------------------------------------------
    merged_result.avg_nof_req = np.mean([res.avg_nof_req for res in mw_results])
    merged_result.std_nof_req = np.sqrt(np.mean([np.square(res.std_nof_req) for res in mw_results]))

    merged_result.avg_tp = np.mean([res.avg_tp for res in mw_results])
    merged_result.std_tp = np.sqrt(np.mean([np.square(res.std_tp) for res in mw_results]))

    merged_result.avg_ql = np.mean([res.avg_ql for res in mw_results])
    merged_result.std_ql = np.sqrt(np.mean([np.square(res.std_ql) for res in mw_results]))

    merged_result.avg_qwt = np.mean([res.avg_qwt for res in mw_results])
    merged_result.std_qwt = np.sqrt(np.mean([np.square(res.std_qwt) for res in mw_results]))

    merged_result.avg_st = np.mean([res.avg_st for res in mw_results])
    merged_result.std_st = np.sqrt(np.mean([np.square(res.std_st) for res in mw_results]))

    merged_result.avg_mwt = np.mean([res.avg_mwt for res in mw_results])
    merged_result.std_mwt = np.sqrt(np.mean([np.square(res.std_mwt) for res in mw_results]))
    #------------------------------------------------------------
    merged_result.avg_st_get = np.mean([res.avg_st_get for res in mw_results])
    merged_result.avg_st_mul_get = np.mean([res.avg_st_mul_get for res in mw_results])
    merged_result.avg_st_set = np.mean([res.avg_st_set for res in mw_results])

    merged_result.avg_pt_get = np.mean([res.avg_pt_get for res in mw_results])
    merged_result.avg_pt_mul_get = np.mean([res.avg_pt_mul_get for res in mw_results])
    merged_result.avg_pt_set = np.mean([res.avg_pt_set for res in mw_results])

    merged_result.avg_nof_read_get = np.mean([res.avg_nof_read_get for res in mw_results])
    merged_result.avg_nof_read_mul_get = np.mean([res.avg_nof_read_mul_get for res in mw_results])
    merged_result.avg_nof_read_set = np.mean([res.avg_nof_read_set for res in mw_results])

    merged_result.avg_nof_multi_keys = np.mean([res.avg_nof_multi_keys for res in mw_results])

    return merged_result

'''
    def average_tps_mwt_sum_windows(self):
        sum_result = self.worker_results[0]

        avg_tps = np.mean([wdw.avg_tp for wdw in sum_result.windows])
        err_tps = np.std([wdw.avg_tp for wdw in sum_result.windows])
        avg_mwt = np.mean([wdw.avg_mwt for wdw in sum_result.windows])
        err_mwt = np.std([wdw.avg_mwt for wdw in sum_result.windows])
        self.total_avg_tps = avg_tps
        self.total_avg_st = avg_mwt
        self.err_tps = err_tps
        self.err_st  = err_mwt

        return avg_tps, err_tps, avg_mwt, err_mwt
'''

def parse_mw_single_run(directory, middleware_nr,  nof_clients, nof_workers, runId, write_or_readonly):
    filename_pattern = '{}/mw{}_i1_c{}_{}_mwt{}_run{}.log'.format(directory, middleware_nr, nof_clients, write_or_readonly, nof_workers, runId)
    return parse_mw_single_custom_file(filename_pattern)


def parse_mw_single_custom_file(filename):
    run_filenames = glob.glob(filename)

    if len(run_filenames) == 0:
        print"File: {} not found".format(filename)
        return

    with open(run_filenames[0]) as mw_run:
        waiting_for_start = True

        mw_result = MiddlewareResult(filename)

        for line in mw_run:
            if line.startswith("Stat"):
                line_split = line.split()
                if waiting_for_start:
                    worker_result = WorkerResult(worker_name=line_split[0])
                    mw_result.worker_results.append(worker_result)
                    waiting_for_start = False

                agg_wdow = AggregationWindwow()
                agg_wdow.nof_gets = int(line_split[3])
                agg_wdow.nof_multi_gets = int(line_split[4])
                agg_wdow.nof_empty_resp = int(line_split[5])
                agg_wdow.nof_sets = int(line_split[6])
                agg_wdow.nof_req = int(line_split[7])
                agg_wdow.avg_tp = float(line_split[8])
                agg_wdow.avg_ql = float(line_split[9])
                agg_wdow.avg_qwt = float(line_split[10])
                agg_wdow.avg_st = float(line_split[11])
                agg_wdow.avg_mwt = float(line_split[12])

                if len(line_split) > 13:
                    agg_wdow.avg_st_get = float(line_split[13])
                    agg_wdow.avg_st_mul_get = float(line_split[16])
                    agg_wdow.avg_st_set = float(line_split[19])

                    agg_wdow.avg_pt_get = float(line_split[14])
                    agg_wdow.avg_pt_mul_get = float(line_split[17])
                    agg_wdow.avg_pt_set = float(line_split[20])

                    agg_wdow.avg_nof_read_get = float(line_split[15])
                    agg_wdow.avg_nof_read_mul_get = float(line_split[18])
                    agg_wdow.avg_nof_read_set = float(line_split[21])

                    agg_wdow.avg_nof_multi_keys = float(line_split[22])

                if agg_wdow.nof_req > 0:
                    worker_result.windows.append(agg_wdow)

            elif line.startswith("Hist"):
                line_split = line.split()
                counts = int(line_split[1])
                time = float(line_split[3])
                worker_result.histogram.append(tuple((time, counts)))

            else:
                waiting_for_start = True

    return mw_result


def print_mw_experiment(title, clients, mw_results, filename):
    format_i="%12i"
    format_f="%12.2f"
    nof_c = len(clients)
    path="/home/siegli/Code/asl-17/experiment_outputs/useful/" + filename +".txt"
    with open(path, 'a') as f:
        writeline("-------------------------------------------------------------------------------------------------", f)
        writeline(title, f)
        writeline("-------------------------------------------------------------------------------------------------", f)
        writeline("Clients" + format_i * nof_c % tuple(clients), f)
        writeline("-------", f)
        writeline("TP     " + format_i*nof_c % tuple([res.avg_tp for res in mw_results]), f)
        writeline("err    " + format_i*nof_c % tuple([res.std_tp for res in mw_results]), f)

        writeline("QL     " + format_f * nof_c % tuple([res.avg_ql for res in mw_results]), f)
        writeline("err    " + format_f * nof_c % tuple([res.std_ql for res in mw_results]), f)

        writeline("QWT    " + format_f * nof_c % tuple([res.avg_qwt / 1000 for res in mw_results]), f)
        writeline("err    " + format_f * nof_c % tuple([res.std_qwt / 1000 for res in mw_results]), f)

        writeline("ST     " + format_f * nof_c % tuple([res.avg_st for res in mw_results]), f)
        writeline("err    " + format_f * nof_c % tuple([res.std_st for res in mw_results]), f)

        writeline("MWT    " + format_f * nof_c % tuple([res.avg_mwt for res in mw_results]), f)
        writeline("err    " + format_f * nof_c % tuple([res.std_mwt for res in mw_results]), f)

        writeline("REQ    " + format_i * nof_c % tuple([res.avg_nof_req for res in mw_results]), f)
        writeline("err    " + format_i * nof_c % tuple([res.std_nof_req for res in mw_results]), f)

        writeline("GET    " + format_i * nof_c % tuple([res.avg_nof_gets for res in mw_results]), f)

        writeline("MUL    " + format_i * nof_c % tuple([res.avg_nof_multi_gets for res in mw_results]), f)

        writeline("SET    " + format_i * nof_c % tuple([res.avg_nof_sets for res in mw_results]), f)

        writeline("EMPTY  " + format_i * nof_c % tuple([res.avg_nof_empty_resp for res in mw_results]), f)


def print_mw_experiment_extended(title, first_row, header_first_row, mw_results, filename):
    format_i="%12i"
    format_f="%12.1f"
    nof_c = len(first_row)
    path="/home/siegli/Code/asl-17/experiment_outputs/useful/" + filename +".txt"
    with open(path, 'a') as f:
        writeline("-------------------------------------------------------------------------------------------------", f)
        writeline(title, f)
        writeline("-------------------------------------------------------------------------------------------------", f)
        writeline(header_first_row + format_i * nof_c % tuple(first_row), f)
        writeline("-------", f)
        writeline("TP      " + format_i*nof_c % tuple([res.avg_tp for res in mw_results]), f)
        writeline("err     " + format_i*nof_c % tuple([res.std_tp for res in mw_results]), f)
        writeline("---", f)
        writeline("MWT     " + format_f * nof_c % tuple([res.avg_mwt for res in mw_results]), f)
        writeline("err     " + format_f * nof_c % tuple([res.std_mwt for res in mw_results]), f)
        writeline("---", f)
        writeline("QL      " + format_f * nof_c % tuple([res.avg_ql for res in mw_results]), f)
        writeline("err     " + format_f * nof_c % tuple([res.std_ql for res in mw_results]), f)
        writeline("---", f)
        writeline("QWT     " + format_f * nof_c % tuple([res.avg_qwt / 1000 for res in mw_results]), f)
        writeline("err     " + format_f * nof_c % tuple([res.std_qwt / 1000 for res in mw_results]), f)
        writeline("---", f)
        writeline("ST      " + format_f * nof_c % tuple([res.avg_st for res in mw_results]), f)
        writeline("err     " + format_f * nof_c % tuple([res.std_st for res in mw_results]), f)
        writeline("---", f)
        writeline("ST GET  " + format_f * nof_c % tuple([res.avg_st_get for res in mw_results]), f)
        writeline("RT GET  " + format_f * nof_c % tuple([res.avg_pt_get for res in mw_results]), f)
        writeline("#R GET  " + format_f * nof_c % tuple([res.avg_nof_read_get for res in mw_results]), f)
        writeline("---", f)
        writeline("ST MUL  " + format_f * nof_c % tuple([res.avg_st_mul_get for res in mw_results]), f)
        writeline("RT MUL  " + format_f * nof_c % tuple([res.avg_pt_mul_get for res in mw_results]), f)
        writeline("#R MUL  " + format_f * nof_c % tuple([res.avg_nof_read_mul_get for res in mw_results]), f)
        writeline("---", f)
        writeline("ST SET  " + format_f * nof_c % tuple([res.avg_st_set for res in mw_results]), f)
        writeline("RT SET  " + format_f * nof_c % tuple([res.avg_pt_set for res in mw_results]), f)
        writeline("#R SET  " + format_f * nof_c % tuple([res.avg_nof_read_set for res in mw_results]), f)
        writeline("---", f)
        writeline("REQ     " + format_i * nof_c % tuple([res.avg_nof_req for res in mw_results]), f)
        writeline("err     " + format_i * nof_c % tuple([res.std_nof_req for res in mw_results]), f)
        writeline("---", f)
        writeline("GET     " + format_i * nof_c % tuple([res.avg_nof_gets for res in mw_results]), f)
        writeline("---", f)
        writeline("MUL     " + format_i * nof_c % tuple([res.avg_nof_multi_gets for res in mw_results]), f)
        writeline("MUL len " + format_i * nof_c % tuple([res.avg_nof_multi_keys for res in mw_results]), f)
        writeline("---", f)
        writeline("SET     " + format_i * nof_c % tuple([res.avg_nof_sets for res in mw_results]), f)
        writeline("---", f)
        writeline("EMPTY   " + format_i * nof_c % tuple([res.avg_nof_empty_resp for res in mw_results]), f)


def writeline(string, file):
    file.write(string + os.linesep)