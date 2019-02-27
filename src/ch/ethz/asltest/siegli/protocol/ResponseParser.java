package ch.ethz.asltest.siegli.protocol;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.SocketChannel;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;


/***
 * This class is responsible for parsing a (possibly split) response received from one or multiple memcached servers represented by a SocketChannel.
 * There is exactly one object dedicated per worker thread at runtime. This allows to reuse the Buffers allocated at object creation time.
 * @author siegli
 *
 */
public class ResponseParser extends Parser {
	public static final int SINGLE_GET_RESPONSE_BUFFER_SIZE = 1500;
	public static final int MULTI_GET_RESPONSE_BUFFER_SIZE = 15000;	//enough for a MULTIGET response with 9 keys
	public static final int SET_RESPONSE_BUFFER_SIZE = 512;

	private ByteBuffer setBuffer = ByteBuffer.allocate(SET_RESPONSE_BUFFER_SIZE);
	private ByteBuffer singleGetBuffer = ByteBuffer.allocate(SINGLE_GET_RESPONSE_BUFFER_SIZE);
	private ByteBuffer multiGetBuffer = ByteBuffer.allocate(MULTI_GET_RESPONSE_BUFFER_SIZE);

	/***
	 * As SET requests are replicated to all memcached servers we wait for the answer (STORED) on all provided serverChannels.
	 * If an error occured in more than one case we return the last one.
	 * @param task represents corresponding request for the response we received
	 * @param serverChannels
	 * @throws IOException
	 */
	public void parseSetResponse(MemcachedTask task, ArrayList<SocketChannel> serverChannels) throws IOException {
		boolean responseIsError = false;
		int errorPosition = 0;
		String response;

		for (SocketChannel serverChannel : serverChannels) {
			// we still proceed in order to wait for all servers to respond
			setBuffer.clear();
			long startReading = System.nanoTime();
			serverChannel.read(setBuffer);
			long stopReading = System.nanoTime();
			task.socketReadingTime += stopReading - startReading;
			task.nofReadCalls += 1;
			

			response = new String(setBuffer.array());
			if (!response.startsWith(KeyWords.STORED)) {
				responseIsError = true;
				errorPosition = handleError(setBuffer, 0, task, serverChannel);
			}

		}		
		if (responseIsError) {
			setBuffer.position(errorPosition);
		}
	}

	public void parseNonShardedMultiGetResponse(MemcachedTask task, SocketChannel serverChannel) throws IOException {
		parseNonShardedGetResponse(multiGetBuffer, task, serverChannel);
	}

	public void parseSingleGetResponse(MemcachedTask task, SocketChannel serverChannel) throws IOException {
		parseNonShardedGetResponse(singleGetBuffer, task, serverChannel);
	}

	private void parseNonShardedGetResponse(ByteBuffer getBuffer, MemcachedTask task, SocketChannel serverChannel)
			throws IOException {
		getBuffer.clear();
		boolean isError = readCheckAndCountGetResponses(getBuffer, serverChannel, task);
		if (isError) {
			handleError(getBuffer, 0, task, serverChannel);
		}
	}

	/***
	 * Handles a response of a sharded MULTIGET which means it reads sequentially from the list of servers and
	 * reassembles the received partial results into a final one which will be sent back to the client.
	 * Basically calls parseNonShardedGetResponse for every server. 
	 * @param task
	 * @param receivers list of servers
	 * @throws IOException
	 */
	public void parseShardedMultiGetResponse(MemcachedTask task, List<SocketChannel> receivers)
			throws IOException {
		multiGetBuffer.clear();
		boolean responseIsError = false;
		int errorPosition = 0;
		boolean partialResponseIsError = false;

		for (SocketChannel serverChannel : receivers) {
			int oldPosition = multiGetBuffer.position();
			partialResponseIsError = readCheckAndCountGetResponses(multiGetBuffer, serverChannel, task);

			if (!partialResponseIsError) {
				int currentPos = multiGetBuffer.position();
				multiGetBuffer.position(currentPos - 5); // the buffer ends with END\r\n which we only want at the
				// very end of the response
			} else {
				responseIsError = true;
				errorPosition = handleError(multiGetBuffer, oldPosition, task, serverChannel);
			}
		}
		if (!responseIsError) {
			multiGetBuffer.position(multiGetBuffer.position() + 5); // we want the END\r\n at the end
		} else {
			multiGetBuffer.position(errorPosition);
		}
	}

	/***
	 * Implements the core functionality used for parsing a response.  First it checks whether the response contains
	 * a complete response header. If so it looks for either VALUE, END or an ERROR keyword. In the first case we received
	 * one or more values corresponding to one or more keys. Therefore we parse response line by response line until we 
	 * reach END. While doing so we keep track of the number of received keys in order to report any empty messages.
	 * @param getBuffer
	 * @param serverChannel
	 * @param task
	 * @return
	 * @throws IOException
	 */
	private boolean readCheckAndCountGetResponses(ByteBuffer getBuffer, SocketChannel serverChannel, MemcachedTask task)
			throws IOException {
		boolean error = false;
		boolean responseIsComplete = false;

		byte[] bufArray = getBuffer.array();
		int nextResponseLineStart = getBuffer.position(); // position of the response line (VALUE 0 0 5\r\n)
		int nofPackets = 0; // corresponding to the next value
		// (i.e. end of current response line + dataLength + 4 )

		while (!responseIsComplete) {
			long startReading = System.nanoTime();
			serverChannel.read(getBuffer);
			long stopReading = System.nanoTime();
			task.socketReadingTime += stopReading - startReading;
			
			task.nofReadCalls += 1;
			nofPackets++;
			int minimalBufferPosition = getBuffer.position() - 5; // position the buffer needs to be so that we can
																	// parse response
			if (nextResponseLineStart > minimalBufferPosition) {
				continue;
			}
			boolean endReached = false;

			while (!endReached) {
				String firstWord = getFirsNBytes(bufArray, nextResponseLineStart, 5);
				if (firstWord.startsWith(KeyWords.VALUE)) {
					task.increaseNofResponses(1);
					int oldResponseLineStart = nextResponseLineStart;
					nextResponseLineStart = getNextResponseLineIndex(bufArray, nextResponseLineStart, getBuffer.position());
		
					if (nextResponseLineStart > minimalBufferPosition) {
						endReached = true; // response is split over multiple packets -> we need to read more data
						INFO_LOGGER.debug("Answer is split over more than one packet. -> we need to read more data");
					}
					if (nextResponseLineStart == -1) {
						endReached = true; // response is split over multiple packets -> we need to read more data
						nextResponseLineStart = oldResponseLineStart;
						task.increaseNofResponses(-1); //we can only count the response if it is complete
						INFO_LOGGER.debug("Response was split in Response Line. -> we need to read more data");
					}

				} else if (firstWord.startsWith(KeyWords.END)) {
					endReached = true;
					responseIsComplete = true;
					INFO_LOGGER.debug("Answer was split over: " + nofPackets + " packets.");

				} else if (checkForError(bufArray, nextResponseLineStart)) {
					endReached = true;
					responseIsComplete = true;
					error = true;
					task.setNofResponses(task.getNofKeys());

				} else {
					endReached = true;
					responseIsComplete = true;
					error = true;
					ERROR_LOGGER.error("Parsed undefined Response Key Word - should not happen.");
				}
			}

		}
		return error;
	}

	private boolean checkForError(byte[] buf, int offset) {
		String possibleErrorString = getFirsNBytes(buf, offset, 20);
		boolean clientError = possibleErrorString.startsWith(KeyWords.CLIENT_ERROR);
		boolean error = possibleErrorString.startsWith(KeyWords.ERROR);
		boolean serverError = possibleErrorString.startsWith(KeyWords.SERVER_ERROR);
		return clientError || error || serverError;
	}

	private int handleError(ByteBuffer buf, int errorStart, MemcachedTask task, SocketChannel channel)
			throws IOException {
		int errorPosition = buf.position();
		byte[] errorBytes = Arrays.copyOfRange(buf.array(), errorStart, errorPosition);
		buf.clear();
		buf.put(errorBytes);
		logError(new String(errorBytes), task, channel);
		int errorLength = errorPosition - errorStart;
		return errorLength;
	}

	private void logError(String error, MemcachedTask task, SocketChannel serverChannel) throws IOException {
		String cmd = task.getCommandLine().replace("\r", "").replace("\n", "");
		String err = String.format("Task '%s' received Error response from: %s\r\n%s", cmd,
				serverChannel.getRemoteAddress(), error);
		String msgBuf = new String(task.getMessageBuffer().array());
		String taskInfo = String.format("Op:  %s\nNofKeys: %s\nMsgBuf: %s", task.getOperation(), task.getNofKeys(), msgBuf);
		INFO_LOGGER.error(err);
		INFO_LOGGER.error(taskInfo);
		ERROR_LOGGER.error(err);
	}

	public ByteBuffer getSetBuffer() {
		return this.setBuffer;
	}

	public ByteBuffer getSingleGetBuffer() {
		return this.singleGetBuffer;
	}

	public ByteBuffer getMultiGetBuffer() {
		return this.multiGetBuffer;
	}
}
