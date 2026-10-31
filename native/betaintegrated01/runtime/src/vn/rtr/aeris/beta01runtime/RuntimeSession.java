package vn.rtr.aeris.beta01runtime;
import java.io.*;
import java.util.*;
import java.util.function.BooleanSupplier;
import vn.rtr.aeris.betaintegrated01.*;
import vn.rtr.aeris.native98.WireGate95;

/** One native dispatch owner. Wire events retain original bytes before all parsing/send. */
public final class RuntimeSession {
    private final RunLifecycle lifecycle;private final RunLifecycle.Context context;private final RunLifecycle.Clock clock;
    private final NativeSegments journal;private final BooleanSupplier foreground;private final NativeSegments.Send sender;
    private final boolean manualCapability;private final Mavlink parser=new Mavlink();private final WireGate95 readonly=new WireGate95(new byte[0][]);
    private final FlightReadiness flight=new FlightReadiness();private boolean active,closed,manualConsent;private long inputSequence;private String lease;
    public RuntimeSession(RunLifecycle.Context context,RunLifecycle.Clock clock,ProviderDescriptor expected,ProviderDescriptor.Observation observed,NativeSegments journal,BooleanSupplier foreground,NativeSegments.Send sender,long durationNs,boolean manualCapability)throws Exception {
        this.context=context;this.clock=clock;this.journal=journal;this.foreground=foreground;this.sender=sender;this.manualCapability=manualCapability;
        lifecycle=new RunLifecycle(context,clock,e->journal.append("LIFECYCLE",Values.bytes(e)),durationNs);
        lifecycle.begin(context,expected.validateObserved(observed));
        journal.append("PROVIDER_OBSERVATION",Values.bytes(Values.map("profileId",expected.profileId,"binarySHA256",observed.binarySHA256,"endpoint",observed.endpoint,"observationAuthority","ROOT_OWNED_HOST_LAUNCH_NOT_REMOTE_AUTHENTICATION","mode",observed.mode.name(),"manualCapability",manualCapability)));
    }
    private void live()throws IOException {if(closed||!foreground.getAsBoolean())throw new IOException("NATIVE_CLOSED_OR_BACKGROUND");}
    public synchronized void receive(byte[]raw)throws Exception {
        live();journal.append("RX",raw);long n=clock.monotonicNs()/1000000;readonly.receive(raw,n);parser.receive(raw,(id,sys,comp,sequence,p)->flight.frame(id,sys,comp,sequence,p,n));
        if(!active&&flight.discoveryReady(n)){lifecycle.activate(context);active=true;}
    }
    public synchronized void tick()throws Exception {live();long n=clock.monotonicNs()/1000000;readonly.tick(n);flight.tick(n);Map<String,Object>s=lifecycle.snapshot();if("REVOKED".equals(s.get("phase"))||"FAILED_UNCOMMITTED".equals(s.get("phase")))throw new IOException("LIFECYCLE_NO_AUTHORITY");}
    public synchronized void sendReadOnly(byte[]wire)throws Exception {
        live();readonly.transmit(wire,clock.monotonicNs()/1000000);
        journal.intentSend(wire,b->{live();readonly.transmit(b,clock.monotonicNs()/1000000);sender.write(b);});
    }
    public synchronized void consentManual()throws Exception {
        live();if(!manualCapability||!active)throw new IOException("MANUAL_PROFILE_CAPABILITY_OR_DISCOVERY");
        flight.sealProfile(clock.monotonicNs()/1000000);journal.append("MANUAL_CONSENT",Values.bytes(Values.map("explicit",true,"profileId",context.profileId,"continuousManualQualified",false)));manualConsent=true;
    }
    public synchronized void neutral()throws Exception {
        live();if(!manualConsent)throw new IOException("MANUAL_CONSENT_REQUIRED");
        long now=clock.monotonicNs();RunLifecycle.Neutral token=lifecycle.observeNeutral(context,++inputSequence,now,new double[4]);lease="lease-"+inputSequence;
        lifecycle.grantLease(context,lease,token,Math.addExact(now,RunLifecycle.INPUT_TTL_NS));
    }
    public synchronized void manual(String action,int wireSequence,double[] axes,long observedNs)throws Exception {
        live();if(!manualConsent||lease==null)throw new IOException("FRESH_EXPLICIT_NEUTRAL_REQUIRED");
        flight.requireManualCommand(action,clock.monotonicNs()/1000000);
        double[] a=axes.clone();lifecycle.acceptInput(context,lease,++inputSequence,observedNs,a);
        byte[] wire;
        if("GUIDED".equals(action))wire=Mavlink.command(wireSequence,176,1,4);
        else if("ARM".equals(action))wire=Mavlink.command(wireSequence,400,1,0);
        else if("TAKEOFF".equals(action))wire=Mavlink.command(wireSequence,22,0,0,0,0,0,0,3);
        else if("LAND".equals(action))wire=Mavlink.command(wireSequence,176,1,9);
        else wire=Mavlink.override(wireSequence,(int)(1500+a[0]*100),(int)(1500+a[1]*100),(int)(1500+a[2]*100),(int)(1500+a[3]*100));
        journal.append("MANUAL_BINDING",Values.bytes(Values.map("action",action,"inputSequence",inputSequence,"leaseId",lease,"wireSHA256",Values.hash(wire),"observedNs",observedNs)));
        journal.intentSend(wire,b->{live();flight.requireManualCommand(action,clock.monotonicNs()/1000000);if(!Boolean.TRUE.equals(lifecycle.snapshot().get("leaseActive")))throw new IOException("LEASE_EXPIRED_BEFORE_SEND");sender.write(b);});
        lifecycle.releaseLease(context,lease);lease=null;
    }
    public synchronized void beginClose(String reason)throws Exception {
        if(closed)return;lifecycle.requestClose(context,reason);lifecycle.activityStopped(context);manualConsent=false;lease=null;
    }
    public synchronized String resourcesClosed(boolean ownedSocketClosed)throws Exception {
        if(closed)return Values.json(snapshot());
        lifecycle.resourcesClosed(context,ownedSocketClosed);
        byte[] review=Values.bytes(Values.map("format","aeris-native-review","version",1,"lifecycle",lifecycle.snapshot(),"flight",flight.snapshot(),"authorityRestorable",false,"aircraftExecutionAccepted",false,"nativeWirePendingBytes",parser.pendingBytes()));
        journal.append("REVIEW",review);String sha=Values.hash(review);lifecycle.reviewCommitted(context,sha);
        journal.finish("OWNED_SOCKET_CLOSED_REVIEW_RETAINED");closed=true;return Values.json(snapshot());
    }
    public synchronized void failClose(String reason,boolean socketClosed) {
        try{beginClose(reason);}catch(Exception ignored){}try{resourcesClosed(socketClosed);}catch(Exception ignored){}try{journal.close();}catch(Exception ignored){}closed=true;manualConsent=false;lease=null;
    }
    public synchronized Map<String,Object> snapshot(){return Values.map("format","aeris-native-runtime-state","version",1,"run",context.run,"epoch",context.epoch,"boot",context.boot,"generation",context.generation,"lifecycle",lifecycle.snapshot(),"flight",flight.snapshot(),"journal",journal.snapshot(),"closed",closed,"manualConsent",manualConsent,"authorityRestorable",false,"actualFrameCompletenessFromHostRequired",true,"continuousManualQualified",false);}
}
