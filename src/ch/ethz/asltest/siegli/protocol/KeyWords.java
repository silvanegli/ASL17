package ch.ethz.asltest.siegli.protocol;

/**
 * Key words as defined by the memcached protocol which we use for parsing the requests and responses.
 * @author siegli
 *
 */

public final class KeyWords {
	
	public final static String GET = "get";
	public final static String SET = "set";
	public static final String VALUE = "VALUE";	
	public static final String END = "END";
	public static final String STORED = "STORED";
	public static final String ERROR = "ERROR";
	public static final String CLIENT_ERROR = "CLIENT_ERROR";
	public static final String SERVER_ERROR = "SERVER_ERROR";
	
	public static final String SPACE_ASCII = "32";
	public static final String RETURN_ASCII = "13";
	public static final String NEWLINE_ASCII = "10";
	
	public static final int SPACE_ASCII_INT = 32;
	public static final int RETURN_ASCII_INT = 13;
	public static final int NEWLINE_ASCII_INT = 10;
	
}
