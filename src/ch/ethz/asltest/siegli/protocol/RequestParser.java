package ch.ethz.asltest.siegli.protocol;

import java.io.IOException;

import java.nio.ByteBuffer;
import java.nio.channels.SocketChannel;
import java.util.Arrays;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import ch.ethz.asltest.siegli.MyMiddleware;
import ch.ethz.asltest.siegli.protocol.MemcachedTask.Operation;

/***
 * This class parses a request memcached request into a MemcachedTask object. It therefore has a ByteBuffer which is allocated once at 
 * object creation time. The same RequestParser object will always be reused by the same client. This allows for Buffer reuse and also
 * to keep track of the state in case we did not receive a complete message.
 * @author siegli
 *
 */

public class RequestParser extends Parser {
	
	private static final Logger INFO_LOGGER = LogManager.getLogger(MyMiddleware.INFO_LOGGER_NAME);

	public long nofReq = 0;
	public long lastResponse = 0;
	public double avgThinkingTime = 0;
	
	public static final int REQUEST_BUFFER_SIZE = 2048;
	
	private ByteBuffer requestBuf = ByteBuffer.allocate(REQUEST_BUFFER_SIZE);
	private boolean lastMsgWasIncomplete = false;
	
	
	/***
	 * Checks whether we received a complete command line (tailing \r) and if not reads as long as we receive a
	 * a complete line. While checking it keeps track of possible key candidates in the request e.g GET memtier-1 memtier-2....
	 * @param clientChannel
	 * @return
	 * @throws IOException
	 */
	public MemcachedTask parseMessage(SocketChannel clientChannel) throws IOException {
		if(!lastMsgWasIncomplete) {
			requestBuf.clear();
		}
		
		int readBytes;
		try {
			readBytes = clientChannel.read(requestBuf);
		} catch (IOException e) {
			readBytes = -1;
			INFO_LOGGER.debug("Reading from client was interrupted: " + e.getMessage());
			ERROR_LOGGER.catching(e);
		}
					
		if (readBytes == -1) { // client closed connection properly or improperly
			INFO_LOGGER.debug("Client closed connection: " + clientChannel.getRemoteAddress());
			clientChannel.close();
			return null;
		}	
		
		byte[] bufferArray = requestBuf.array();
		int currentPosition = 0;
		int bufferPos = requestBuf.position();
		int nofKeyCandidates = 0;
		boolean commandLineComplete = false;
		lastMsgWasIncomplete = false;

		while(!commandLineComplete && currentPosition < bufferPos) {
			int currentByteInt = Byte.toUnsignedInt(bufferArray[currentPosition]);
			commandLineComplete =  currentByteInt == KeyWords.RETURN_ASCII_INT;
			currentPosition++;
			if(currentByteInt == KeyWords.SPACE_ASCII_INT) {
				nofKeyCandidates ++;
			}
		}
		if(!commandLineComplete) {
			lastMsgWasIncomplete = true;
			return null;
		}

		MemcachedTask parsedTask = parseTask(nofKeyCandidates, clientChannel);
		return parsedTask;
	}
	
	/***
	 * This method is called after a complete command line was received. It determines the type of the request (GET, SET, MULTIGET)
	 * based on the key word and the number of parsed keys. In the case of a GET it additionally checks whether all Bytes (corresponding
	 * to the parsed length of the request) have been read. If not it returns and signals it by setting lastMsgWasIncomplete to true.
	 * @param nofKeyCandidates
	 * @param clientChannel
	 * @return
	 */
	private MemcachedTask parseTask(int nofKeyCandidates, SocketChannel clientChannel) {
		byte[] bufferArray = requestBuf.array();
		MemcachedTask task = null;	
		String operation = getFirsNBytes(bufferArray, 0, 3).toLowerCase();

		switch (operation) {
		case KeyWords.GET:
			task = new MemcachedTask(clientChannel, requestBuf);
			task.setNofKeys(nofKeyCandidates);
			if (nofKeyCandidates > 1) {
				task.setOperation(Operation.MULTIGET);
			} else {
				task.setOperation(Operation.GET);
			}		
			break;

		case KeyWords.SET:
			int lastExpectedIndex = getNextResponseLineIndex(bufferArray, 0, requestBuf.position());
			if( lastExpectedIndex > -1 && lastExpectedIndex <= requestBuf.position()) {
				task = new MemcachedTask(clientChannel, requestBuf);
				task.setOperation(Operation.SET);
			} else {
				INFO_LOGGER.debug("Last Set was incomplete. Last Expected Index= " + lastExpectedIndex + " and buffer position= " + requestBuf.position());
				lastMsgWasIncomplete = true;
			}
			break;

		default:
			byte[] requestBytes = Arrays.copyOfRange(bufferArray, 0, requestBuf.position());
			String request = new String(requestBytes); 
			ERROR_LOGGER.error("Unparseable Request: " + request);
			break;
		}	
		
		return task;
	}
	
	
	public void updateThinkingTime(double newRequest) {
		if(lastResponse != 0) {
			nofReq ++;
			double currentThinkTime = newRequest - lastResponse;
			avgThinkingTime = avgThinkingTime + (currentThinkTime - avgThinkingTime)/nofReq;
		}
	}
}
