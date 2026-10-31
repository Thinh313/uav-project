package vn.rtr.aeris.control01;
import java.util.*;
import vn.rtr.aeris.betaintegrated01.RunLifecycle;
import vn.rtr.aeris.beta01runtime.Values;

/** Producer-clocked continuous authority. No IO timer may manufacture a sample. */
public final class ControlAuthority {
    public static final long TTL_NS=200000000L;
    public interface Sink {void append(String kind,Map<String,Object> row)throws Exception;}
    public static final class Input {
        public final RunLifecycle.Context context;public final String source,clockDomain,provenance;
        public final long sequence,uptimeNs,elapsedNs,lastMotionUptimeNs;private final double[] axes;
        public final int pointers,motionAction;public final boolean release;
        public Input(RunLifecycle.Context context,String source,String clockDomain,String provenance,long sequence,long uptimeNs,long elapsedNs,long lastMotionUptimeNs,double[]axes,int pointers,int motionAction,boolean release){
            this.context=context;this.source=source;this.clockDomain=clockDomain;this.provenance=provenance;this.sequence=sequence;this.uptimeNs=uptimeNs;this.elapsedNs=elapsedNs;this.lastMotionUptimeNs=lastMotionUptimeNs;this.axes=axes==null?null:axes.clone();this.pointers=pointers;this.motionAction=motionAction;this.release=release;
        }
        public Map<String,Object> row(){return Values.map("run",context.run,"epoch",context.epoch,"boot",context.boot,"operator",context.operator,"generation",context.generation,"profileId",context.profileId,"source",source,"clockDomain",clockDomain,"provenance",provenance,"sequence",sequence,"uptimeNs",uptimeNs,"elapsedNs",elapsedNs,"lastMotionUptimeNs",lastMotionUptimeNs,"axes",axes==null?null:Arrays.asList(axes[0],axes[1],axes[2],axes[3]),"pointers",pointers,"motionAction",motionAction,"release",release);}
        public double axis(int index){return axes[index];}
    }
    private final RunLifecycle.Context context;private final String source,provenance;private final Sink sink;
    private long lastNow=-1,lastInput=-1,lastUptime=-1,offset=Long.MIN_VALUE,expires=-1;private boolean consent,failed;
    private Input latest;private String failure,lease;private long grants,accepted,sent;
    public ControlAuthority(RunLifecycle.Context c,String source,String provenance,Sink sink){if(c==null||source==null||!source.matches("touch-[a-f0-9-]{36}")||!Arrays.asList("ROOT_INJECTED_ANDROID_TOUCH","LOCAL_ANDROID_TOUCH_NOT_HID_ATTESTED").contains(provenance)||sink==null)throw new IllegalArgumentException("INPUT_SOURCE_CONTEXT");context=c;this.source=source;this.provenance=provenance;this.sink=sink;}
    private void event(String kind,Map<String,Object> row)throws Exception {try{sink.append(kind,row);}catch(Exception e){failed=true;consent=false;expires=-1;failure="AUTHORITY_JOURNAL_FAILED";throw e;}}
    private void time(long now)throws Exception{if(failed)throw new IllegalStateException("AUTHORITY_FAILED:"+failure);if(now<0||now<lastNow){failed=true;consent=false;expires=-1;failure="CONTROL_CLOCK_REGRESSION";throw new IllegalStateException(failure);}lastNow=now;}
    private void validate(Input i,long now)throws Exception{
        if(i==null||!context.equals(i.context)||!source.equals(i.source)||!provenance.equals(i.provenance)||!"ANDROID_UPTIME_NS_SAMPLER".equals(i.clockDomain)||i.sequence<0||i.sequence<=lastInput||i.uptimeNs<0||i.uptimeNs<lastUptime||i.elapsedNs<0||i.uptimeNs>i.elapsedNs||i.elapsedNs>now||now-i.elapsedNs>TTL_NS||i.lastMotionUptimeNs<0||i.lastMotionUptimeNs>i.uptimeNs||i.axes==null||i.axes.length!=4||i.pointers<0||i.pointers>2||!Arrays.asList(-1,0,1,2,3,5,6).contains(i.motionAction))throw new IllegalArgumentException("INPUT_CONTEXT_SEQUENCE_CLOCK_OR_AGE");
        for(double a:i.axes)if(!Double.isFinite(a)||a< -1||a>1)throw new IllegalArgumentException("INPUT_AXIS_DOMAIN");
        if(i.pointers==0)for(double a:i.axes)if(a!=0.0)throw new IllegalArgumentException("UNHELD_NONZERO_AXES");
        if(i.motionAction==-1&&(i.pointers!=0||i.lastMotionUptimeNs!=0||i.release))throw new IllegalArgumentException("NO_MOTION_STATE_INVALID");
        if(Arrays.asList(0,2,5).contains(i.motionAction)&&i.pointers==0)throw new IllegalArgumentException("ACTIVE_MOTION_WITHOUT_POINTER");
        if(Arrays.asList(1,3,6).contains(i.motionAction)&&i.pointers!=0)throw new IllegalArgumentException("RELEASE_MOTION_WITH_ACTIVE_POINTER");
        if(i.release&&!Arrays.asList(1,3,6).contains(i.motionAction))throw new IllegalArgumentException("RELEASE_WITHOUT_UP_CANCEL");
        long nextOffset=i.elapsedNs-i.uptimeNs;if(offset!=Long.MIN_VALUE&&Math.abs(nextOffset-offset)>5000000L)throw new IllegalArgumentException("GUEST_UPTIME_ELAPSED_OFFSET_STEP");
    }
    public synchronized void accept(Input i,long now)throws Exception{
        time(now);
        if(consent&&now>expires)revoke("INPUT_LEASE_EXPIRED_BEFORE_NEW_SAMPLE",now);
        try{validate(i,now);}catch(Exception e){event("CONTROL_INPUT_REJECTED",Values.map("reason",e.getMessage(),"sequence",i==null?null:i.sequence,"atNs",now,"fullInvalidInputRetained",false));revoke("INVALID_INPUT",now);throw e;}
        event("CONTROL_INPUT",i.row());latest=i;lastInput=i.sequence;lastUptime=i.uptimeNs;offset=i.elapsedNs-i.uptimeNs;accepted++;
        if(i.release){revoke("POINTER_RELEASE_OR_CANCEL",now);return;}
        if(consent){expires=Math.addExact(i.elapsedNs,TTL_NS);event("CONTROL_LEASE_RENEWED",Values.map("leaseId",lease,"inputSequence",i.sequence,"expiresNs",expires));}
    }
    public synchronized void consent(long now,String actionId)throws Exception{
        time(now);if(actionId==null||!actionId.matches("[A-Za-z0-9_.:-]{1,128}")||latest==null||now-latest.elapsedNs>TTL_NS||latest.release||latest.pointers!=0)throw new IllegalStateException("FRESH_CENTERED_UI_OBSERVATION_REQUIRED");
        for(double a:latest.axes)if(a!=0.0)throw new IllegalStateException("EXACT_NEUTRAL_REQUIRED");
        if(consent)throw new IllegalStateException("CONSENT_ALREADY_ACTIVE");
        String next="lease-"+(grants+1)+"-"+actionId;long until=Math.addExact(latest.elapsedNs,TTL_NS);
        event("CONTROL_CONSENT",Values.map("actionId",actionId,"leaseId",next,"neutralInputSequence",latest.sequence,"source",source,"clockDomain",latest.clockDomain,"provenance",provenance,"expiresNs",until));
        lease=next;consent=true;expires=until;grants++;
    }
    public synchronized Input requireFresh(long now)throws Exception{
        time(now);if(!consent||latest==null||now>expires||now-latest.elapsedNs>TTL_NS){if(consent)revoke("INPUT_LEASE_EXPIRED",now);throw new IllegalStateException("NO_FRESH_CONTROL_LEASE");}return latest;
    }
    public synchronized void bindWire(Input i,byte[]wire,String purpose,long now)throws Exception{
        Input actual=requireFresh(now);if(i!=actual)throw new IllegalStateException("INPUT_REPLACED_OR_FOREIGN");
        event("CONTROL_INPUT_WIRE_BINDING",Values.map("purpose",purpose,"inputSequence",i.sequence,"source",source,"leaseId",lease,"producerElapsedNs",i.elapsedNs,"sendCheckNs",now,"wireSHA256",Values.hash(wire),"wireAxes",Arrays.asList(i.axes[0]*.25,i.axes[1]*.25,i.axes[2]*.25,i.axes[3]*.25)));
    }
    public synchronized void sent(Input i,long now)throws Exception{if(i!=latest)throw new IllegalStateException("INPUT_CHANGED_BEFORE_SENT_OBSERVATION");event("CONTROL_LOCAL_SEND_RETURNED",Values.map("inputSequence",i.sequence,"atNs",now,"executionAccepted",false));sent++;}
    public synchronized boolean tick(long now)throws Exception{time(now);if(consent&&now>expires){revoke("INPUT_LEASE_EXPIRED",now);return true;}return false;}
    public synchronized void revoke(String why,long now)throws Exception{time(now);boolean was=consent;consent=false;expires=-1;event("CONTROL_REVOKED",Values.map("reason",why,"atNs",now,"previousLeaseId",lease,"previouslyActive",was,"lastInputSequence",lastInput,"authorityRestorable",false));lease=null;}
    public synchronized void failure(String why){failed=true;consent=false;expires=-1;failure=why;lease=null;}
    public synchronized Input latest(){return latest;}
    public synchronized Map<String,Object> snapshot(){return Values.map("source",source,"provenance",provenance,"consent",consent&&!failed,"leaseId",lease,"leaseExpiresNs",expires,"lastInputSequence",lastInput,"acceptedInputs",accepted,"grants",grants,"wireBindingsSent",sent,"failed",failed,"failure",failure,"authorityRestorable",false);}
}
