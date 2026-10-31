package vn.rtr.aeris.betaworkbench05;
/** Volatile data-operation owner. No authority, queue, retry or persisted ownership. */
public final class OperationGate {
 private String owner;
 public synchronized boolean busy(){return owner!=null;}
 public synchronized void begin(String key){if(key==null||key.length()<4||key.length()>300)throw new IllegalArgumentException("OPERATION_ID");if(owner!=null)throw new IllegalStateException("NATIVE_BUSY_NO_QUEUE");owner=key;}
 public synchronized boolean finish(String key){if(owner==null||!owner.equals(key))return false;owner=null;return true;}
}
