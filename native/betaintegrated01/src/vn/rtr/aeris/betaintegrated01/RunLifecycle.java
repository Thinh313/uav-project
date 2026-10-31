package vn.rtr.aeris.betaintegrated01;

import java.util.*;

/** Pure, serialized lifecycle policy, not flight execution or physical safety proof. */
public final class RunLifecycle {
    public interface Clock { long monotonicNs(); long wallUtcMs(); }
    public interface DurableSink { void append(Map<String,Object> event) throws Exception; }
    public enum Phase { NEW, OPEN, ACTIVE, REVOKED, CLOSING, RESOURCES_CLOSED, SEALED, FAILED_UNCOMMITTED }
    public static final long INPUT_TTL_NS=200000000L;
    public static final class Context {
        public final String run,epoch,boot,operator,generation,profileId;
        public Context(String run,String epoch,String boot,String operator,String generation,String profileId) {
            for(String s:new String[]{run,epoch,boot,operator,generation,profileId})ProviderDescriptor.identifier(s);
            this.run=run;this.epoch=epoch;this.boot=boot;this.operator=operator;this.generation=generation;this.profileId=profileId;
        }
        @Override public boolean equals(Object v) {
            if(!(v instanceof Context))return false;Context c=(Context)v;
            return run.equals(c.run)&&epoch.equals(c.epoch)&&boot.equals(c.boot)&&operator.equals(c.operator)&&generation.equals(c.generation)&&profileId.equals(c.profileId);
        }
        @Override public int hashCode() { return Objects.hash(run,epoch,boot,operator,generation,profileId); }
    }
    public static final class Neutral {
        private final Context context; private final long observed,sequence; private boolean used;
        private Neutral(Context c,long n,long s) { context=c;observed=n;sequence=s; }
    }
    /** Historical view has no methods to connect, activate or restore a grant. */
    public static final class History {
        public final Context context;public final Phase phase;public final long activeElapsedNs,resourceCloseNs,wallClosedMs;
        public final String reviewSHA256;public final boolean authorityRestorable=false;
        public final String scope="HISTORY_ONLY_NOT_CURRENT_AIRCRAFT_STATE";
        private History(Context c,Phase p,long elapsed,long close,long wall,String sha) {
            context=c;phase=p;activeElapsedNs=elapsed;resourceCloseNs=close;wallClosedMs=wall;reviewSHA256=sha;
        }
    }
    private Context context;private final Clock clock;private final DurableSink sink;private final long durationNs;
    private Phase phase=Phase.NEW;private long journalSequence,lastMono=-1,opened=-1,active=-1,deadline=-1;
    private long stopRequested=-1,activityStopped=-1,resourcesClosed=-1,reviewCommitted=-1,wallClosed=-1;
    private String lease=null,reviewSHA=null,failure=null;private long leaseUntil=-1,lastInputSequence=-1;
    private long lastObserved=-1,failureBoundary=-1;
    private boolean committing=false,explicitActivityStop=false,successorAttempted=false;
    public RunLifecycle(Context context,Clock clock,DurableSink sink,long durationNs) {
        if(context==null||clock==null||sink==null||durationNs<=0)throw new IllegalArgumentException("LIFECYCLE_CONSTRUCTOR");
        this.context=context;this.clock=clock;this.sink=sink;this.durationNs=durationNs;
    }
    private long now(Context c) {
        if(committing)throw new IllegalStateException("REENTRANT_STATE_CHANGE");
        if(!context.equals(c))throw new IllegalStateException("FOREIGN_GENERATION_CONTEXT");
        if(phase==Phase.FAILED_UNCOMMITTED)throw new IllegalStateException("FAILED_NO_AUTHORITY");
        long n=clock.monotonicNs();
        if(n<0||n<lastObserved||n<lastMono) {
            // A sealed journal is immutable, including on a rejected late callback.
            if(phase==Phase.SEALED)throw new IllegalStateException("SEALED_CLOCK_REGRESSION");
            event("CLOCK_REGRESSION",lastMono,"observedNs",n);failure="CLOCK_REGRESSION";phase=Phase.FAILED_UNCOMMITTED;clearLease();
            failureBoundary=Math.max(0,Math.max(lastMono,lastObserved));
            throw new IllegalStateException(failure);
        }
        lastObserved=n;
        return n;
    }
    private void event(String kind,long time,Object... values) {
        LinkedHashMap<String,Object> e=new LinkedHashMap<>();e.put("format","aeris-beta-lifecycle-event");e.put("version",1);
        e.put("sequence",journalSequence+1);e.put("kind",kind);e.put("run",context.run);e.put("epoch",context.epoch);
        e.put("boot",context.boot);e.put("operator",context.operator);e.put("generation",context.generation);
        e.put("profileId",context.profileId);e.put("monotonicNs",time);e.put("wallUtcMs",clock.wallUtcMs());
        for(int i=0;i<values.length;i+=2)e.put((String)values[i],values[i+1]);
        committing=true;
        try { sink.append(Collections.unmodifiableMap(e));journalSequence++; }
        catch(Exception ex) { failure="DURABLE_SINK_FAILED";failureBoundary=Math.max(0,Math.max(time,lastObserved));phase=Phase.FAILED_UNCOMMITTED;clearLease();throw new IllegalStateException(failure,ex); }
        finally { committing=false; }
    }
    private void clearLease() { lease=null;leaseUntil=-1; }
    private void require(Phase... allowed) {
        for(Phase p:allowed)if(phase==p)return;
        throw new IllegalStateException("LIFECYCLE_PHASE:"+phase);
    }
    private void live(long n) {
        require(Phase.ACTIVE);
        if(n>deadline) { event("RUN_DEADLINE_EXPIRED",n);lastMono=n;phase=Phase.REVOKED;clearLease();throw new IllegalStateException("RUN_DEADLINE_EXPIRED"); }
    }
    private void expireLease(long n) {
        if(lease!=null&&n>leaseUntil) {
            event("LEASE_EXPIRED",n,"leaseId",lease,"expiresNs",leaseUntil);
            clearLease();lastMono=n;
        }
    }
    public synchronized void begin(Context c,ProviderDescriptor.Binding binding) {
        long n=now(c);require(Phase.NEW);
        if(binding==null||!context.profileId.equals(binding.descriptor.profileId))throw new IllegalStateException("PROVIDER_BINDING_REQUIRED");
        long d;try { d=Math.addExact(n,durationNs); }catch(ArithmeticException e){throw new IllegalArgumentException("DURATION_OVERFLOW",e);}
        event("OPENED",n,"providerMode",binding.descriptor.mode.name(),"binarySHA256",binding.descriptor.binarySHA256,"scope",binding.scope);
        opened=n;deadline=d;lastMono=n;phase=Phase.OPEN;
    }
    public synchronized void activate(Context c) {
        long n=now(c);require(Phase.OPEN);if(n>deadline)throw new IllegalStateException("RUN_DEADLINE_EXPIRED");
        event("ACTIVATED",n,"aircraftSafe",false);active=n;lastMono=n;phase=Phase.ACTIVE;
    }
    public synchronized Neutral observeNeutral(Context c,long inputSeq,long observedNs,double[] axes) {
        long n=now(c);live(n);expireLease(n);input(c,inputSeq,observedNs,axes,n);
        for(double a:axes)if(a!=0.0)throw new IllegalArgumentException("NEUTRAL_REQUIRED");
        event("NEUTRAL_OBSERVED",n,"inputSequence",inputSeq,"observedNs",observedNs);
        lastInputSequence=inputSeq;lastMono=n;return new Neutral(context,observedNs,inputSeq);
    }
    public synchronized void grantLease(Context c,String id,Neutral neutral,long expiresNs) {
        long n=now(c);live(n);ProviderDescriptor.identifier(id);
        if(lease!=null||neutral==null||neutral.used||!context.equals(neutral.context)||neutral.sequence!=lastInputSequence||
           n<neutral.observed||n-neutral.observed>INPUT_TTL_NS||expiresNs<=n||expiresNs>deadline||expiresNs-n>INPUT_TTL_NS)
            throw new IllegalStateException("FRESH_NEUTRAL_BOUND_LEASE_REQUIRED");
        event("LEASE_GRANTED",n,"leaseId",id,"expiresNs",expiresNs,"transportAuthenticated",false);
        neutral.used=true;lease=id;leaseUntil=expiresNs;lastMono=n;
    }
    private void input(Context c,long seq,long observed,double[] axes,long n) {
        if(seq<0||seq<=lastInputSequence||observed<0||observed>n||n-observed>INPUT_TTL_NS||axes==null||axes.length!=4)
            throw new IllegalArgumentException("INPUT_SEQUENCE_OR_AGE");
        for(double a:axes)if(!Double.isFinite(a)||a< -1||a>1)throw new IllegalArgumentException("INPUT_AXES");
    }
    public synchronized void acceptInput(Context c,String id,long seq,long observedNs,double[] axes) {
        long n=now(c);live(n);expireLease(n);input(c,seq,observedNs,axes,n);
        if(lease==null||!lease.equals(id)||n>leaseUntil)throw new IllegalStateException("LEASE_INVALID_OR_EXPIRED");
        event("INPUT_ACCEPTED_POLICY_ONLY",n,"leaseId",id,"inputSequence",seq,"observedNs",observedNs,
              "axes",Collections.unmodifiableList(Arrays.asList(axes[0],axes[1],axes[2],axes[3])),"dispatched",false);
        lastInputSequence=seq;lastMono=n;
    }
    public synchronized void releaseLease(Context c,String id) {
        long n=now(c);live(n);
        if(lease==null||!lease.equals(id))throw new IllegalStateException("LEASE_NOT_OWNED");
        event("LEASE_RELEASED_EXPLICIT",n,"leaseId",id);clearLease();lastMono=n;
    }
    public synchronized void revoke(Context c,String reason) {
        long n=now(c);require(Phase.OPEN,Phase.ACTIVE,Phase.REVOKED);ProviderDescriptor.identifier(reason);
        if(phase==Phase.REVOKED)return;
        event("REVOKED",n,"reason",reason);clearLease();lastMono=n;phase=Phase.REVOKED;
    }
    public synchronized void requestClose(Context c,String reason) {
        long n=now(c);require(Phase.OPEN,Phase.ACTIVE,Phase.REVOKED,Phase.CLOSING);ProviderDescriptor.identifier(reason);
        if(phase==Phase.CLOSING)return;
        event("CLOSE_REQUESTED",n,"reason",reason);clearLease();stopRequested=n;lastMono=n;phase=Phase.CLOSING;
    }
    public synchronized void activityStopped(Context c) {
        long n=now(c);require(Phase.CLOSING);
        if(activityStopped>=0)return;
        event("ACTIVITY_STOP_OBSERVED",n,"aircraftSafe",false);activityStopped=n;explicitActivityStop=true;lastMono=n;
    }
    public synchronized void resourcesClosed(Context c,boolean allOwnedClosed) {
        long n=now(c);require(Phase.CLOSING,Phase.RESOURCES_CLOSED);
        if(!allOwnedClosed)throw new IllegalStateException("EXACT_RESOURCE_CLOSURE_REQUIRED");
        if(phase==Phase.RESOURCES_CLOSED)return;
        long wall=clock.wallUtcMs();event("RESOURCES_CLOSED",n,"allOwnedClosed",true,"aircraftSafe",false);
        resourcesClosed=n;wallClosed=wall;if(activityStopped<0)activityStopped=n;lastMono=n;phase=Phase.RESOURCES_CLOSED;
    }
    public synchronized void reviewCommitted(Context c,String hash) {
        long n=now(c);require(Phase.RESOURCES_CLOSED,Phase.SEALED);ProviderDescriptor.hash(hash,false);
        if(phase==Phase.SEALED) { if(!hash.equals(reviewSHA))throw new IllegalStateException("REVIEW_ALREADY_SEALED_DIFFERENT_SHA");return; }
        event("REVIEW_COMMITTED",n,"reviewSHA256",hash,"authorityRestorable",false);
        reviewCommitted=n;reviewSHA=hash;lastMono=n;phase=Phase.SEALED;
    }
    public synchronized RunLifecycle newSession(Context oldContext,Context next,DurableSink nextSink) {
        long n=now(oldContext);require(Phase.SEALED);
        if(successorAttempted||next==null||nextSink==null||nextSink==sink||next.run.equals(context.run)||next.generation.equals(context.generation)||next.epoch.equals(context.epoch))
            throw new IllegalStateException("FRESH_GENERATION_IDENTITIES_REQUIRED");
        // The old sealed lifecycle and its sink are never reopened or appended.
        // Reserve once, including an unknown/failed next-sink commit: no retry fork.
        successorAttempted=true;
        RunLifecycle created=new RunLifecycle(next,clock,nextSink,durationNs);
        created.event("NEW_SESSION_EXPLICIT",n,"parentRun",context.run,"parentReviewSHA256",reviewSHA,"authorityRestorable",false);
        created.lastMono=n;created.lastObserved=n;return created;
    }
    public synchronized Map<String,Object> snapshot() {
        long n;
        if(resourcesClosed>=0)n=resourcesClosed;
        else if(committing)n=Math.max(0,lastMono);
        else if(phase==Phase.FAILED_UNCOMMITTED)n=failureBoundary;
        else {
            try { n=now(context);if(phase==Phase.ACTIVE)expireLease(n); }
            catch(IllegalStateException ex) {
                if(phase!=Phase.FAILED_UNCOMMITTED)throw ex;
                n=failureBoundary;
            }
        }
        long end=activityStopped>=0?activityStopped:n;
        long elapsed=active<0?0:Math.max(0,end-active);
        LinkedHashMap<String,Object> m=new LinkedHashMap<>();m.put("phase",phase.name());m.put("run",context.run);m.put("generation",context.generation);
        m.put("activeElapsedNs",elapsed);m.put("openedNs",opened);m.put("activeNs",active);m.put("deadlineNs",deadline);
        m.put("closeRequestedNs",stopRequested);m.put("activityStoppedNs",activityStopped);m.put("explicitActivityStop",explicitActivityStop);
        m.put("resourcesClosedNs",resourcesClosed);m.put("reviewCommittedNs",reviewCommitted);m.put("wallClosedUtcMs",wallClosed);
        m.put("reviewSHA256",reviewSHA);m.put("leaseActive",phase==Phase.ACTIVE&&lease!=null&&n<=leaseUntil&&n<=deadline);
        m.put("leaseId",phase==Phase.ACTIVE&&n<=leaseUntil?lease:null);m.put("failure",failure);m.put("journalEvents",journalSequence);
        m.put("successorAttempted",successorAttempted);
        m.put("authorityRestorable",false);m.put("aircraftSafe",false);m.put("scope","MOCK_POLICY_NOT_CONNECTED_TO_TRANSPORT");
        return Collections.unmodifiableMap(m);
    }
    public synchronized History history() {
        Map<String,Object> s=snapshot();
        return new History(context,phase,(Long)s.get("activeElapsedNs"),resourcesClosed,wallClosed,reviewSHA);
    }
}
