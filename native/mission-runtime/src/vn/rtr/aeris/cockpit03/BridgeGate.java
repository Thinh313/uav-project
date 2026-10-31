package vn.rtr.aeris.cockpit03;
import java.io.IOException;
import java.util.*;
/** Per-Activity monotonically ordered UI requests. Contains no flight action dispatch. */
public final class BridgeGate {
 public final int epoch;private long last;private boolean closed;
 public BridgeGate(int epoch){if(epoch<1)throw new IllegalArgumentException("EPOCH");this.epoch=epoch;}
 public synchronized void accept(String id,int suppliedEpoch,String type,int bytes)throws IOException{if(closed||bytes<1||bytes>16384||suppliedEpoch!=epoch||id==null||!id.matches("ui-"+epoch+"-[1-9][0-9]{0,9}"))throw new IOException("BRIDGE_CONTEXT_OR_BOUND");long seq=Long.parseLong(id.substring(id.lastIndexOf('-')+1));if(seq<=last||seq>2147483647L)throw new IOException("BRIDGE_REPLAY_OR_ORDER");last=seq;if(!Arrays.asList("LOAD","SAVE_DRAFT","NAVIGATE","STATE","REVIEWS").contains(type))throw new IOException("BRIDGE_NONFLIGHT_METHOD_ONLY");}
 public synchronized void close(){closed=true;}
}
