import matplotlib.pyplot as plotter
from matplotlib.ticker import AutoMinorLocator

clients=[16, 32, 64, 128]

data1=[2.16   ,     2.20    ,    2.56    ,    4.49]
error1=[0.09 ,       0.07   ,     0.08     ,   0.10]
data2=[2.12   ,     2.19 ,       2.72 ,       4.65 ]
error2=[0.05    ,    0.07    ,    0.13     ,   0.13]

plotter.figure(1)
font = {'family': 'normal',
            'weight': 'normal',
            'size': 18}

plotter.rc('font', **font)

plotter.xticks(clients)
plotter.grid(True)
plotter.xlabel("#Virtual Clients")
plotter.ylabel("Average Response Time [ms]")
plotter.title("Avg. Response time relative to #Virtual Clients")

plotter.errorbar(clients, data1, yerr=error1, fmt='ro-', label="one client machine", capsize=3)
plotter.errorbar(clients, data2, yerr=error2, fmt='go-', label="two client machines", capsize=3)

plotter.legend(numpoints=1, loc='best')
plotter.gca().set_ylim(bottom=0)
plotter.gca().set_xlim(left=0)
minor_locator = AutoMinorLocator(2)
plotter.gca().yaxis.set_minor_locator(minor_locator)
plotter.tick_params(axis='y',which='both',bottom='off')
plotter.gca().yaxis.grid(True, which='both')

plotter.show() 



