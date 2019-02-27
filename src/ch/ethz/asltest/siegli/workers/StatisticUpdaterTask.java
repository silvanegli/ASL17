package ch.ethz.asltest.siegli.workers;

import java.util.TimerTask;

/***
 * This Task is scheduled periodically and makes sure that every MyMiddleware.STATISTIC_AGGREGATION_WINDOW seconds the
 * current Statistics objects in all Workers are updated simultaneously.
 * @author siegli
 *
 */

public class StatisticUpdaterTask extends TimerTask {

	private WorkerPool workerPool;

	public StatisticUpdaterTask(WorkerPool workerPool) {
		this.workerPool = workerPool;
	}

	@Override
	public void run() {
		workerPool.updateStatisticsWindow();;
	}

}