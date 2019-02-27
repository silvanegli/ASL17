package ch.ethz.asltest.siegli.workers;

import org.apache.logging.log4j.LogManager;

import org.apache.logging.log4j.Logger;

import ch.ethz.asltest.siegli.MyMiddleware;
import ch.ethz.asltest.siegli.protocol.MemcachedTask;

/***
 * A collection of all measurements we need to keep track of. For every MyMiddleware.STATISTIC_AGGREGATION_WINDOW the current object in every worker is
 * put into a "history" and replaced by a new one. It provides basic functionality for updating the averages in an online fashion.
 * @author siegli
 *
 */
public class Statistics {
	
	private static final Logger ERROR_LOGGER = LogManager.getLogger(MyMiddleware.ERROR_LOGGER_NAME);
	private static final Logger INFO_LOGGER = LogManager.getLogger(MyMiddleware.INFO_LOGGER_NAME);
	private static final int  MAX_SERVICE_COUNT_INDEX = 10000 * MyMiddleware.HISTOGRAM_MAX_SECONDS - 1;
	
	public long startTimestamp;
	public long stopTimestamp;
	public double timeDeltaSec;

	public long nofGET;
	public long nofMULTIGET;
	public long nofSET;
	public long nofRequests;
	public long nofEmptyResponses;
	
	
	public double avgMultigetSize;
	public double avgThroughput;
	public double avgQueueLength;
	
	public double avgQueueWaitingTime;
	public double avgServiceTime;
	public double avgMiddlewareTime;
		
	public double avgServiceTimeGet;
	public double avgReadingTimeGet;
	public double avgNofReadCallsGet;
	
	public double avgServiceTimeMultiget;
	public double avgReadingTimeMulGet;
	public double avgNofReadCallsMulGet;
	
	public double avgServiceTimeSet;
	public double avgReadingTimeSet;
	public double avgNofReadCallsSet;
	
	public Statistics() {
		startTimestamp = System.nanoTime();
		nofEmptyResponses = 0;
		nofGET = 0;
		nofMULTIGET = 0;
		avgMultigetSize = 0;
		nofSET = 0;
		nofRequests = 0;
		avgQueueLength = 0;
		avgQueueWaitingTime = 0;
		avgServiceTime = 0;
		avgServiceTimeGet = 0;
		avgServiceTimeMultiget = 0;
		avgServiceTimeSet = 0;
		avgReadingTimeGet = 0;
		avgNofReadCallsGet = 0;
		avgReadingTimeMulGet = 0;
		avgNofReadCallsMulGet = 0;
		avgReadingTimeSet = 0;
		avgNofReadCallsSet = 0;
	}

	public void updateStatistics(MemcachedTask task, int[] serviceTimeCounts) {
		nofRequests += 1;
		long serviceTime = task.stopTimeServer - task.startTimeServer;
		avgServiceTime = updateAvg(avgServiceTime, serviceTime, nofRequests);
		long mwTime = task.stopTimeMiddleWare - task.startTimeMiddleWare; 
		avgMiddlewareTime = updateAvg(avgMiddlewareTime, mwTime, nofRequests);
		long mwTime100us = mwTime / 100000;
		try {
			serviceTimeCounts[(int) mwTime100us] += 1;
		} catch (ArrayIndexOutOfBoundsException e) {
			serviceTimeCounts[MAX_SERVICE_COUNT_INDEX] += 1;
			String info = String.format("Mw Time of %s ms exceeded max Service Time bound of: %s ms", mwTime100us / 1000000, MyMiddleware.HISTOGRAM_MAX_SECONDS * 10000);
			INFO_LOGGER.warn(info);
			ERROR_LOGGER.warn(info);
			ERROR_LOGGER.catching(e);
		}
		avgQueueLength = updateAvg(avgQueueLength, task.getQueueLength(), nofRequests);
		avgQueueWaitingTime = updateAvg(avgQueueWaitingTime, task.stopTimeQueue - task.startTimeQueue, nofRequests);

		nofEmptyResponses += task.getNofKeys() - task.getNofResponses();
		
		switch(task.getOperation()) {
		case GET:
			nofGET += 1;
			avgServiceTimeGet = updateAvg(avgServiceTimeGet, serviceTime, nofGET);
			avgReadingTimeGet = updateAvg(avgReadingTimeGet, task.socketReadingTime, nofGET);
			avgNofReadCallsGet = updateAvg(avgNofReadCallsGet, task.nofReadCalls, nofGET);
			break;
		case MULTIGET:
			nofMULTIGET += 1;
			avgMultigetSize = updateAvg(avgMultigetSize, task.getNofKeys(), nofMULTIGET);
			avgServiceTimeMultiget = updateAvg(avgServiceTimeMultiget, serviceTime, nofMULTIGET);
			avgReadingTimeMulGet = updateAvg(avgReadingTimeMulGet, task.socketReadingTime, nofMULTIGET);
			avgNofReadCallsMulGet = updateAvg(avgNofReadCallsMulGet, task.nofReadCalls, nofMULTIGET);
			break;
		case SET:
			nofSET += 1;
			avgServiceTimeSet = updateAvg(avgServiceTimeSet, serviceTime, nofSET);
			avgReadingTimeSet = updateAvg(avgReadingTimeSet, task.socketReadingTime, nofSET);
			avgNofReadCallsSet = updateAvg(avgNofReadCallsSet, task.nofReadCalls, nofSET);
			break;
		default:
			ERROR_LOGGER.error("Caught task with undefined operation.");
			break;
		}
	}
	
	private double updateAvg(double oldAvg, long newDatapoint, long updatedDenominator) {
		return oldAvg + (newDatapoint - oldAvg) / updatedDenominator;
	}
	
	public void finalize() {
		stopTimestamp = System.nanoTime();
		double timeDelta = stopTimestamp - startTimestamp;
		timeDeltaSec = timeDelta / 1000000000;
		avgThroughput = nofRequests / timeDeltaSec;
	}
}
