##############################################################################################
Overview of Project Submission - Silvan Egli - siegli@student.ethz.ch
##############################################################################################

1) Source Code
--------------
Can all be found under https://github.com/silvanegli/ASL17/tree/master/src/ch/ethz/asltest

a) siegli/protocol contains classes related to the memcached protocol
inclusive parsing requests and responses

b) siegli/workers contains all threading related stuff such as the worker
thread implementation.

c) /src/ch/ethz/asltest/siegli/MyMiddleware.java is the main entry point of the middleware


2) Experiment Data
------------------
a) There is one folder for each section of the report which can be found under
https://github.com/silvanegli/ASL17/tree/master/experiment_outputs/useful

b) each folder might contain subfolders for the corresponding individual experiments. They contain:
      i)    *-plot-data.txt file, *-summary-data.txt or plot_data folder which contains the output 
            of the postprocessing scripts. This includes all data used for generating the plots as 
            well as the aggregated memtier and middleware measurements
      ii)   dstat*.txt file for every VM 
      iii)  ping*.txt ping files

c) Each folder contains a .tar file which is a collection of all experimental data of the 
corresponding section. The naming convention for a raw-data log file is the following:
<machine_type>_i<instance>_<experiment_specific_parameters>_run<runID>.log for example
client1_i2_c10_wo_mwt8_run3.log means output of memtier instance 2 (connected to middleware 2)
running on client1. The experiment parameters are write-only payload, 10 virtual clients per
memtier thread, 8 middleware workers and run 3.

3) Scripts
----------
The scripts which were used for postprocessing the experiment data can be found under
https://github.com/silvanegli/ASL17/tree/master/scripts/python_postprocessing 
There is again one folder for each section of the report according to 2a) the scripts can 
be run using python and the corresponding experiment data folder as argument. e.g.
python baseline_one_mw.py baseline_one_mw/

4) Figures
----------
a) All the figures shown and listed in the report can be found in the following directory:
https://github.com/silvanegli/ASL17/tree/master/figures

b) In case the reference to the corresponding data file of a plot should be missing in the report
the file figure_data_references.txt contains a mapping from figures to data files.
