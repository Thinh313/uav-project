package vn.rtr.aeris.beta01runtime;
import java.io.*;
import java.net.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.function.*;
import vn.rtr.aeris.betaintegrated01.*;
import vn.rtr.aeris.native98.Profile95;

/** Exactly one owned socket thread, no reconnect or retry after ambiguous send. */
public final class SocketOwner {
    private final File files;private final RuntimeConfig config;private final RunLifecycle.Clock clock;private final NativeSegments.Sync sync;
    private final BooleanSupplier foreground;private final Consumer<String> update;
    private final ArrayBlockingQueue<String> actions=new ArrayBlockingQueue<>(16);
    private volatile boolean stop,running;private volatile String state="{\"phase\":\"NEW\"}";private volatile String reason="EXPLICIT_CLOSE";
    private Thread thread;private Socket socket;private RuntimeSession session;private int sequence;
    public SocketOwner(File files,RuntimeConfig config,RunLifecycle.Clock clock,NativeSegments.Sync sync,BooleanSupplier foreground,Consumer<String> update){this.files=files;this.config=config;this.clock=clock;this.sync=sync;this.foreground=foreground;this.update=update;}
    public synchronized void start(){if(thread!=null)throw new IllegalStateException("OWNER_SINGLE_START");running=true;thread=new Thread(this::loop,"aeris-m1-native-owner");thread.start();}
    public boolean isRunning(){return running;}
    public String state(){return state;}
    public void close(String reason){this.reason=reason;stop=true;Socket s=socket;if(s!=null)try{s.close();}catch(Exception ignored){}}
    public void action(String action)throws IOException{if(!running||stop||!actions.offer(action))throw new IOException("ACTION_OWNER_CLOSED_OR_BOUNDED_QUEUE");}
    private void publish(){if(session!=null)state=Values.json(session.snapshot());update.accept(state);}
    private void loop(){
        NativeSegments journal=null;boolean socketClosed=false;
        try {
            File journals=new File(files,"runs");if(!journals.isDirectory()&&!journals.mkdir())throw new IOException("RUNS_DIRECTORY");
            journal=new NativeSegments(new File(journals,config.context.run),config.context.run,config.context.epoch,clock::monotonicNs,sync,1024*1024,128L*1024*1024,256);
            final Socket connected=new Socket();socket=connected;connected.connect(new InetSocketAddress("10.0.2.2",5961),3000);connected.setTcpNoDelay(true);connected.setSoTimeout(100);
            session=new RuntimeSession(config.context,clock,config.expected,config.observed,journal,foreground,b->{connected.getOutputStream().write(b);connected.getOutputStream().flush();},config.durationNs,config.manualCapability);
            long started=clock.monotonicNs(),lastHeartbeat=-1,lastRefresh=-1,lastUI=-1;int refreshIndex=0;
            List<String> parameters=new ArrayList<>(Profile95.P.keySet());byte[]block=new byte[4096];
            while(!stop){
                if(!foreground.getAsBoolean())throw new IOException("ACTIVITY_BACKGROUND");long now=clock.monotonicNs();
                if(now-started>config.durationNs)throw new IOException("NATIVE_RUN_DURATION_REACHED");
                if(lastHeartbeat<0||now-lastHeartbeat>=1000000000L){session.sendReadOnly(Mavlink.heartbeat(sequence++));lastHeartbeat=now;}
                if(lastRefresh<0||now-lastRefresh>=100000000L){int index=refreshIndex++%(parameters.size()+4);byte[]wire;
                    if(index<parameters.size())wire=Mavlink.parameter(sequence++,parameters.get(index));
                    else if(index==parameters.size())wire=Mavlink.command(sequence++,512,148,0);
                    else if(index==parameters.size()+1)wire=Mavlink.command(sequence++,512,242,0);
                    else wire=Mavlink.command(sequence++,511,index==parameters.size()+2?33:245,200000);
                    session.sendReadOnly(wire);lastRefresh=now;
                }
                String action=actions.poll();if(action!=null){if("CONSENT".equals(action))session.consentManual();else if("NEUTRAL".equals(action))session.neutral();else{session.neutral();session.manual(action,sequence++,new double[4],clock.monotonicNs());}}
                try{int n=connected.getInputStream().read(block);if(n<0)throw new IOException("AP_SOCKET_EOF");if(n>0)session.receive(Arrays.copyOf(block,n));}catch(SocketTimeoutException expected){}catch(IOException e){if(stop&&connected.isClosed())break;throw e;}
                session.tick();now=clock.monotonicNs();if(lastUI<0||now-lastUI>=250000000L){publish();lastUI=now;}
            }
            session.beginClose(reason);connected.close();socketClosed=connected.isClosed();session.resourcesClosed(socketClosed);publish();
        }catch(Exception e){reason=e.getClass().getSimpleName()+":"+e.getMessage();if(socket!=null)try{socket.close();}catch(Exception ignored){}socketClosed=socket==null||socket.isClosed();if(session!=null){session.failClose("RUNTIME_FAILURE",socketClosed);state=Values.json(Values.map("firstFailure",reason,"session",session.snapshot(),"safeLandingClaim",false));}else state=Values.json(Values.map("firstFailure",reason,"phase","FAILED_BEFORE_SESSION","authorityRestorable",false));}
        finally {if(journal!=null)try{journal.close();}catch(Exception ignored){}running=false;update.accept(state);}
    }
}
