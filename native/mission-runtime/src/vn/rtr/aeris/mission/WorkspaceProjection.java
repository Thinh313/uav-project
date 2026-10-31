package vn.rtr.aeris.mission;
import java.io.IOException;
import java.util.concurrent.atomic.AtomicReference;
import vn.rtr.aeris.beta01runtime.Values;
import org.json.*;

/** Immutable presentation cache. Never a replacement for durable WorkspaceStore or native authority. */
public final class WorkspaceProjection {
 public static final class View {
  public final String json,sha256;public final long version,observedNs,mutationSerial;public final int mutations;public final boolean initialized,pendingRefresh;
  private View(String j,long v,long n,long s,int m,boolean init,boolean pending){json=j;sha256=Values.hash(j.getBytes(java.nio.charset.StandardCharsets.UTF_8));version=v;observedNs=n;mutationSerial=s;mutations=m;initialized=init;pendingRefresh=pending;}
  public JSONObject provenance()throws Exception{return new JSONObject().put("version",version).put("sha256",sha256).put("canonicalJSON",json).put("observedElapsedNs",observedNs).put("mutationSerial",mutationSerial).put("pendingRefresh",pendingRefresh).put("initialized",initialized).put("scope","LAST_PUBLISHED_IMMUTABLE_WORKSPACE_NOT_NEWEST_DISK_WHILE_PENDING");}
 }
 private final AtomicReference<View> current=new AtomicReference<>(new View("{\"draft\":null,\"draftSHA256\":null,\"reviews\":[],\"authorityRestorable\":false}",0,-1,0,0,false,true));
 public View capture(){return current.get();}
 public long begin()throws IOException{for(;;){View s=current.get();if(s.mutations>=4)throw new IOException("WORKSPACE_MUTATION_CAPACITY");View next=new View(s.json,s.version,s.observedNs,Math.addExact(s.mutationSerial,1),s.mutations+1,s.initialized,true);if(current.compareAndSet(s,next))return next.mutationSerial;}}
 public void end()throws IOException{for(;;){View s=current.get();if(s.mutations<1)throw new IOException("WORKSPACE_MUTATION_UNBALANCED");View next=new View(s.json,s.version,s.observedNs,Math.addExact(s.mutationSerial,1),s.mutations-1,s.initialized,true);if(current.compareAndSet(s,next))return;}}
 public boolean publish(long expectedSerial,String json,long observedNs)throws Exception{if(json==null||json.getBytes(java.nio.charset.StandardCharsets.UTF_8).length>131072||observedNs<0)throw new IOException("WORKSPACE_PROJECTION_BOUND");new JSONObject(json);View s=current.get();if(s.mutations!=0||s.mutationSerial!=expectedSerial)return false;if(s.initialized&&observedNs<s.observedNs)throw new IOException("WORKSPACE_PROJECTION_CLOCK");View next=new View(json,Math.addExact(s.version,1),observedNs,s.mutationSerial,0,true,false);return current.compareAndSet(s,next);}
}
