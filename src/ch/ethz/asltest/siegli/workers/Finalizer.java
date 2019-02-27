package ch.ethz.asltest.siegli.workers;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedList;
import java.util.List;
import java.util.Timer;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import ch.ethz.asltest.siegli.MyMiddleware;


/***
 * This class takes care of summarizing the collected data during the experiment into a text file. It's run method is called upon middleware shutdown.
 * Summarizing means collecting all Statistic from the workers and printing them. Additionally we directly aggregate them by calculating the
 * averages and sums over the Statistics of the individual worker threads.
 * @author siegli
 *
 */
public class Finalizer extends Thread {
	
	private static final Logger INFO_LOGGER = LogManager.getLogger(MyMiddleware.INFO_LOGGER_NAME);
	private static final Logger TIMING_LOGGER = LogManager.getLogger(MyMiddleware.TIMING_LOGGER_NAME);
	
	private WorkerPool workerPool;
	private ArrayList<Worker> workers;
	private Timer statisticTimer;
	
	public Finalizer(WorkerPool workerPool, Timer statisticTimer) {
		this.workerPool = workerPool;
		this.workers = workerPool.getPool();
		this.statisticTimer = statisticTimer;
	}

	@Override
	public void run() {
		super.run();
		INFO_LOGGER.info("Shutting down statistic timer");
		statisticTimer.cancel();
		INFO_LOGGER.info("Shutting down pool");
		workerPool.shutdown();
		INFO_LOGGER.info("Shuting down pool finished");
		
		INFO_LOGGER.info("Printing Summary Statistics.");	
		printThinkTime();
		printSummary();
		INFO_LOGGER.info("Printing Worker Statistics.");	
		printWorkers();
		INFO_LOGGER.info("Merging and Printing Statistics Finished. Shutting down Loggers.");
		LogManager.shutdown();
	}
	
	public void printThinkTime() {
		TIMING_LOGGER.info("============================================================================================================================");
		TIMING_LOGGER.info("Total Nof Connections: " + MyMiddleware.sumConnections);
		TIMING_LOGGER.info("Total avg Think Time: " + MyMiddleware.sumThinkingTime / MyMiddleware.sumConnections);
		TIMING_LOGGER.info("============================================================================================================================");
	}
	
	public void logSettings(String ip, int port, List<String> mcAddresses, int nofThreads, boolean readSharded, long aggregationWindowInSeconds) {
		TIMING_LOGGER.info("============================================================================================================================");
		TIMING_LOGGER.info("                                                  Middleware Settings                                                  ");
		TIMING_LOGGER.info("----------------------------------------------------------------------------------------------------------------------------");
		String settings = String.format("Middleware IP: %s, Port: %s, Threads: %s, Read Sharded: %s", ip, port, nofThreads, readSharded );
		String settings2 = String.format("Servers: %s, Aggregation Window %ss", String.join(", ", mcAddresses), aggregationWindowInSeconds);
		TIMING_LOGGER.info(settings);
		TIMING_LOGGER.info(settings2);
	}

	private void printWorkers() {
		for(Worker worker : workers) {
			printHeader("Worker: " + worker.getName() + " Statistics");
			LinkedList<Statistics> stats = worker.getStatisticsList();
			int windowNr = 1;
			for(Statistics stat : stats) {
				printStatistics(worker.getName(), stat, windowNr);
				windowNr += 1;
			}
			printHistogram(worker.getName(), worker.serviceTimeCounts);
		}
	}

	private void printSummary() {
		printHeader("Summary Statistics");
		Statistics[] mergedStats = mergeWorkerStatistics();
		int windowNr = 1;
		for(Statistics stat : mergedStats) {
			printStatistics("Sum", stat, windowNr);
			windowNr += 1;
		}
		int[] serviceTimeHistogram = mergeHistograms();
		printHistogram("Sum", serviceTimeHistogram);
	}
	


	private void printHeader(String title) {
		TIMING_LOGGER.info("============================================================================================================================");
		String headerTitle = String.format("                                                 %s                                                         ", title);
		TIMING_LOGGER.info(headerTitle);
		TIMING_LOGGER.info("----------------------------------------------------------------------------------------------------------------------------");
		String description = String.format("%-14s %-9s %-9s %-10s %-10s %-10s %-10s %-10s %-12s %-8s %-12s %-12s %-12s %-21s %-21s %-21s %-12s",
				"ID", "[Window]", "Seconds", "Get", "Multiget", "Empty Gets", "Set", "Requests", "avgTP[req/s]", "avgQL", "avgQWT[um]", "avgST[ms]", "avgMWT[ms]", 
				"avgSTGet", "avgSTMulGet", "avgSTSet", "avgNofMulKeys");  
		TIMING_LOGGER.info(description);
	}

	private void printStatistics(String id, Statistics stat, int windowNr) {
		String setSummary = String.format("%-5.2f %-5.2f %-5.1f", stat.avgServiceTimeSet/ 1000000, stat.avgReadingTimeSet/ 1000000, stat.avgNofReadCallsSet);
		String getSummary = String.format("%-5.2f %-5.2f %-5.1f", stat.avgServiceTimeGet/ 1000000, stat.avgReadingTimeGet/ 1000000, stat.avgNofReadCallsGet);
		String mulGetSummary = String.format("%-5.2f %-5.2f %-5.1f", stat.avgServiceTimeMultiget/ 1000000, stat.avgReadingTimeMulGet/ 1000000, stat.avgNofReadCallsMulGet);
		
		String timing = String.format("%-14s %-9s %-9.2f %-10s %-10s %-10s %-10s %-10s %-12.0f %-8.1f %-12.1f %-12.1f %-12.1f %-21s %-21s %-21s %-12.1f", 
				"Stat" + id,  "["+ windowNr +"]", stat.timeDeltaSec, stat.nofGET, 
				stat.nofMULTIGET, stat.nofEmptyResponses, stat.nofSET, stat.nofRequests, stat.avgThroughput, stat.avgQueueLength, 
				stat.avgQueueWaitingTime / 1000, stat.avgServiceTime / 1000000, stat.avgMiddlewareTime / 1000000, 
				getSummary, mulGetSummary, setSummary, stat.avgMultigetSize);
		TIMING_LOGGER.info(timing);		
	}
	
	private void printHistogram(String id, int[] histogram) {
		TIMING_LOGGER.info("----------------------------------------------------------------------------------------------------------------------------");

		for(int slot = 0; slot < histogram.length; slot++ ) {
			int nofOcc = histogram[slot];
			if(nofOcc > 0) {
				float timeMs = ((float) slot) / 10;
				String slotOutput = String.format("%-14s %-10s : %.1f ms", "Hist" + id,  nofOcc, timeMs);
				TIMING_LOGGER.info(slotOutput);	
			}
		}
		TIMING_LOGGER.info("----------------------------------------------------------------------------------------------------------------------------");
	}
	
	private int[] mergeHistograms() {
	    int totalHistogram[] = new int[10000 * MyMiddleware.HISTOGRAM_MAX_SECONDS];

		for(Worker worker : workers) {
			int[] workerHistogram = worker.serviceTimeCounts;
		    Arrays.setAll(totalHistogram, i -> totalHistogram[i] + workerHistogram[i]);
		}
		return totalHistogram;
	}
	
	private Statistics[] mergeWorkerStatistics() {
		int minNofStats = getMinNofStats();
		Statistics[] mergedStats = new Statistics[minNofStats];
		ArrayList<Statistics> workerStats = new ArrayList<>(workers.size());
		
		for(int aggregateWindow = 0; aggregateWindow < minNofStats; aggregateWindow++) {
			for(Worker worker : workers) {
				Statistics currentWindowWorkerStat = worker.getStatisticsList().get(aggregateWindow);
				workerStats.add(currentWindowWorkerStat);
			}
			Statistics merged = mergeStatistics(workerStats);
			mergedStats[aggregateWindow] = merged;
			workerStats.clear();
		}
		
		return mergedStats;
	}
	
	private Statistics mergeStatistics(ArrayList<Statistics> statArr) {
		Statistics mergedStats = new Statistics();
			
		for(Statistics stat : statArr) {
			mergedStats.nofGET += stat.nofGET;
			mergedStats.nofMULTIGET += stat.nofMULTIGET;
			mergedStats.nofEmptyResponses += stat.nofEmptyResponses;
			mergedStats.nofSET += stat.nofSET;
			mergedStats.nofRequests += stat.nofRequests;
		}
		
		double totalNofRequests = mergedStats.nofRequests;
		int nofWorkers = this.workers.size();
		for(Statistics stat : statArr) {
			double requestWeight = stat.nofRequests / totalNofRequests;
			mergedStats.timeDeltaSec += stat.timeDeltaSec / nofWorkers; //abuse the timeDeltaSec field for the average here
			mergedStats.avgThroughput += stat.avgThroughput; //throughput must be summed up
			mergedStats.avgQueueLength += requestWeight * stat.avgQueueLength;
			mergedStats.avgQueueWaitingTime += requestWeight * stat.avgQueueWaitingTime;
			mergedStats.avgServiceTime += requestWeight * stat.avgServiceTime;
			mergedStats.avgMiddlewareTime += requestWeight * stat.avgMiddlewareTime;
			
			//request type individual measurements
			if(mergedStats.nofMULTIGET > 0) {
				double mulGetReqWeight = stat.nofMULTIGET / (double) mergedStats.nofMULTIGET;
				mergedStats.avgMultigetSize += mulGetReqWeight * stat.avgMultigetSize;
				mergedStats.avgServiceTimeMultiget += mulGetReqWeight * stat.avgServiceTimeMultiget;
				mergedStats.avgReadingTimeMulGet += mulGetReqWeight * stat.avgReadingTimeMulGet;
				mergedStats.avgNofReadCallsMulGet += mulGetReqWeight * stat.avgNofReadCallsMulGet;
			}
			if(mergedStats.nofGET > 0) {
				double getReqWeight = stat.nofGET / (double) mergedStats.nofGET;
				mergedStats.avgServiceTimeGet += getReqWeight * stat.avgServiceTimeGet;
				mergedStats.avgReadingTimeGet += getReqWeight * stat.avgReadingTimeGet;
				mergedStats.avgNofReadCallsGet += getReqWeight * stat.avgNofReadCallsGet;
			}
			if(mergedStats.nofSET > 0) {
				double setReqWeight = stat.nofSET / (double) mergedStats.nofSET;
				mergedStats.avgServiceTimeSet += setReqWeight * stat.avgServiceTimeSet;
				mergedStats.avgReadingTimeSet += setReqWeight * stat.avgReadingTimeSet;
				mergedStats.avgNofReadCallsSet += setReqWeight * stat.avgNofReadCallsSet;
			}
		}
		
		return mergedStats;
	}
	
	
	private int getMinNofStats() {
		int minNofStats = workers.get(0).getStatisticsList().size();
		for(Worker worker : workers) {
			int nofStats = worker.getStatisticsList().size();
			if(nofStats != minNofStats) {
				INFO_LOGGER.warn("Workers Statistics list differ in size.");
			}
			if(nofStats < minNofStats) {
				minNofStats = nofStats;
			}
		}
		
		return minNofStats;
	}
	
}
