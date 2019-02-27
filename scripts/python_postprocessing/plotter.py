import matplotlib.pyplot as plotter
import operator
import matplotlib.ticker as ticker


def plot_response_time(wo_result_dict, ro_result_dict, nof_clients_list, nof_total_CT, title):
    (wo_nof_clients, wo_results) = zip(*sorted(wo_result_dict.items(), key=operator.itemgetter(0)))
    (ro_nof_clients, ro_results) = zip(*sorted(ro_result_dict.items(), key=operator.itemgetter(0)))
    check_parsed_client_lists(wo_nof_clients, ro_nof_clients, nof_clients_list)

    wo_rt = [r.total_avg_resp for r in wo_results]
    ro_rt = [r.total_avg_resp for r in ro_results]
    wo_rt_stdev = [r.total_avg_resp_stdev for r in wo_results]
    ro_rt_stdev = [r.total_avg_resp_stdev for r in ro_results]

    (interactive_wo_rt, _) = get_interactive_response_time_law(nof_total_CT, wo_result_dict)
    (interactive_ro_rt, _) = get_interactive_response_time_law(nof_total_CT, ro_result_dict)

    nof_clients = [nof_total_CT*clients for clients in nof_clients_list]

    set_big_font()

    #plotter.figure()
    plotter.errorbar(nof_clients, wo_rt, yerr=wo_rt_stdev, fmt='ro-', label="write-only requests", capsize=3)
    plotter.errorbar(nof_clients, ro_rt, yerr=ro_rt_stdev, fmt='go-', label="read-only requests", capsize=3)
    plotter.plot(nof_clients, interactive_wo_rt, linestyle='-', color="lightcoral", marker='o', label="w-o interactive law")
    plotter.plot(nof_clients, interactive_ro_rt, linestyle='-', color="lightgreen", marker='o', label="r-o interactive law")
    plotter.legend(numpoints=1, loc='lower right')

    plotter.xticks(nof_clients)
    plotter.gca().set_ylim(bottom=0)
    plotter.gca().set_xlim(left=0)

    plotter.grid(True)

    plotter.xlabel('#Virtual Clients')
    plotter.ylabel('Average Response Time [ms]')
    plotter.title(title)




def plot_tps(wo_result_dict, ro_result_dict, nof_clients_list, nof_total_CT,  title):
    (wo_nof_clients, wo_results) = zip(*sorted(wo_result_dict.items(), key=operator.itemgetter(0)))
    (ro_nof_clients, ro_results) = zip(*sorted(ro_result_dict.items(), key=operator.itemgetter(0)))
    check_parsed_client_lists(wo_nof_clients, ro_nof_clients, nof_clients_list)

    wo_tps = [r.total_tps for r in wo_results]
    ro_tps = [r.total_tps for r in ro_results]
    wo_tps_stdev = [r.total_tps_stdev for r in wo_results]
    ro_tps_stdev = [r.total_tps_stdev for r in ro_results]

    (_, interactive_wo_tps) = get_interactive_response_time_law(nof_total_CT, wo_result_dict)
    (_, interactive_ro_tps) = get_interactive_response_time_law(nof_total_CT, ro_result_dict)

    nof_clients = [nof_total_CT * clients for clients in nof_clients_list]

    set_big_font()

    #plotter.figure()
    plotter.errorbar(nof_clients, wo_tps, yerr=wo_tps_stdev, fmt='ro-', label="write-only requests", capsize=3)
    plotter.errorbar(nof_clients, ro_tps, yerr=ro_tps_stdev, fmt='go-', label="read-only requests", capsize=3)
    plotter.plot(nof_clients, interactive_wo_tps, linestyle='-', color="lightcoral", marker='o', label="w-o interactive law")
    plotter.plot(nof_clients, interactive_ro_tps, linestyle='-', color="lightgreen", marker='o',
                 label="r-o interactive law")
    plotter.legend(numpoints=1, loc='lower right')

    plotter.xticks(nof_clients)
    plotter.gca().set_ylim(bottom=0)
    plotter.gca().set_xlim(left=0)
    plotter.grid(True)

    plotter.xlabel('#Virtual Clients')
    plotter.ylabel('Transactions per Second')
    plotter.title(title)


def get_interactive_response_time_law(nof_total_CT, result_dict):
    (nof_clients, results) = zip(*sorted(result_dict.items(), key=operator.itemgetter(0)))
    interactive_tps = [ c*nof_total_CT*1000/r.total_avg_resp for (c, r) in zip(nof_clients, results) ]
    interactive_rt = [ c*nof_total_CT*1000/r.total_tps  for (c, r) in zip(nof_clients, results)]

    return interactive_rt, interactive_tps


def check_parsed_client_lists(wo_nof_clients, ro_nof_clients, nof_clients_list):
    if nof_clients_list != list(wo_nof_clients) or list(wo_nof_clients) != list(ro_nof_clients):
        print("WARNING: number of virtual clients do not match")
        print("parsed wo list: " + list(wo_nof_clients))
        print("parsed ro list: " + list(ro_nof_clients))
        print("expected list: " + list(nof_clients_list))


def show_plots():
    plotter.show()


def set_big_font():
    plotter.figure()
    font = {'family' : 'normal',
        'weight' : 'normal',
        'size'   : 18}

    plotter.rc('font', **font)


def setup_plots(figure_idx, x_axis, title, xlabel, ylabel):
    plotter.figure(figure_idx)
    font = {'family': 'normal',
            'weight': 'normal',
            'size': 18}

    plotter.rc('font', **font)

    plotter.xticks(x_axis)
    plotter.grid(True)
    plotter.xlabel(xlabel)
    plotter.ylabel(ylabel)
    plotter.title(title)


def finish_plots(nof_plots):
    for i in range(1, nof_plots + 1):
        plotter.figure(i)
        #font = {'family': 'normal', 'weight': 'normal', size': 12}
        #plotter.rc('font', **font)
        
        plotter.legend(numpoints=1, loc='best')
        plotter.gca().set_ylim(bottom=0)
        #plotter.gca().set_ylim(top=8250)
        #plotter.yticks([1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000])
        #plotter.gca().yaxis.set_major_locator(ticker.MultipleLocator(1000))
        plotter.gca().set_xlim(left=0)


    plotter.show(i)

