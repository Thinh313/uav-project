package vn.rtr.aeris.operator01;
import java.util.function.BooleanSupplier;
/** Shared production send boundary used for both domains; never retries partial/unknown writes. */
public final class NativeSend98{
 public interface Durable{void append(String kind,byte[]bytes)throws Exception;}public interface Output{void write(byte[]bytes)throws Exception;}public interface Approval{void approve()throws Exception;}
 public static void send(Durable wal,Output out,BooleanSupplier foreground,Approval policy,byte[]wire)throws Exception{wal.append("TX_INTENT",wire);if(!foreground.getAsBoolean())throw new java.io.IOException("NATIVE_FOREGROUND_BEFORE_APPROVAL");policy.approve();if(!foreground.getAsBoolean())throw new java.io.IOException("NATIVE_FOREGROUND_BEFORE_SOCKET");out.write(wire);wal.append("TX_WRITTEN",wire);}
}
