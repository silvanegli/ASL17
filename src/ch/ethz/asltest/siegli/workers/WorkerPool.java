package ch.ethz.asltest.siegli.workers;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.BlockingQueue;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import ch.ethz.asltest.siegli.MyMiddleware;
import ch.ethz.asltest.siegli.protocol.MemcachedTask;

/***
 * Collection of all the Worker threads providing an interface for handling collective operations such as shutdown.
 * @author siegli
 *
 */
public class WorkerPool {
	
	private static final Logger INFO_LOGGER = LogManager.getLogger(MyMiddleware.INFO_LOGGER_NAME);
	
	private ArrayList<Worker> pool;
	
	
	public void initialize(List<String> mcAddresses, BlockingQueue<MemcachedTask> taskQueue, int nofWorkers, boolean readSharded) throws IOException {
		this.pool =  new ArrayList<Worker>(nofWorkers);
		for(int i=0; i < nofWorkers; i++) {
			Worker worker = new Worker(mcAddresses, taskQueue, readSharded);
			this.pool.add(worker);
		}
	}
	
	public void updateStatisticsWindow() {
		for(Worker worker : pool) {
			worker.setNewStatisticsWindow();
		}
	}
	
	
	public void shutdown() {
		for(Worker worker : pool) {
			worker.cancel();
		}
	}
	
	public void startWorkers() {
		INFO_LOGGER.debug("WorkerPool starting.");
		for(Worker worker : pool) {
			INFO_LOGGER.debug("Starting Worker: " + worker.getName());
			worker.start();
		}
	}
	
	public ArrayList<Worker> getPool() {
		return pool;
	}
}
