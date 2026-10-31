package vn.rtr.aeris.control01;
import java.io.*;
import java.util.*;
import java.util.function.*;
import vn.rtr.aeris.betaintegrated01.*;
import vn.rtr.aeris.beta01runtime.*;

/** Sole native wire path for operator input, assisted commands and finite de-escalation. */
public final class ControlSession {
    private final RunLifecycle.Context context;private final RunLifecycle.Clock clock;private final RunLifecycle lifecycle;
    private final NativeSegments journal;private final BooleanSupplier foreground;private final NativeSegments.Send sender;
    private final ControlAuthority authority;private final ControlFlight flight;private final Mavlink parser=new Mavlink();
    private final long runDeadline;private long lastObserved=-1;
    private long loopObserved=-1,maxLoopGap,maxRxApplyGap;
    private int wireSequence;private long lastPilotSequence=-1,releaseDeadline=-1;private boolean active,closed,rcActive;
    private String releaseState="NONE",firstFailure;private boolean releaseRCRequired;
    private final Set<String> actionIds=new HashSet<>();
    public ControlSession(RunLifecycle.Context context,RunLifecycle.Clock clock,ProviderDescriptor expected,ProviderDescriptor.Observation observed,NativeSegments journal,BooleanSupplier foreground,NativeSegments.Send sender,Map<String,int[]> typed,String inputSource,String provenance,long durationNs)throws Exception{
        this.context=context;this.clock=clock;this.journal=journal;this.foreground=foreground;this.sender=sender;runDeadline=Math.addExact(clock.monotonicNs(),durationNs);
        lifecycle=new RunLifecycle(context,clock,e->journal.append("LIFECYCLE",Values.bytes(e)),durationNs);lifecycle.begin(context,expected.validateObserved(observed));
        authority=new ControlAuthority(context,inputSource,provenance,(kind,event)->journal.append(kind,Values.bytes(event)));
        flight=new ControlFlight(typed,(kind,event)->journal.append(kind,Values.bytes(event)));
        journal.append("CONTROL_PROVIDER",Values.bytes(Values.map("run",context.run,"epoch",context.epoch,"boot",context.boot,"generation",context.generation,"binarySHA256",observed.binarySHA256,"configSHA256",observed.configSHA256,"source",inputSource,"inputProvenance",provenance,"modeLabel","LOITER_ASSISTED_PILOT_NOT_ACRO","rootObservationTrust","LOCAL_ORCHESTRATION_NOT_REMOTE_AUTHENTICATION")));
    }
    private long now(){return clock.monotonicNs();}
    private void live()throws IOException{if(closed)throw new IOException("CONTROL_SESSION_CLOSED");long n=now();if(n<0||n<lastObserved||n>runDeadline||loopObserved>=0&&n-loopObserved>500000000L||!foreground.getAsBoolean()){if(firstFailure==null)firstFailure=n>runDeadline?"CONTROL_SESSION_DEADLINE":n<0||n<lastObserved?"CONTROL_SESSION_CLOCK_REGRESSION":loopObserved>=0&&n-loopObserved>500000000L?"CONTROL_LOOP_IO_GAP":"CONTROL_OWNER_BACKGROUND";authority.failure(firstFailure);}lastObserved=Math.max(lastObserved,n);if(closed||firstFailure!=null)throw new IOException("CONTROL_OWNER_BACKGROUND_CLOSED_OR_FAILED:"+firstFailure);}
    public synchronized void observeLoop(long receiptNs)throws Exception{long n=now();if(receiptNs<0||receiptNs>n||n-receiptNs>500000000L||loopObserved>=0&&receiptNs-loopObserved>500000000L){authority.failure("CONTROL_LOOP_IO_GAP");firstFailure="CONTROL_LOOP_IO_GAP";throw new IOException(firstFailure);}if(loopObserved>=0)maxLoopGap=Math.max(maxLoopGap,receiptNs-loopObserved);loopObserved=receiptNs;live();event("CONTROL_LOOP_OBSERVATION",Values.map("producerElapsedNs",receiptNs,"maxGapNs",maxLoopGap));}
    private void event(String kind,Map<String,Object> e)throws Exception{journal.append(kind,Values.bytes(e));}
    private void transmit(byte[]wire,RunnableApproval approval)throws Exception{
        live();byte[]immutable=wire.clone();journal.intentSend(immutable,b->{live();approval.check();sender.write(b.clone());});
    }
    public interface RunnableApproval {void check()throws Exception;}
    public synchronized void readOnly(byte[]wire)throws Exception{
        // Wire comes only from the finite native factories below, never external raw input.
        live();if(wire==null||wire.length<13||(wire[0]&255)!=253||wire[2]!=0||wire[3]!=0||(wire[5]&255)!=255||(wire[6]&255)!=190||wire.length!=12+(wire[1]&255))throw new IOException("READONLY_PACKET_HEADER");int id=(wire[7]&255)|(wire[8]&255)<<8|(wire[9]&255)<<16;if(id!=0&&id!=20&&id!=76)throw new IOException("READONLY_FACTORY_MESSAGE");
        int[]d=vn.rtr.aeris.native98.Dialect95.D.get(id);int length=wire[1]&255;if(length<1||length>d[1]||Mavlink.crc(wire,10+length,d[2])!=Mavlink.u16(wire,10+length))throw new IOException("READONLY_CRC_LENGTH");byte[]p=new byte[d[1]];System.arraycopy(wire,10,p,0,length);
        if(id==0&&(Mavlink.u32(p,0)!=0||p[4]!=6||p[5]!=8||p[6]!=0||p[7]!=4||p[8]!=3))throw new IOException("READONLY_GCS_HEARTBEAT");
        if(id==20&&(p[2]!=42||p[3]!=1||Mavlink.u16(p,0)!=65535))throw new IOException("READONLY_PARAMETER_TARGET");
        if(id==20){int end=4;while(end<20&&p[end]!=0)end++;String name=new String(p,4,end-4,java.nio.charset.StandardCharsets.US_ASCII);if(!flight.hasParameter(name))throw new IOException("READONLY_PARAMETER_PROFILE");}
        if(id==76){if(p[30]!=42||p[31]!=1||p[32]!=0)throw new IOException("READONLY_COMMAND_TARGET");int command=Mavlink.u16(p,28);float one=Mavlink.f32(p,0),two=Mavlink.f32(p,4);if(command==512){if((one!=148&&one!=242)||two!=0)throw new IOException("READONLY_REQUEST_ID");}else if(command==511){if(!Arrays.asList(0f,1f,24f,30f,33f,193f,245f).contains(one)||two!=200000)throw new IOException("READONLY_STREAM_ID");}else throw new IOException("READONLY_COMMAND");for(int i=2;i<7;i++)if(Mavlink.f32(p,i*4)!=0)throw new IOException("READONLY_COMMAND_EXTRA");}
        transmit(wire,()->{});
    }
    public synchronized void heartbeat()throws Exception{readOnly(Mavlink.heartbeat(wireSequence++));}
    public synchronized void parameter(String name)throws Exception{readOnly(Mavlink.parameter(wireSequence++,name));}
    public synchronized void request(int id)throws Exception{readOnly(Mavlink.command(wireSequence++,512,id,0));}
    public synchronized void stream(int id)throws Exception{readOnly(Mavlink.command(wireSequence++,511,id,200000));}
    public synchronized void motion(Map<String,Object> raw)throws Exception{live();if(!Objects.equals(raw.get("source"),authority.snapshot().get("source")))throw new IOException("MOTION_SOURCE_GENERATION_MISMATCH");event("TOUCH_MOTION_EVENT",Values.map("run",context.run,"epoch",context.epoch,"boot",context.boot,"operator",context.operator,"generation",context.generation,"profileId",context.profileId,"inputProvenance",authority.snapshot().get("provenance"),"raw",raw));}
    public synchronized void input(ControlAuthority.Input input)throws Exception{
        live();boolean previouslyConsented=Boolean.TRUE.equals(authority.snapshot().get("consent"));authority.accept(input,now());
        if(previouslyConsented&&!Boolean.TRUE.equals(authority.snapshot().get("consent"))){requestRelease(input.release?"TOUCH_UP_CANCEL":"EXPIRED_BEFORE_NEW_INPUT");return;}
        if(Boolean.TRUE.equals(authority.snapshot().get("consent"))&&flight.mode()==5&&flight.isAirborne()&&"NONE".equals(releaseState))sendPilot(input);
    }
    private void sendPilot(ControlAuthority.Input input)throws Exception{
        if(input.sequence<=lastPilotSequence)throw new IOException("RC_INPUT_ALREADY_DISPATCHED");flight.pilot(now()/1000000);byte[]wire=RcWire.pilot(wireSequence++,input);
        authority.bindWire(input,wire,"RC_LOITER_PILOT",now());
        transmit(wire,()->{authority.requireFresh(now());if(authority.latest()!=input)throw new IOException("INPUT_CHANGED_BEFORE_WIRE");flight.pilot(now()/1000000);});
        rcActive=true;lastPilotSequence=input.sequence;authority.sent(input,now());
    }
    public synchronized void receive(byte[]raw)throws Exception{receive(raw,now());}
    public synchronized void receive(byte[]raw,long receiptNs)throws Exception{if(closed)throw new IOException("LATE_RX_AFTER_SEALED_CLOSURE_NOT_APPENDED");journal.append("RX",raw);event("AP_RX_RECEIPT",Values.map("receiptElapsedNs",receiptNs,"afterRawFsyncNs",now(),"wireSHA256",Values.hash(raw),"kernelNetworkAge","NOT_MEASURED"));live();if(receiptNs<0||receiptNs>now())throw new IOException("RAW_RX_CLOCK_INVALID_RETAINED");maxRxApplyGap=Math.max(maxRxApplyGap,now()-receiptNs);if(now()-receiptNs>200000000L){authority.failure("RAW_RX_APPLY_IO_GAP");firstFailure="RAW_RX_APPLY_IO_GAP";event("AP_RX_APPLY_REFUSED",Values.map("receiptNs",receiptNs,"applyNs",now()));throw new IOException(firstFailure);}parser.receive(raw,(id,sys,comp,seq,p)->flight.frame(id,sys,comp,seq,p,receiptNs/1000000));if(!active&&flight.discovery(now()/1000000)){lifecycle.activate(context);active=true;}advanceRelease();}
    public synchronized void action(String action,String actionId,String displayedHomeHash,long producerElapsedNs)throws Exception{
        live();long n=now();if(actionId==null||!actionId.matches("[A-Za-z0-9_.:-]{1,128}")||producerElapsedNs<0||producerElapsedNs>n||n-producerElapsedNs>1000000000L||actionIds.contains(actionId)||actionIds.size()>=128)throw new IOException("FRESH_ACTION_CONTEXT_OR_REPLAY");
        event("OPERATOR_TOUCH_ACTION",Values.map("action",action,"actionId",actionId,"producerElapsedNs",producerElapsedNs,"receiptElapsedNs",n,"displayedHomeHash",displayedHomeHash,"source","ANDROID_BUTTON_CLICK_NOT_NETWORK_RETIMESTAMPED"));
        actionIds.add(actionId);
        if("CONSENT".equals(action)){if("WAIT_HOLD".equals(releaseState))throw new IOException("RELEASE_IN_PROGRESS");flight.consent(n/1000000);authority.consent(n,actionId);releaseState="NONE";return;}
        if("RELEASE".equals(action)||"HOLD".equals(action)){authority.requireFresh(n);requestRelease("OPERATOR_HOLD_RELEASE");return;}
        ControlAuthority.Input input=authority.requireFresh(n);
        if("CONFIRM_HOME".equals(action)){flight.confirmHome(displayedHomeHash,n/1000000,actionId);return;}
        flight.action(action,n/1000000);
        if("LAND".equals(action)&&rcActive)throw new IOException("OBSERVED_HOLD_RC_RELEASE_BEFORE_LAND_REQUIRED");
        final byte[]wire;
        if("GUIDED".equals(action))wire=Mavlink.command(wireSequence++,176,1,4);
        else if("ARM".equals(action))wire=Mavlink.command(wireSequence++,400,1,0);
        else if("TAKEOFF".equals(action))wire=Mavlink.command(wireSequence++,22,0,0,0,0,0,0,3);
        else if("LOITER".equals(action))wire=Mavlink.command(wireSequence++,176,1,5);
        else if("LAND".equals(action))wire=Mavlink.command(wireSequence++,176,1,9);
        else throw new IOException("ASSISTED_ACTION_ALLOWLIST");
        authority.bindWire(input,wire,action,now());
        transmit(wire,()->{authority.requireFresh(now());if(authority.latest()!=input)throw new IOException("ACTION_INPUT_REPLACED");flight.action(action,now()/1000000);if("ARM".equals(action))flight.armIntent();});authority.sent(input,now());
        if("LAND".equals(action))authority.revoke("EXPLICIT_LAND_SENT_NO_MORE_PILOT_INPUT",now());
    }
    private void requestRelease(String reason)throws Exception{
        if("WAIT_HOLD".equals(releaseState)||"RELEASED".equals(releaseState))return;
        authority.revoke(reason,now());
        if(!flight.isAirborne()){releaseState="RELEASED";event("RC_RELEASE_NOT_NEEDED",Values.map("reason",reason,"noActiveRCOverrideSent",!rcActive,"airborne",false));return;}
        releaseRCRequired=rcActive;
        flight.safety(now()/1000000);event("SAFETY_RELEASE_REQUESTED",Values.map("reason",reason,"lastPilotInputSequence",lastPilotSequence,"cleanupPacketBudget",3,"requiresObservedBrake17BeforeNeutralRelease",true));
        releaseDeadline=Math.addExact(now(),1500000000L);releaseState="WAIT_HOLD";byte[]brake=Mavlink.command(wireSequence++,176,1,17);
        transmit(brake,()->flight.safety(now()/1000000));
    }
    private void advanceRelease()throws Exception{
        if(!"WAIT_HOLD".equals(releaseState))return;if(now()>releaseDeadline)throw new IOException("BRAKE17_NOT_OBSERVED_BEFORE_RELEASE_DEADLINE");
        if(flight.mode()!=17)return;
        event("SAFETY_BRAKE17_OBSERVED",Values.map("atNs",now(),"mode",17));
        if(releaseRCRequired){byte[]neutral=RcWire.neutral(wireSequence++);transmit(neutral,()->{flight.safety(now()/1000000);if(flight.mode()!=17)throw new IOException("OBSERVED_BRAKE_REQUIRED");});
        byte[]release=RcWire.release(wireSequence++);transmit(release,()->{flight.safety(now()/1000000);if(flight.mode()!=17)throw new IOException("OBSERVED_BRAKE_REQUIRED");});}
        rcActive=false;releaseState="RELEASED";event(releaseRCRequired?"RC_NEUTRAL_AND_RELEASE_WRITTEN":"BRAKE_HOLD_NO_RC_RELEASE_NEEDED",Values.map("atNs",now(),"neutralAndReleaseWritten",releaseRCRequired,"cleanupPacketsWritten",releaseRCRequired?3:1,"localWriteOnly",true,"userAuthorityRestored",false));
    }
    public synchronized void tick()throws Exception{live();flight.tick(now()/1000000);boolean expired=authority.tick(now());if(expired||rcActive&&!Boolean.TRUE.equals(authority.snapshot().get("consent"))&&"NONE".equals(releaseState))requestRelease("INPUT_PRODUCER_EXPIRED_OR_REVOKED");advanceRelease();lifecycle.snapshot();}
    public synchronized boolean actionRefusalRecoverable(Exception error)throws Exception{if(Boolean.TRUE.equals(journal.snapshot().get("failed"))||Boolean.TRUE.equals(flight.snapshot().get("failed"))||Boolean.TRUE.equals(authority.snapshot().get("failed"))||firstFailure!=null)return false;event("OPERATOR_ACTION_REFUSED",Values.map("reason",error.getMessage(),"atNs",now(),"automaticRetry",false));return true;}
    public synchronized void close(String reason,boolean socketClosed)throws Exception{
        if(closed)return;authority.revoke(reason,now());if(rcActive||"WAIT_HOLD".equals(releaseState))event("RC_RELEASE_UNSENT_UNKNOWN",Values.map("reason",reason,"socketClosed",socketClosed,"safetyState",releaseState,"lastPilotInputSequence",lastPilotSequence,"noRetry",true));
        lifecycle.requestClose(context,reason);lifecycle.activityStopped(context);lifecycle.resourcesClosed(context,socketClosed);
        byte[] review=Values.bytes(Values.map("flight",flight.snapshot(),"input",authority.snapshot(),"releaseState",releaseState,"authorityRestorable",false,"APExecutionAccepted",false));journal.append("CONTROL_REVIEW",review);lifecycle.reviewCommitted(context,Values.hash(review));journal.finish("CONTROL_OWNED_RESOURCES_CLOSED");closed=true;
    }
    public synchronized void fail(String reason,boolean socketClosed){if(firstFailure==null)firstFailure=reason;authority.failure(reason);try{event("CONTROL_FAILURE",Values.map("reason",reason,"socketClosed",socketClosed,"releaseOutcome","UNSENT_UNKNOWN_IF_RC_WAS_ACTIVE","authorityRestorable",false));}catch(Exception ignored){}try{lifecycle.requestClose(context,"CONTROL_FAILURE");lifecycle.activityStopped(context);lifecycle.resourcesClosed(context,socketClosed);byte[]review=Values.bytes(snapshot());journal.append("CONTROL_REVIEW",review);lifecycle.reviewCommitted(context,Values.hash(review));journal.finish("CONTROL_FAILED_RESOURCES_CLOSED");}catch(Exception ignored){}try{journal.close();}catch(Exception ignored){}closed=true;}
    public synchronized Map<String,Object> snapshot(){String ready=null;if(!closed&&firstFailure==null)try{flight.ready(now()/1000000,!flight.isArmed());}catch(Exception e){ready=e.getMessage();}return Values.map("format","aeris-control01-state","version",1,"run",context.run,"epoch",context.epoch,"boot",context.boot,"generation",context.generation,"lifecycle",lifecycle.snapshot(),"flight",flight.snapshot(),"input",authority.snapshot(),"preflightReady",ready==null&&!closed&&firstFailure==null,"preflightReason",ready,"releaseState",releaseState,"maxLoopGapNs",maxLoopGap,"maxRxApplyGapNs",maxRxApplyGap,"rcOverrideActiveLocally",rcActive,"lastPilotSequence",lastPilotSequence,"firstFailure",firstFailure,"journal",journal.snapshot(),"closed",closed,"authorityRestorable",false,"inputMapping","ROLL_RIGHT+,PITCH_FORWARD+,THROTTLE_UP+,YAW_CLOCKWISE+; PWM1500+125*{roll,-pitch,throttle,yaw}");}
}
