package vn.rtr.aeris.beta01runtime;
import java.util.*;

/** Memory-only explicit UI intent fence; never reconstructed from Activity/history state. */
public final class PendingExplicitAction<T> {
    public static final class Ticket<T> {
        public final String id,action;public final T payload;public final long receivedNs;
        private Ticket(String id,String action,T payload,long receivedNs){this.id=id;this.action=action;this.payload=payload;this.receivedNs=receivedNs;}
    }
    private final long ttlNs;private final int recentLimit;
    private final LinkedHashSet<String> recent=new LinkedHashSet<>();
    private Ticket<T> pending;private long lastObserved=-1;private String status="NO_EXPLICIT_ACTION";
    private boolean failed;private long accepted,consumed,cancelled,replaced,expired;
    public PendingExplicitAction(long ttlNs,int recentLimit){if(ttlNs<=0||ttlNs>5000000000L||recentLimit<1||recentLimit>128)throw new IllegalArgumentException("PENDING_POLICY");this.ttlNs=ttlNs;this.recentLimit=recentLimit;}
    private void time(long now){if(failed||now<0||now<lastObserved){pending=null;failed=true;status="FAILED_CLOCK_REGRESSION";throw new IllegalStateException(status);}lastObserved=now;}
    public synchronized void enqueue(String id,String action,T payload,long now){
        time(now);
        if(id==null||!id.matches("[A-Za-z0-9_.:-]{1,128}")||action==null||!Arrays.asList("CONNECT","CLOSE","STATUS","CONSENT","NEUTRAL","GUIDED","ARM","TAKEOFF","LAND","PULSE").contains(action)||payload==null){pending=null;status="REJECTED_EXPLICIT_ACTION_INPUT";throw new IllegalArgumentException("EXPLICIT_ACTION_ID_COMMAND_PAYLOAD_REQUIRED");}
        if(recent.contains(id)){pending=null;status="REJECTED_EXPLICIT_ACTION_REPLAY";throw new IllegalStateException("EXPLICIT_ACTION_REPLAY");}
        if(pending!=null)replaced++;
        pending=new Ticket<>(id,action,payload,now);recent.add(id);while(recent.size()>recentLimit)recent.remove(recent.iterator().next());accepted++;status="PENDING_EXPLICIT_ACTION";
    }
    public synchronized Ticket<T> consume(long now,boolean foreground){
        time(now);if(pending==null)return null;
        if(now-pending.receivedNs>ttlNs){pending=null;expired++;status="EXPLICIT_ACTION_EXPIRED";return null;}
        if(!foreground){status="WAITING_FOR_FOREGROUND";return null;}
        Ticket<T> ticket=pending;pending=null;consumed++;status="CONSUMED_EXPLICIT_ACTION_ONCE";return ticket;
    }
    public synchronized void cancel(String reason){if(pending!=null){pending=null;cancelled++;status="CANCELLED_"+reason;}}
    public synchronized Map<String,Object> snapshot(){LinkedHashMap<String,Object>s=new LinkedHashMap<>();s.put("status",status);s.put("pending",pending!=null);s.put("action",pending==null?null:pending.action);s.put("id",pending==null?null:pending.id);s.put("recentIds",recent.size());s.put("accepted",accepted);s.put("consumed",consumed);s.put("cancelled",cancelled);s.put("replaced",replaced);s.put("expired",expired);s.put("failed",failed);return Collections.unmodifiableMap(s);}
}
