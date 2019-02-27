package ch.ethz.asltest.siegli.workers;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.nio.ByteBuffer;
import java.nio.channels.SocketChannel;
import java.util.ArrayList;
import java.util.LinkedList;
import java.util.List;
import java.util.concurrent.BlockingQueue;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import ch.ethz.asltest.siegli.MyMiddleware;
import ch.ethz.asltest.siegli.protocol.KeyWords;
import ch.ethz.asltest.siegli.protocol.MemcachedTask;
import ch.ethz.asltest.siegli.protocol.MemcachedTask.Operation;
import ch.ethz.asltest.siegli.protocol.RequestParser;
import ch.ethz.asltest.siegli.protocol.ResponseParser;

/***
 * This class represents a middleware worker. It runs in an infinite loop of reading (blocking) from the middleware and processing the different requests accordingly.
 * This includes sending it to one or possibly multiple servers (depending on request type and middleware mode), waiting for the answer and correctly parse and
 * possibly reassembling the responses.
 * @author siegli
 *
 */

public class Worker extends Thread {
	protected BlockingQueue<MemcachedTask> taskQueue;

	private ArrayList<SocketChannel> serverChannels;
	private final int nofServers;
	private boolean cancelled = false;
	private boolean readSharded;

	private ResponseParser respParser;
	private ByteBuffer multishardedCopyBuffer = ByteBuffer.allocate(RequestParser.REQUEST_BUFFER_SIZE);

	Statistics currentStatistics = new Statistics();
	private LinkedList<Statistics> statisticsList;
	public int[] serviceTimeCounts;

	protected static final Logger TIMING_LOGGER = LogManager.getLogger(MyMiddleware.TIMING_LOGGER_NAME);
	protected static final Logger INFO_LOGGER = LogManager.getLogger(MyMiddleware.INFO_LOGGER_NAME);
	protected static final Logger ERROR_LOGGER = LogManager.getLogger(MyMiddleware.ERROR_LOGGER_NAME);

	public Worker(List<String> mcAddresses, BlockingQueue<MemcachedTask> taskQueue, boolean readSharded)
			throws IOException {
		this.taskQueue = taskQueue;
		this.readSharded = readSharded;
		this.respParser = new ResponseParser();
		initializeServerConnections(mcAddresses);
		this.nofServers = serverChannels.size();
		this.statisticsList = new LinkedList<>();
		int nofServiceTimeSlotsA100us = 10000 * MyMiddleware.HISTOGRAM_MAX_SECONDS;
		this.serviceTimeCounts = new int[nofServiceTimeSlotsA100us];
	}

	private void initializeServerConnections(List<String> mcAddresses) throws IOException {
		this.serverChannels = new ArrayList<SocketChannel>(mcAddresses.size());
		for (String serverAddress : mcAddresses) {
			String[] addressAndPort = serverAddress.split(":");
			String memcachedServerURL = addressAndPort[0];
			int memcachedServerPort = Integer.parseInt(addressAndPort[1]);

			SocketChannel socketChannel = SocketChannel.open();
			socketChannel.connect(new InetSocketAddress(memcachedServerURL, memcachedServerPort));
			socketChannel.configureBlocking(true);
			serverChannels.add(socketChannel);
			INFO_LOGGER.debug("Connection from worker:" + this.getName() + " to server on " + serverAddress);
		}
	}

	@Override
	public void run() {

		while (!cancelled) {
			MemcachedTask task;
			try {
				task = this.taskQueue.take(); // blocking
				task.stopTimeQueue = System.nanoTime();

				Operation taskOperation = task.getOperation();

				switch (taskOperation) {
				case GET:
					processSingleGET(task);
					break;
				case MULTIGET:
					if (this.readSharded) {
						processShardedMULTIGET(task);
					} else {
						processNonShardedMULTIGET(task);
					}
					break;
				case SET:
					processSET(task);
					break;
				default:
					ERROR_LOGGER.error("Worker dequed Task with undefined operation.");
					break;
				}

				task.currentRequestParser.lastResponse = task.stopTimeMiddleWare;
				currentStatistics.updateStatistics(task, serviceTimeCounts);

			} catch (InterruptedException e) {
				cancelled = true;
				e.printStackTrace();
			}
		}
		currentStatistics.finalize();
		closeConnections();
	}

	/***
	 * Determine the number of keys that each server should get then split the message into multiple smaller 
	 * MULTIGETS and send them to all available servers. Afterwards wait for the answer and reassemble it
	 * before forwarding it to the client.
	 * @param task
	 */
	private void processShardedMULTIGET(MemcachedTask task) {
		int fairShare = task.getNofKeys() / this.nofServers;
		int remaining = task.getNofKeys() - this.nofServers * fairShare;
		List<SocketChannel> receivers = serverChannels;
		int start = 4;
		try {
			if (fairShare == 0) {
				receivers = receivers.subList(0, remaining);
			}
			byte[] commandLineBytes = task.getMessageBuffer().array();
			for (SocketChannel serverChannel : receivers) {
				int remainingAdd = remaining > 0 ? 1 : 0;
				int nofKeys = fairShare + remainingAdd;
				int newStart = sendShardedGetToServer(commandLineBytes, start, nofKeys, serverChannel);
				start = newStart;
				remaining -= 1;
			}
			task.startTimeServer = System.nanoTime();
			respParser.parseShardedMultiGetResponse(task, receivers);
			task.stopTimeServer = System.nanoTime();

			sendResponseToClient(task, respParser.getMultiGetBuffer());
			task.stopTimeMiddleWare = System.nanoTime();
		} catch (IOException e) {
			ERROR_LOGGER.error("Error while processing task: " + task.getCommandLine());
			ERROR_LOGGER.catching(e);
		}
	}

	/***
	 * send the message to the server determined by the network thread in a round robin manner
	 * @param task
	 */
	private void processNonShardedMULTIGET(MemcachedTask task) {
		int serverId = task.getProcessingServerId();
		SocketChannel serverChannel = serverChannels.get(serverId);

		try {
			sendMessageToServer(task, serverChannel);
			task.startTimeServer = System.nanoTime();
			respParser.parseNonShardedMultiGetResponse(task, serverChannel);
			task.stopTimeServer = System.nanoTime();

			sendResponseToClient(task, respParser.getMultiGetBuffer());
			task.stopTimeMiddleWare = System.nanoTime();

		} catch (IOException e) {
			ERROR_LOGGER.error("Error while processing task: " + task.getCommandLine());
			ERROR_LOGGER.catching(e);
		}
	}

	/***
	 * Also similar to processNonShardedMULTIGET except for the buffer
	 * @param task
	 */
	private void processSingleGET(MemcachedTask task) {
		int serverId = task.getProcessingServerId();
		SocketChannel serverChannel = serverChannels.get(serverId);

		try {
			sendMessageToServer(task, serverChannel);
			task.startTimeServer = System.nanoTime();
			respParser.parseSingleGetResponse(task, serverChannel);
			task.stopTimeServer = System.nanoTime();

			sendResponseToClient(task, respParser.getSingleGetBuffer());
			task.stopTimeMiddleWare = System.nanoTime();

		} catch (IOException e) {
			ERROR_LOGGER.error("Error while processing task: " + task.getCommandLine());
			ERROR_LOGGER.catching(e);
		}
	}

	/***
	 * send the request to all the servers and afterwards parse all responses
	 * @param task
	 */
	private void processSET(MemcachedTask task) {
		try {
			for (SocketChannel serverChannel : serverChannels) {
				sendMessageToServer(task, serverChannel);
			}
			task.startTimeServer = System.nanoTime();
			respParser.parseSetResponse(task, serverChannels);
			task.stopTimeServer = System.nanoTime();

			sendResponseToClient(task, respParser.getSetBuffer());
			task.stopTimeMiddleWare = System.nanoTime();

		} catch (IOException e) {
			ERROR_LOGGER.error("Error while processing task: " + task.getCommandLine());
			ERROR_LOGGER.catching(e);
		}

	}

	/***
	 * helper function for processShardedMultiget. Implements the functionality of splitting the packet and sending it
	 * to the different servers.
	 * @param initialCommand
	 * @param start
	 * @param nofKeys
	 * @param serverChannel
	 * @return
	 * @throws IOException
	 */
	private int sendShardedGetToServer(byte[] initialCommand, int start, int nofKeys, SocketChannel serverChannel)
			throws IOException {
		multishardedCopyBuffer.clear();
		multishardedCopyBuffer.put(KeyWords.GET.getBytes());
		multishardedCopyBuffer.put(Byte.decode(KeyWords.SPACE_ASCII));

		int currentReferenceByteIndex = start;
		byte currentByte;
		int byteInt;
		for (int keyIndex = 0; keyIndex < nofKeys; keyIndex++) {
			do {
				currentByte = initialCommand[currentReferenceByteIndex];
				multishardedCopyBuffer.put(currentByte);
				currentReferenceByteIndex++;
				byteInt = Byte.toUnsignedInt(currentByte);
			} while (byteInt != KeyWords.SPACE_ASCII_INT && byteInt != KeyWords.RETURN_ASCII_INT);
		}
		int newPos = multishardedCopyBuffer.position() - 1;
		multishardedCopyBuffer.position(newPos);
		multishardedCopyBuffer.put(Byte.decode(KeyWords.RETURN_ASCII));
		multishardedCopyBuffer.put(Byte.decode(KeyWords.NEWLINE_ASCII));

		sendMessageToServer(multishardedCopyBuffer, serverChannel);

		return currentReferenceByteIndex;
	}

	private void sendMessageToServer(MemcachedTask task, SocketChannel serverChannel) throws IOException {
		ByteBuffer clientBuf = task.getMessageBuffer();
		sendMessageToServer(clientBuf, serverChannel);
	}

	private void sendMessageToServer(ByteBuffer buf, SocketChannel serverChannel) throws IOException {
		buf.flip();
		while (buf.hasRemaining()) {
			serverChannel.write(buf);
		}
	}

	private void sendResponseToClient(MemcachedTask task, ByteBuffer responseBuffer) throws IOException {
		SocketChannel clientChannel = task.getClientChannel();

		responseBuffer.flip();
		while (responseBuffer.hasRemaining()) {
			clientChannel.write(responseBuffer);
		}
	}

	public void cancel() {
		this.cancelled = true;
	}

	private void closeConnections() {
		for (SocketChannel serverChannel : serverChannels) {
			try {
				SocketAddress serverAddress = serverChannel.getRemoteAddress();
				serverChannel.close();
				INFO_LOGGER.debug("Closed Connection to server: " + serverAddress);
			} catch (IOException e) {
				INFO_LOGGER.error("Exception while closing connection to server.");
				ERROR_LOGGER.catching(e);
			}
		}
	}

	public void setNewStatisticsWindow() {
		currentStatistics.finalize();
		statisticsList.add(currentStatistics);
		currentStatistics = new Statistics();
	}

	public LinkedList<Statistics> getStatisticsList() {
		return statisticsList;
	}

}
