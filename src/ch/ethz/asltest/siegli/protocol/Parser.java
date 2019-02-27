package ch.ethz.asltest.siegli.protocol;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import ch.ethz.asltest.siegli.MyMiddleware;

/**
 * Parent class for RequestParser and ResponseParser implementing some basic functionality
 * @author siegli
 *
 */

public class Parser {
	
	protected static final Logger INFO_LOGGER = LogManager.getLogger(MyMiddleware.INFO_LOGGER_NAME);
	protected static final Logger ERROR_LOGGER = LogManager.getLogger(MyMiddleware.ERROR_LOGGER_NAME);
	
	/**
	 * Assumes that a memcached-request-header of the form <type> params length\r\n was read into the buffer.
	 * Traverses the buffer until a return character is detected or we reach the current buffers position and
	 * then parses the length at the end of the line with which we can calculate the position of the next
	 * expected response line. 
	 */
	protected int getNextResponseLineIndex(byte[] buf, int start, int bufferEnd) {
		int lastArgumentStart = start;
		int currentPos = start;
		int currentByteInt;
		do {
			byte currentByte = buf[currentPos];
			currentByteInt = Byte.toUnsignedInt(currentByte);
			if(currentByteInt == KeyWords.SPACE_ASCII_INT) {
				lastArgumentStart = currentPos + 1;
			}
			currentPos += 1;
		} while(currentByteInt != KeyWords.RETURN_ASCII_INT && currentPos < bufferEnd);
		
		if(currentPos == bufferEnd) {
			INFO_LOGGER.debug("Msg was split in the middle of a response line.");
			return -1;
		} else {
			currentPos -= 1;
			int nofLetters = currentPos - lastArgumentStart;
			String lengthString = getFirsNBytes(buf, lastArgumentStart, nofLetters);
			int responseLength = Integer.parseInt(lengthString);
			int nextResponseLineIndex = currentPos + responseLength + 4; //+4 because of the \r\n in the response line and after the data values

			return nextResponseLineIndex;		
		}
	}
	
	protected String getFirsNBytes(byte[] buf,int offset, int nofBytes) {
		byte[] responseBytes = new byte[nofBytes];

		for (int i = 0; i < nofBytes; i++) {
			responseBytes[i] = buf[offset + i];
		}
		String word = new String(responseBytes);
		return word;
	}

}
