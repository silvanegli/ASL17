package ch.ethz.asltest.siegli;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.nio.channels.SelectionKey;
import java.nio.channels.Selector;
import java.nio.channels.ServerSocketChannel;
import java.nio.channels.SocketChannel;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Set;
import java.util.Timer;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import ch.ethz.asltest.siegli.protocol.MemcachedTask;
import ch.ethz.asltest.siegli.protocol.MemcachedTask.Operation;
import ch.ethz.asltest.siegli.workers.Finalizer;
import ch.ethz.asltest.siegli.workers.StatisticUpdaterTask;
import ch.ethz.asltest.siegli.workers.WorkerPool;
import ch.ethz.asltest.siegli.protocol.RequestParser;

/**
 * This class is the main entry point of the application. It maintains a ServerSocketChannel which listens for incoming 
 * connections of memtier clients. After having registered a client connection it listens for incoming packets and tries 
 * to parse them. Therefore it maintains a HashMap which links the client connections to a RequestParser. This allows to
 * reuse the same buffers for the same clients. After having received a successfully parsed MemcachedTask from the Request
 * parser we enqueue into the middleware queue. This class also adds the shutdown hook which summarizes the statistics 
 * gathered during the experiment after a shutdown event has occurred.
 * 
 * @author siegli
 *
 */

public class MyMiddleware {

	public static double sumThinkingTime = 0;
	public static double sumConnections = 0;
	
	public static final long STATISTIC_AGGREGATION_WINDOW = 1000;
	public static final int HISTOGRAM_MAX_SECONDS = 5;
	public static final String TIMING_LOGGER_NAME = "TimingLogger";
	public static final String INFO_LOGGER_NAME = "InfoLogger";
	public static final String ERROR_LOGGER_NAME = "ErrorLogger";

	private HashMap<SocketChannel, RequestParser> requestParserMap;

	private WorkerPool workerPool;
	private Selector clientSelector;
	private ServerSocketChannel middlewareServerChannel;
	private Timer statisticTimer;
	private Finalizer finalizer;

	protected BlockingQueue<MemcachedTask> taskQueue;
	private int nofServers;
	private int currentServerId = 0;

	private static final Logger INFO_LOGGER = LogManager.getLogger(INFO_LOGGER_NAME);
	private static final Logger ERROR_LOGGER = LogManager.getLogger(ERROR_LOGGER_NAME);

	public MyMiddleware(String myIp, int myPort, List<String> mcAddresses, int numThreadsPTP, boolean readSharded)
			throws NumberFormatException, IOException {
		this.taskQueue = new LinkedBlockingQueue<MemcachedTask>();
		this.requestParserMap = new HashMap<>();
		this.clientSelector = Selector.open();
		this.middlewareServerChannel = createAndRegisterServerSocket(myIp, myPort);
		this.statisticTimer = new Timer(true);
		this.workerPool = new WorkerPool();
		this.workerPool.initialize(mcAddresses, taskQueue, numThreadsPTP, readSharded);

		this.nofServers = mcAddresses.size();
		this.finalizer = new Finalizer(this.workerPool, this.statisticTimer);
		Runtime.getRuntime().addShutdownHook(this.finalizer);
		this.finalizer.logSettings(myIp, myPort, mcAddresses, numThreadsPTP, readSharded,
				STATISTIC_AGGREGATION_WINDOW / 1000);
	}

	public void run() {
		this.workerPool.startWorkers();
		StatisticUpdaterTask statTask = new StatisticUpdaterTask(workerPool);
		statisticTimer.schedule(statTask, STATISTIC_AGGREGATION_WINDOW, STATISTIC_AGGREGATION_WINDOW);

		INFO_LOGGER.info("Middleware ready for receiving requests...");
		while (true) {
			try {
				this.clientSelector.select();
				Set<SelectionKey> selKeySet = this.clientSelector.selectedKeys();
				Iterator<SelectionKey> selKeyIterator = selKeySet.iterator();

				while (selKeyIterator.hasNext()) {
					SelectionKey channelKey = selKeyIterator.next();

					if (channelKey.isAcceptable()) {
						registerClientChannel();

					} else if (channelKey.isReadable()) {
						handleRequest(channelKey);
					}
					selKeyIterator.remove();
				}
			} catch (Exception e) {
				ERROR_LOGGER.catching(e);
				INFO_LOGGER.error("Error occured see log file for more info.");
			}
		}
	}

	private void handleRequest(SelectionKey channelKey) throws IOException {
		SocketChannel clientChannel = (SocketChannel) channelKey.channel();

		RequestParser reqParser = this.requestParserMap.get(clientChannel);

		MemcachedTask task;
		SocketAddress clientAddr = clientChannel.getRemoteAddress();

		task = reqParser.parseMessage(clientChannel);

		// if task is null then command line was not complete yet, the client
		// closed the connection or an error occurred
		if (task != null) {
			setAndUpdateServerId(task);
			task.setQueueLength(this.taskQueue.size());
			reqParser.updateThinkingTime(System.nanoTime());
			task.setCurrentRequestParser(reqParser);
			task.startTimeQueue = System.nanoTime();
			this.taskQueue.add(task);
		} else if (!clientChannel.isOpen()) {
			RequestParser parser = requestParserMap.get(clientChannel);
			requestParserMap.remove(clientChannel);
			INFO_LOGGER.debug("Removed client from map " + clientAddr);
			INFO_LOGGER.debug("Nof requests: " + parser.nofReq);
			INFO_LOGGER.debug("Avg think time: " + parser.avgThinkingTime / 1000000);
			sumConnections += 1;
			sumThinkingTime += parser.avgThinkingTime / 1000000;
		}
	}

	private void setAndUpdateServerId(MemcachedTask task) {
		task.setProcessingServerId(this.currentServerId);
		int nextServerId = currentServerId + 1;
		currentServerId = nextServerId % nofServers;
	}

	private void registerClientChannel() throws IOException {
		SocketChannel clientChannel = this.middlewareServerChannel.accept();
		clientChannel.configureBlocking(false);
		clientChannel.register(this.clientSelector, SelectionKey.OP_READ);
		this.requestParserMap.put(clientChannel, new RequestParser());
		INFO_LOGGER.debug("Connection Accepted: " + clientChannel.getRemoteAddress());
		INFO_LOGGER.debug("Hash Map size: " + requestParserMap.size());
	}

	private ServerSocketChannel createAndRegisterServerSocket(String middlewareIP, int middlewarePort)
			throws IOException {
		ServerSocketChannel middlewareServerSocket = ServerSocketChannel.open();
		InetSocketAddress middlewareServerAddress = new InetSocketAddress(middlewareIP, middlewarePort);

		middlewareServerSocket.bind(middlewareServerAddress);
		middlewareServerSocket.configureBlocking(false);

		int ops = middlewareServerSocket.validOps();
		middlewareServerSocket.register(this.clientSelector, ops);
		return middlewareServerSocket;
	}

}
