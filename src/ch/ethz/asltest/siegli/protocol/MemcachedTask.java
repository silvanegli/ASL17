package ch.ethz.asltest.siegli.protocol;

import java.nio.ByteBuffer;
import java.nio.channels.SocketChannel;
import java.util.Arrays;

/**
 * This class represents a memcached request. It contains all the necessary timestamps and other measurements which will be set at the corresponding stages in the middleware.
 * Moreover does it keep track of the clientChannel on which the request modeled by this object was received on. This will allow the Worker to send
 * the response back to the correct client.
 * @author siegli
 *
 */

public class MemcachedTask {
	
	public enum Operation {
		GET, MULTIGET, SET
	}
	
	public long startTimeMiddleWare;
	public long stopTimeMiddleWare;
	
	public long startTimeQueue;
	public long stopTimeQueue;
	
	public long startTimeServer;
	public long stopTimeServer;
		
	private SocketChannel clientChannel;
	private ByteBuffer messageBuffer;
	private int nofKeys;
	private int nofResponses;
	private Operation operation;
	
	private int processingServerId;
	private int queueLength;
	
	public long socketReadingTime = 0;
	public int nofReadCalls = 0;
	
	public RequestParser currentRequestParser;
	
	public void setCurrentRequestParser(RequestParser pars) {
		currentRequestParser = pars;
	}
	
	public MemcachedTask(SocketChannel clientChannel, ByteBuffer messageBuffer) {
		this.startTimeMiddleWare = System.nanoTime();
		this.clientChannel = clientChannel;		
		this.messageBuffer = messageBuffer;	
		setNofResponses(0);
		setNofKeys(0);
	}

	public String getCommandLine() {
		byte[] bufArray = messageBuffer.array();
		int currentPos = 0;
		int currentByteInt;
		do {
			currentByteInt = Byte.toUnsignedInt(bufArray[currentPos]);
			currentPos++;
		} while(currentByteInt != KeyWords.RETURN_ASCII_INT);
		byte[] cmdBytes = Arrays.copyOfRange(bufArray, 0, currentByteInt);
		String commandLine = new String(cmdBytes);
		return commandLine;
	}
	
	public int getProcessingServerId() {
		return processingServerId;
	}

	public void setProcessingServerId(int processingServerId) {
		this.processingServerId = processingServerId;
	}
	
	public SocketChannel getClientChannel() {
		return clientChannel;
	}

	public void setClientChannel(SocketChannel clientChannel) {
		this.clientChannel = clientChannel;
	}

	public ByteBuffer getMessageBuffer() {
		return messageBuffer;
	}

	public void setNofKeys(int nofKeys) {
		this.nofKeys = nofKeys;
	}

	public void setOperation(Operation op) {
		this.operation = op;		
	}
	
	public Operation getOperation() {
		return this.operation;		
	}

	public int getNofKeys() {
		return nofKeys;
	}

	public int getQueueLength() {
		return queueLength;
	}

	public void setQueueLength(int queueLength) {
		this.queueLength = queueLength;
	}

	public int getNofResponses() {
		return nofResponses;
	}

	public void setNofResponses(int nofEmptyResponses) {
		this.nofResponses = nofEmptyResponses;
	}

	public void increaseNofResponses(int additionalNofResponses) {
		this.nofResponses += additionalNofResponses;
	}
}
