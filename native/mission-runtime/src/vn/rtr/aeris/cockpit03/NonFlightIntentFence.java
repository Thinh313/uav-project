package vn.rtr.aeris.cockpit03;
import java.io.IOException;
import java.util.Arrays;
import vn.rtr.aeris.beta01runtime.PendingExplicitAction;
import vn.rtr.aeris.beta01runtime.Values;
/** Nonflight envelope adapter; delegates the accepted TTL/replay/foreground/clock policy unchanged. */
public final class NonFlightIntentFence<T> {
 private static final class Envelope<T>{final String action;final T payload;Envelope(String a,T p){action=a;payload=p;}}
 public static final class Ticket<T>{public final String id,action;public final T payload;public final long receivedNs;private Ticket(PendingExplicitAction.Ticket<Envelope<T>>t){id=t.id;action=t.payload.action;payload=t.payload.payload;receivedNs=t.receivedNs;}}
 private final PendingExplicitAction<Envelope<T>> delegate;
 public NonFlightIntentFence(long ttlNs,int recentLimit){delegate=new PendingExplicitAction<>(ttlNs,recentLimit);}
 public void enqueue(String id,String action,T payload,long now){if(action==null||!Arrays.asList("STAGE_BINDING","CLOSE","STATUS").contains(action)||payload==null){delegate.cancel("NONFLIGHT_ACTION_REJECTED");throw new IllegalArgumentException("VISIBLE_NATIVE_CONNECT_AND_FLIGHT_TOUCH_ONLY");}delegate.enqueue(id,action.equals("STAGE_BINDING")?"STATUS":action,new Envelope<>(action,payload),now);}
 public Ticket<T> consume(long now,boolean foreground){PendingExplicitAction.Ticket<Envelope<T>>t=delegate.consume(now,foreground);return t==null?null:new Ticket<>(t);}
 public void cancel(String reason){delegate.cancel(reason);}
 public static String verifyBindingSHA(byte[]observed,String expected)throws IOException{if(observed==null||observed.length>65536||expected==null||!expected.matches("[a-f0-9]{64}")||!expected.equals(Values.hash(observed)))throw new IOException("BINDING_STAGE_SHA");return expected;}
}
