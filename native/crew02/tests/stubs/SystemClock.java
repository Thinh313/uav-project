package android.os;
public final class SystemClock{private static long n=1000;public static synchronized long elapsedRealtime(){return ++n;}public static synchronized void advance(long ms){n+=ms;}}
