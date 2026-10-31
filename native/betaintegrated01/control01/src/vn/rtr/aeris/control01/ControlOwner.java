package vn.rtr.aeris.control01;
import java.io.*;
import java.net.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.function.*;
import vn.rtr.aeris.betaintegrated01.*;
import vn.rtr.aeris.beta01runtime.*;

/** Process singleton. Exactly one native socket/writer; no reconnect or stale resend. */
public final class ControlOwner {
    public interface Listener {void update(String ownerIdentity,String state);}
    private interface Message {void apply(ControlSession session)throws Exception;}
    private static ControlOwner current;private static String latestIdentity;
    public static synchronized boolean latest(String identity){return Objects.equals(latestIdentity,identity);}
    private static synchronized void reserve(ControlOwner owner){if(current!=null)throw new IllegalStateException("PREVIOUS_NATIVE_OWNER_NOT_CLOSED");current=owner;latestIdentity=owner.identity;}
    private static synchronized void release(ControlOwner owner){if(current==owner)current=null;}
    private final File files;private final ControlConfig config;private final RunLifecycle.Clock clock;private final NativeSegments.Sync sync;private final BooleanSupplier foreground;private final Listener listener;
    private final ArrayBlockingQueue<Message> queue=new ArrayBlockingQueue<>(128);private final String source,identity;
    private volatile boolean running,stop;private volatile String stopReason="EXPLICIT_OPERATOR_CLOSE",queueFailure,state="{\"phase\":\"NEW\"}";
    private Thread thread;private Socket socket;private ControlSession session;
    public ControlOwner(File files,ControlConfig config,RunLifecycle.Clock clock,NativeSegments.Sync sync,BooleanSupplier foreground,Listener listener,String source){this.files=files;this.config=config;this.clock=clock;this.sync=sync;this.foreground=foreground;this.listener=listener;this.source=source;identity=config.context.run+":"+config.context.generation;}
    public synchronized void start(){if(thread!=null)throw new IllegalStateException("CONTROL_OWNER_SINGLE_START");reserve(this);running=true;thread=new Thread(this::loop,"aeris-control01-native-writer");try{thread.start();}catch(RuntimeException|Error e){running=false;release(this);throw e;}}
    public boolean running(){return running&&!stop;}public String identity(){return identity;}public String state(){return state;}
    public void close(String reason){stopReason=reason;stop=true;Socket s=socket;if(s!=null)try{s.close();}catch(Exception ignored){}}
    private void offer(Message m){if(!running||stop)return;if(!queue.offer(m)){queueFailure="INPUT_QUEUE_OVERFLOW_NOT_DURABLY_ADMITTED";close("INPUT_QUEUE_OVERFLOW");}}
    public void input(ControlAuthority.Input i){offer(s->s.input(i));}
    public void motion(Map<String,Object> raw){Map<String,Object>copy=Collections.unmodifiableMap(new LinkedHashMap<>(raw));offer(s->s.motion(copy));}
    public void action(String action,String id,String displayedHome,long producerElapsedNs){offer(s->{try{s.action(action,id,displayedHome,producerElapsedNs);}catch(Exception e){if(!s.actionRefusalRecoverable(e))throw e;}});}
    private void publish(){if(session!=null)state=Values.json(session.snapshot());listener.update(identity,state);}
    private void loop(){NativeSegments journal=null;boolean socketClosed=false;
        try{
            File runs=new File(files,"control-runs");if(!runs.isDirectory()&&!runs.mkdir())throw new IOException("CONTROL_RUNS_DIRECTORY");
            journal=new NativeSegments(new File(runs,config.context.run),config.context.run,config.context.epoch,clock::monotonicNs,sync,1024*1024,128L*1024*1024,256);
            Socket connected=new Socket();socket=connected;connected.connect(new InetSocketAddress("10.0.2.2",5961),3000);connected.setTcpNoDelay(true);connected.setSoTimeout(25);
            session=new ControlSession(config.context,clock,config.expected,config.observed,journal,()->foreground.getAsBoolean()&&!stop,b->{connected.getOutputStream().write(b);connected.getOutputStream().flush();},config.typed,source,config.provenance,config.durationNs);
            for(int id:new int[]{0,1,24,30,33,193,245})session.stream(id);
            long start=clock.monotonicNs(),lastHB=-1,lastHome=-1,lastVersion=-1,lastParam=-1,lastUI=-1;List<String>params=new ArrayList<>(config.typed.keySet());int paramIndex=0;byte[]block=new byte[4096];
            while(!stop){
                if(!foreground.getAsBoolean())throw new IOException("CONTROL_NOT_FOREGROUND");long now=clock.monotonicNs();session.observeLoop(now);if(now-start>config.durationNs)throw new IOException("CONTROL_RUN_DEADLINE");
                if(lastHB<0||now-lastHB>=500000000L){session.heartbeat();lastHB=now;}
                if(lastHome<0||now-lastHome>=750000000L){session.request(242);lastHome=now;}
                if(lastVersion<0||now-lastVersion>=2000000000L){session.request(148);lastVersion=now;}
                if(lastParam<0||now-lastParam>=100000000L){session.parameter(params.get(paramIndex++%params.size()));lastParam=now;}
                for(int n=0;n<16;n++){Message m=queue.poll();if(m==null)break;m.apply(session);if(stop)break;}
                if(stop)break;
                try{int n=connected.getInputStream().read(block);long receipt=clock.monotonicNs();if(n<0)throw new IOException("CONTROL_AP_EOF");if(n>0)session.receive(Arrays.copyOf(block,n),receipt);}catch(SocketTimeoutException expected){}catch(IOException e){if(stop&&connected.isClosed())break;throw e;}
                session.tick();now=clock.monotonicNs();if(lastUI<0||now-lastUI>=250000000L){publish();lastUI=now;}
            }
            if(queueFailure!=null)throw new IOException(queueFailure);connected.close();socketClosed=connected.isClosed();session.close(stopReason,socketClosed);publish();
        }catch(Exception e){if(socket!=null)try{socket.close();}catch(Exception ignored){}socketClosed=socket==null||socket.isClosed();String reason=e.getClass().getSimpleName()+":"+e.getMessage();if(session!=null){session.fail(reason,socketClosed);state=Values.json(session.snapshot());}else state=Values.json(Values.map("firstFailure",reason,"phase","FAILED_BEFORE_SESSION","run",config.context.run,"authorityRestorable",false));}
        finally{if(journal!=null)try{journal.close();}catch(Exception ignored){}running=false;listener.update(identity,state);release(this);}
    }
}
