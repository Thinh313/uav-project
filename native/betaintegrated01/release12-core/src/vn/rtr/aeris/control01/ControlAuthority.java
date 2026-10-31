package vn.rtr.aeris.control01;
import java.util.*;
import vn.rtr.aeris.betaintegrated01.RunLifecycle;
import vn.rtr.aeris.beta01runtime.Values;
import vn.rtr.aeris.beta01runtime.NativeSegments;

/** Producer-clocked continuous authority. No IO timer may manufacture a sample. */
public final class ControlAuthority {
    public static final long TTL_NS=200000000L;
    public interface Sink {void append(String kind,Map<String,Object> row)throws Exception;}
    public interface CommitSink extends Sink {NativeSegments.Barrier transaction(String kind,Map<String,Object> row)throws Exception;long nowNs();void postCheck(Input input,long nowNs)throws Exception;default long finalDecision(Input input,long floorNs)throws Exception{long decision=nowNs();if(decision<floorNs)throw new IllegalStateException("FINAL_DECISION_CLOCK_REGRESSION");postCheck(input,decision);return decision;}}
    public static final class Input {
        public final RunLifecycle.Context context;public final String source,clockDomain,provenance;
        public final long sequence,uptimeNs,elapsedNs,lastMotionUptimeNs;private final double[] axes;
        public final int pointers,motionAction;public final boolean release;public final Map<String,Object> inputObservation;
        public Input(RunLifecycle.Context context,String source,String clockDomain,String provenance,long sequence,long uptimeNs,long elapsedNs,long lastMotionUptimeNs,double[]axes,int pointers,int motionAction,boolean release){
            this(context,source,clockDomain,provenance,sequence,uptimeNs,elapsedNs,lastMotionUptimeNs,axes,pointers,motionAction,release,null);}
        public Input(RunLifecycle.Context context,String source,String clockDomain,String provenance,long sequence,long uptimeNs,long elapsedNs,long lastMotionUptimeNs,double[]axes,int pointers,int motionAction,boolean release,Map<String,Object>observation){inputObservation=observation==null?null:ReleaseControl.freeze(observation);this.context=context;this.source=source;this.clockDomain=clockDomain;this.provenance=provenance;this.sequence=sequence;this.uptimeNs=uptimeNs;this.elapsedNs=elapsedNs;this.lastMotionUptimeNs=lastMotionUptimeNs;this.axes=axes==null?null:axes.clone();this.pointers=pointers;this.motionAction=motionAction;this.release=release;
        }
        public Map<String,Object> row(){Map<String,Object> row=Values.map("run",context.run,"epoch",context.epoch,"boot",context.boot,"operator",context.operator,"generation",context.generation,"profileId",context.profileId,"source",source,"clockDomain",clockDomain,"provenance",provenance,"sequence",sequence,"uptimeNs",uptimeNs,"elapsedNs",elapsedNs,"lastMotionUptimeNs",lastMotionUptimeNs,"axes",axes==null?null:Arrays.asList(axes[0],axes[1],axes[2],axes[3]),"pointers",pointers,"motionAction",motionAction,"release",release);if(inputObservation!=null)row.put("inputObservation",inputObservation);return row;}
        public double axis(int index){return axes[index];}
    }
    private final RunLifecycle.Context context;private final String source,provenance;private final Sink sink;
    private long lastNow=-1,lastInput=-1,lastCancelledInput=-1,lastUptime=-1,offset=Long.MIN_VALUE,expires=-1;private boolean consent,failed;
    private Map<String,Object>pendingReceipt;private final CommitSink commitSink;private Input latest;private String failure,lease;private long grants,accepted,sent;
    public ControlAuthority(RunLifecycle.Context c,String source,String provenance,Sink sink){if(c==null||source==null||!source.matches("touch-[a-f0-9-]{36}")||!Arrays.asList("ROOT_INJECTED_ANDROID_TOUCH","LOCAL_ANDROID_TOUCH_NOT_HID_ATTESTED").contains(provenance)||sink==null)throw new IllegalArgumentException("INPUT_SOURCE_CONTEXT");context=c;this.source=source;this.provenance=provenance;this.sink=sink;commitSink=sink instanceof CommitSink?(CommitSink)sink:null;}
    private void event(String kind,Map<String,Object> row)throws Exception {try{Map<String,Object>out=new LinkedHashMap<>(row);if(pendingReceipt!=null)out.put("commitReceipt",pendingReceipt);sink.append(kind,out);pendingReceipt=null;}catch(Exception e){failed=true;consent=false;expires=-1;failure="AUTHORITY_JOURNAL_FAILED";throw e;}}
    private void time(long now)throws Exception{if(failed)throw new IllegalStateException("AUTHORITY_FAILED:"+failure);if(now<0||now<lastNow){failed=true;consent=false;expires=-1;failure="CONTROL_CLOCK_REGRESSION";throw new IllegalStateException(failure);}lastNow=now;}
    private void validate(Input i,long now)throws Exception{
        if(i==null||!context.equals(i.context)||!source.equals(i.source)||!provenance.equals(i.provenance)||!"ANDROID_UPTIME_NS_SAMPLER".equals(i.clockDomain)||i.sequence<0||i.sequence<=Math.max(lastInput,lastCancelledInput)||i.uptimeNs<0||i.uptimeNs<lastUptime||i.elapsedNs<0||i.uptimeNs>i.elapsedNs||i.elapsedNs>now||now-i.elapsedNs>TTL_NS||i.lastMotionUptimeNs<0||i.lastMotionUptimeNs>i.uptimeNs||i.axes==null||i.axes.length!=4||i.pointers<0||i.pointers>2||!Arrays.asList(-1,0,1,2,3,5,6).contains(i.motionAction))throw new IllegalArgumentException("INPUT_CONTEXT_SEQUENCE_CLOCK_OR_AGE");
        for(double a:i.axes)if(!Double.isFinite(a)||a< -1||a>1)throw new IllegalArgumentException("INPUT_AXIS_DOMAIN");
        if(i.pointers==0)for(double a:i.axes)if(a!=0.0)throw new IllegalArgumentException("UNHELD_NONZERO_AXES");
        if(i.motionAction==-1&&(i.pointers!=0||i.lastMotionUptimeNs!=0||i.release))throw new IllegalArgumentException("NO_MOTION_STATE_INVALID");
        if(Arrays.asList(0,2,5).contains(i.motionAction)&&i.pointers==0)throw new IllegalArgumentException("ACTIVE_MOTION_WITHOUT_POINTER");
        if(Arrays.asList(1,3,6).contains(i.motionAction)&&i.pointers!=0)throw new IllegalArgumentException("RELEASE_MOTION_WITH_ACTIVE_POINTER");
        if(i.release&&!Arrays.asList(1,3,6).contains(i.motionAction))throw new IllegalArgumentException("RELEASE_WITHOUT_UP_CANCEL");
        observation(i,now);long nextOffset=i.elapsedNs-i.uptimeNs;if(offset!=Long.MIN_VALUE&&Math.abs(nextOffset-offset)>5000000L)throw new IllegalArgumentException("GUEST_UPTIME_ELAPSED_OFFSET_STEP");
    }
    public synchronized void accept(Input i,long now)throws Exception{
        if(commitSink!=null){acceptCommitted(i);return;}time(now);
        if(consent&&now>expires)revoke("INPUT_LEASE_EXPIRED_BEFORE_NEW_SAMPLE",now);
        try{validate(i,now);}catch(Exception e){event("CONTROL_INPUT_REJECTED",Values.map("reason",e.getMessage(),"sequence",i==null?null:i.sequence,"atNs",now,"fullInvalidInputRetained",false));revoke("INVALID_INPUT",now);throw e;}
        event("CONTROL_INPUT",i.row());latest=i;lastInput=i.sequence;lastUptime=i.uptimeNs;offset=i.elapsedNs-i.uptimeNs;accepted++;
        if(i.release){revoke("POINTER_RELEASE_OR_CANCEL",now);return;}
        if(consent){expires=Math.addExact(i.elapsedNs,TTL_NS);event("CONTROL_LEASE_RENEWED",Values.map("leaseId",lease,"inputSequence",i.sequence,"expiresNs",expires));}
    }
    public synchronized void consent(long now,String actionId)throws Exception{
        if(commitSink!=null){consentCommitted(actionId);return;}time(now);if(actionId==null||!actionId.matches("[A-Za-z0-9_.:-]{1,128}")||latest==null||now-latest.elapsedNs>TTL_NS||latest.release||latest.pointers!=0)throw new IllegalStateException("FRESH_CENTERED_UI_OBSERVATION_REQUIRED");
        observation(latest,now);
        for(double a:latest.axes)if(a!=0.0)throw new IllegalStateException("EXACT_NEUTRAL_REQUIRED");
        if(consent)throw new IllegalStateException("CONSENT_ALREADY_ACTIVE");
        String next="lease-"+(grants+1)+"-"+actionId;long until=Math.addExact(latest.elapsedNs,TTL_NS);
        event("CONTROL_CONSENT",Values.map("actionId",actionId,"leaseId",next,"neutralInputSequence",latest.sequence,"source",source,"clockDomain",latest.clockDomain,"provenance",provenance,"expiresNs",until));
        lease=next;consent=true;expires=until;grants++;
    }
    private Map<String,Object>contextRow(){return Values.map("run",context.run,"epoch",context.epoch,"boot",context.boot,"operator",context.operator,"generation",context.generation,"profileId",context.profileId);}
    private Map<String,Object>invalidInput(Input i){if(i==null)return null;List<Object>axes=new ArrayList<>();if(i.axes!=null){if(i.axes.length>8)throw new IllegalArgumentException("INVALID_INPUT_RETAINED_BOUND");for(double a:i.axes)axes.add(Double.isFinite(a)?a:String.valueOf(a));}return Values.map("context",i.context==null?null:Values.map("run",i.context.run,"epoch",i.context.epoch,"boot",i.context.boot,"generation",i.context.generation,"operator",i.context.operator,"profileId",i.context.profileId),"source",i.source,"clockDomain",i.clockDomain,"provenance",i.provenance,"sequence",i.sequence,"uptimeNs",i.uptimeNs,"elapsedNs",i.elapsedNs,"lastMotionUptimeNs",i.lastMotionUptimeNs,"axes",i.axes==null?null:axes,"pointers",i.pointers,"motionAction",i.motionAction,"release",i.release,"inputObservation",i.inputObservation);}
    private NativeSegments.Barrier transaction(String kind,Map<String,Object>row)throws Exception{Map<String,Object>candidate=new LinkedHashMap<>(row);candidate.put("format","aeris-authority-transaction");candidate.put("version",1);candidate.put("context",contextRow());candidate.put("priorCommitReceipt",pendingReceipt);try{NativeSegments.Barrier b=commitSink.transaction(kind,candidate);pendingReceipt=null;return b;}catch(Exception e){failure("AUTHORITY_TRANSACTION_STORAGE_OR_CLOCK_FAILED");throw e;}}
    private Map<String,Object>receipt(String operation,NativeSegments.Barrier b,long decision,String disposition,Map<String,Object>proposal,String reason){return Values.map("format","aeris-authority-commit-receipt","version",1,"context",contextRow(),"operation",operation,"txRecordN",b.recordN,"txPayloadSHA256",b.payloadSHA256,"groupDurableNs",b.durableNs,"decisionNs",decision,"disposition",disposition,"proposal",proposal,"reason",reason,"authorityRestorable",false);}
    private long post(Input i,NativeSegments.Barrier b,long priorExpiry,boolean continuity)throws Exception{time(b.durableNs);validate(i,b.durableNs);if(continuity&&b.durableNs>priorExpiry)throw new IllegalStateException("PRIOR_LEASE_EXPIRED_DURING_INPUT_COMMIT");commitSink.postCheck(i,b.durableNs);long decision=commitSink.nowNs();time(decision);validate(i,decision);commitSink.postCheck(i,decision);decision=commitSink.finalDecision(i,decision);time(decision);validate(i,decision);if(continuity&&decision>priorExpiry)throw new IllegalStateException("PRIOR_LEASE_EXPIRED_BEFORE_AUTHORITY_PUBLICATION");return decision;}
    private void refused(String operation,NativeSegments.Barrier b,Map<String,Object>proposal,Input original,boolean continuity,long priorExpiry,Exception cause)throws Exception{
        if(cause instanceof ReleaseControl.Cancel){
            long decision=commitSink.nowNs();
            try{time(decision);if("INPUT".equals(operation)){validate(original,decision);if(continuity&&decision>priorExpiry)throw new IllegalStateException("PRIOR_LEASE_EXPIRED_BEFORE_CANCELLATION");}else{observation(original,decision);if(decision-original.elapsedNs>TTL_NS)throw new IllegalStateException("CONSENT_INPUT_EXPIRED_BEFORE_CANCELLATION");}}catch(Exception generalFailure){cause=generalFailure;}
            if(cause instanceof ReleaseControl.Cancel){
            ReleaseControl.Cancel c=(ReleaseControl.Cancel)cause;consent=false;expires=-1;c.persistWitness();if("INPUT".equals(operation))lastCancelledInput=Math.max(lastCancelledInput,original.sequence);
            pendingReceipt=receipt(operation,b,decision,"CANCELLED",proposal,"EXPECTED_RELEASE_CANCELLATION");pendingReceipt.put("expectedCancellation",c.details());
            event("CONTROL_COMMIT_CANCELLED",Values.map("reason","EXPECTED_RELEASE_CANCELLATION","atNs",decision,"noAutomaticRegrant",true));c.outcomeDurable=true;throw c;
            }
        }
long decision=commitSink.nowNs();consent=false;expires=-1;lease=null;failed=true;failure="AUTHORITY_COMMIT_REFUSED:"+String.valueOf(cause.getMessage());pendingReceipt=receipt(operation,b,decision,"REFUSED",proposal,String.valueOf(cause.getMessage()));try{event("CONTROL_COMMIT_REFUSED",Values.map("reason",String.valueOf(cause.getMessage()),"atNs",decision,"noAutomaticRegrant",true));}catch(Exception storage){cause.addSuppressed(storage);}throw cause;}
    private void cancelBefore(Input input,ReleaseControl.Cancel c)throws Exception{
        long n=commitSink.nowNs();time(n);observation(input,n);if(n-input.elapsedNs>TTL_NS||consent&&n>expires)throw new IllegalStateException("INPUT_OR_PRIOR_LEASE_EXPIRED_BEFORE_CANCELLATION");consent=false;expires=-1;c.persistWitness();if(input.sequence>lastInput)lastCancelledInput=Math.max(lastCancelledInput,input.sequence);event("CONTROL_INPUT_CANCELLED_BEFORE_COMMIT",Values.map("input",input.row(),"expectedCancellation",c.details(),"atNs",n));c.outcomeDurable=true;throw c;
    }
    private void acceptCommitted(Input i)throws Exception{
        long pre=commitSink.nowNs();time(pre);try{validate(i,pre);if(consent&&pre>expires)throw new IllegalStateException("PRIOR_LEASE_EXPIRED_BEFORE_COMMIT");commitSink.postCheck(i,pre);}catch(ReleaseControl.Cancel c){cancelBefore(i,c);return;}catch(Exception e){event("CONTROL_INPUT_REJECTED",Values.map("reason",e.getMessage(),"sequence",i==null?null:i.sequence,"atNs",pre,"invalidInput",invalidInput(i),"fullInvalidInputRetained",true));revoke("INVALID_INPUT",commitSink.nowNs());throw e;}
        boolean continuity=consent;long priorExpiry=expires;String priorLease=lease;Map<String,Object>proposal=Values.map("kind",i.release?"RELEASE":continuity?"RENEW":"OBSERVE","priorLeaseId",priorLease,"priorExpiryNs",priorExpiry,"proposedLeaseId",i.release?null:priorLease,"proposedExpiryNs",i.release||!continuity?-1:Math.addExact(i.elapsedNs,TTL_NS),"inputSequence",i.sequence);
        NativeSegments.Barrier b=transaction("CONTROL_INPUT_TX",Values.map("operation","INPUT","preWriteNs",pre,"input",i.row(),"proposal",proposal));long decision;
        try{decision=post(i,b,priorExpiry,continuity);}catch(Exception e){refused("INPUT",b,proposal,i,continuity,priorExpiry,e);return;}
        latest=i;lastInput=i.sequence;lastUptime=i.uptimeNs;offset=i.elapsedNs-i.uptimeNs;accepted++;
        if(i.release){consent=false;expires=-1;lease=null;}else if(continuity)expires=Math.addExact(i.elapsedNs,TTL_NS);
        pendingReceipt=receipt("INPUT",b,decision,"ACCEPTED",proposal,null);
        if(i.release)event("CONTROL_REVOKED",Values.map("reason","POINTER_RELEASE_OR_CANCEL","atNs",decision,"previousLeaseId",priorLease,"previouslyActive",continuity,"lastInputSequence",lastInput,"authorityRestorable",false));
    }
    private void consentCommitted(String actionId)throws Exception{
        long pre=commitSink.nowNs();time(pre);if(actionId==null||!actionId.matches("[A-Za-z0-9_.:-]{1,128}")||latest==null||latest.release||latest.pointers!=0||consent)throw new IllegalStateException("FRESH_CENTERED_UI_NO_ACTIVE_CONSENT_REQUIRED");if(pre-latest.elapsedNs>TTL_NS)throw new IllegalStateException("FRESH_CENTERED_UI_OBSERVATION_REQUIRED");observation(latest,pre);try{commitSink.postCheck(latest,pre);}catch(ReleaseControl.Cancel c){cancelBefore(latest,c);return;}for(double a:latest.axes)if(a!=0)throw new IllegalStateException("EXACT_NEUTRAL_REQUIRED");
        String next="lease-"+(grants+1)+"-"+actionId;long until=Math.addExact(latest.elapsedNs,TTL_NS);Map<String,Object>proposal=Values.map("kind","CONSENT","priorLeaseId",null,"priorExpiryNs",-1L,"proposedLeaseId",next,"proposedExpiryNs",until,"inputSequence",latest.sequence,"actionId",actionId);
        NativeSegments.Barrier b=transaction("CONTROL_CONSENT_TX",Values.map("operation","CONSENT","preWriteNs",pre,"neutralInput",latest.row(),"proposal",proposal));long decision;
        try{time(b.durableNs);observation(latest,b.durableNs);if(b.durableNs-latest.elapsedNs>TTL_NS)throw new IllegalStateException("CONSENT_INPUT_EXPIRED_DURING_COMMIT");commitSink.postCheck(latest,b.durableNs);decision=commitSink.nowNs();time(decision);observation(latest,decision);if(decision-latest.elapsedNs>TTL_NS)throw new IllegalStateException("CONSENT_INPUT_EXPIRED_BEFORE_PUBLICATION");commitSink.postCheck(latest,decision);decision=commitSink.finalDecision(latest,decision);time(decision);observation(latest,decision);if(decision-latest.elapsedNs>TTL_NS)throw new IllegalStateException("CONSENT_INPUT_EXPIRED_AT_PUBLICATION");}catch(Exception e){refused("CONSENT",b,proposal,latest,false,-1,e);return;}
        lease=next;consent=true;expires=until;grants++;pendingReceipt=receipt("CONSENT",b,decision,"ACCEPTED",proposal,null);
    }
    public synchronized void flushCommitReceipt()throws Exception{if(pendingReceipt!=null)event("CONTROL_COMMIT_RECEIPT",Values.map("atNs",commitSink.nowNs(),"reason","BEFORE_DISCRETE_ACTION_OR_CLOSE"));}
    private void observation(Input i,long now)throws Exception{
        if(i.inputObservation==null)return;Map<String,Object>o=i.inputObservation;if(!o.keySet().equals(new HashSet<>(Arrays.asList("kind","uiHeartbeatElapsedNs","touchRevision","samplerThreadId","uiThreadId","viewEpoch","releaseFence"))))throw new IllegalArgumentException("SAMPLER_OBSERVATION_FIELDS");
        for(String k:Arrays.asList("uiHeartbeatElapsedNs","touchRevision","samplerThreadId","uiThreadId","viewEpoch","releaseFence"))if(!(o.get(k)instanceof Long)||((Long)o.get(k))<0)throw new IllegalArgumentException("SAMPLER_OBSERVATION_TYPES");
        long ui=(Long)o.get("uiHeartbeatElapsedNs");if(!"IMMUTABLE_UI_TOUCH_STATE_SAMPLE_NOT_NEW_MOTION_EVENT".equals(o.get("kind"))||ui>i.elapsedNs||now-ui>TTL_NS||o.get("samplerThreadId").equals(o.get("uiThreadId"))||((Long)o.get("samplerThreadId"))<=0||((Long)o.get("uiThreadId"))<=0||((Long)o.get("viewEpoch"))<=0)throw new IllegalStateException("UI_LIVENESS_OR_SAMPLER_CONTEXT_STALE");
    }
    public synchronized void cancelPending(Input input,ReleaseControl.Cancel c)throws Exception{validate(input,commitSink.nowNs());cancelBefore(input,c);}
    public synchronized void pendingPure(Input input,long now)throws Exception{if(failed||now<lastNow)throw new IllegalStateException("AUTHORITY_FAILED_OR_CLOCK");validate(input,now);if(consent&&now>expires)throw new IllegalStateException("PRIOR_LEASE_EXPIRED_BEFORE_CANCEL_CHECK");}
    public synchronized Input checkFreshPure(long now)throws Exception{if(failed||now<0||now<lastNow||!consent||latest==null||now>expires||now-latest.elapsedNs>TTL_NS)throw new IllegalStateException("NO_FRESH_CONTROL_LEASE");observation(latest,now);return latest;}
    public synchronized Input requireFresh(long now)throws Exception{
        time(now);if(!consent||latest==null||now>expires||now-latest.elapsedNs>TTL_NS){if(consent)revoke("INPUT_LEASE_EXPIRED",now);throw new IllegalStateException("NO_FRESH_CONTROL_LEASE");}observation(latest,now);return latest;
    }
    public synchronized void bindWire(Input i,byte[]wire,String purpose,long now)throws Exception{
        Input actual=requireFresh(now);if(i!=actual)throw new IllegalStateException("INPUT_REPLACED_OR_FOREIGN");
        event("CONTROL_INPUT_WIRE_BINDING",Values.map("purpose",purpose,"inputSequence",i.sequence,"source",source,"leaseId",lease,"producerElapsedNs",i.elapsedNs,"sendCheckNs",now,"wireSHA256",Values.hash(wire),"wireAxes",Arrays.asList(i.axes[0]*.25,i.axes[1]*.25,i.axes[2]*.25,i.axes[3]*.25)));
    }
    public synchronized void sent(Input i,long now)throws Exception{if(i!=latest)throw new IllegalStateException("INPUT_CHANGED_BEFORE_SENT_OBSERVATION");event("CONTROL_LOCAL_SEND_RETURNED",Values.map("inputSequence",i.sequence,"atNs",now,"executionAccepted",false));sent++;}
    public synchronized void sent(Input i,long now,Map<String,Object>permit)throws Exception{if(permit==null){sent(i,now);return;}if(i!=latest)throw new IllegalStateException("INPUT_CHANGED_BEFORE_SENT_OBSERVATION");event("CONTROL_LOCAL_SEND_RETURNED",Values.map("inputSequence",i.sequence,"atNs",now,"executionAccepted",false,"dispatchPermit",permit));sent++;}
    public synchronized boolean tick(long now)throws Exception{time(now);if(consent){try{observation(latest,now);}catch(Exception e){revoke("UI_LIVENESS_EXPIRED",now);return true;}if(now>expires){revoke("INPUT_LEASE_EXPIRED",now);return true;}}return false;}
    public synchronized void revoke(String why,long now)throws Exception{time(now);boolean was=consent;consent=false;expires=-1;event("CONTROL_REVOKED",Values.map("reason",why,"atNs",now,"previousLeaseId",lease,"previouslyActive",was,"lastInputSequence",lastInput,"authorityRestorable",false));lease=null;}
    public synchronized void revoke(String why,long now,Map<String,Object>releaseCause)throws Exception{if(releaseCause==null){revoke(why,now);return;}if(!Arrays.asList("TRUSTED_TOUCH_RELEASE","EXPECTED_RELEASE_CANCELLATION").contains(why))throw new IllegalArgumentException("RELEASE_CAUSE_REASON");time(now);boolean was=consent;consent=false;expires=-1;event("CONTROL_REVOKED",Values.map("reason",why,"atNs",now,"previousLeaseId",lease,"previouslyActive",was,"lastInputSequence",lastInput,"authorityRestorable",false,"releaseCause",releaseCause));lease=null;}
    public synchronized void failure(String why){failed=true;consent=false;expires=-1;failure=why;lease=null;}
    public synchronized Input latest(){return latest;}
    public synchronized Map<String,Object> snapshot(){return Values.map("source",source,"provenance",provenance,"consent",consent&&!failed,"leaseId",lease,"leaseExpiresNs",expires,"lastInputSequence",lastInput,"acceptedInputs",accepted,"grants",grants,"wireBindingsSent",sent,"failed",failed,"failure",failure,"authorityRestorable",false);}
}
