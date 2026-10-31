import vn.rtr.aeris.betaintegrated01.ProviderDescriptor;
import vn.rtr.aeris.betaintegrated01.RunLifecycle;
import java.util.*;

/** Calls actual Java product classes. Zero Android, network or dispatch. */
public final class LifecycleTest {
  static int assertions=0;
  static void check(boolean x,String why){assertions++;if(!x)throw new AssertionError(why);}
  static void rejects(Runnable op,String why){try{op.run();throw new AssertionError("accepted "+why);}catch(IllegalArgumentException|IllegalStateException|UnsupportedOperationException expected){assertions++;}}
  static class Clock implements RunLifecycle.Clock {long mono=100,wall=10000;public long monotonicNs(){return mono;}public long wallUtcMs(){return wall;}}
  static class Sink implements RunLifecycle.DurableSink {
    final List<Map<String,Object>> rows=new ArrayList<>();String failKind;RunLifecycle lifecycle;
    public void append(Map<String,Object> e)throws Exception {
      if(lifecycle!=null){Map<String,Object> before=lifecycle.snapshot();if("OPENED".equals(e.get("kind")))check("NEW".equals(before.get("phase")),"publish before commit");}
      if(e.get("kind").equals(failKind))throw new java.io.IOException("injected");
      rows.add(e);
    }
  }
  static RunLifecycle.Context ctx(String suffix){return new RunLifecycle.Context("run"+suffix,"epoch"+suffix,"boot"+suffix,"pilot","generation"+suffix,"baseline");}
  static String sha(char c){char[] x=new char[64];Arrays.fill(x,c);return new String(x);}
  static ProviderDescriptor descriptor(){return new ProviderDescriptor(1,ProviderDescriptor.Mode.INTERNAL_REGRESSION,"baseline",ProviderDescriptor.INTERNAL_AP,null,sha('a'),"tcp://127.0.0.1:19001","4.7.1");}
  static ProviderDescriptor.Observation observation(ProviderDescriptor d,String endpoint){return new ProviderDescriptor.Observation(d.version,d.mode,d.profileId,d.binarySHA256,d.modelSHA256,d.configSHA256,endpoint,d.firmware,true);}
  static RunLifecycle opened(Clock t,Sink sink,RunLifecycle.Context c){RunLifecycle l=new RunLifecycle(c,t,sink,1000000000L);sink.lifecycle=l;l.begin(c,descriptor().validateObserved(observation(descriptor(),"tcp://127.0.0.1:19001")));l.activate(c);return l;}
  public static void main(String[] args)throws Exception {
    ProviderDescriptor d=descriptor();check(d.validateObserved(observation(d,d.endpoint)).scope.contains("NOT_AUTHENTICATION"),"scope");
    rejects(()->d.validateObserved(observation(d,"tcp://127.0.0.1:19002")),"foreign endpoint");
    rejects(()->new ProviderDescriptor(1,ProviderDescriptor.Mode.CANDIDATE_EXTERNAL,"candidate",null,null,sha('a'),d.endpoint,"4.7.1").validateObserved(null),"null candidate");
    rejects(()->new ProviderDescriptor(1,ProviderDescriptor.Mode.CANDIDATE_EXTERNAL,"candidate",ProviderDescriptor.INTERNAL_AP,sha('b'),sha('a'),d.endpoint,"4.7.1"),"baseline candidate alias");
    rejects(()->new ProviderDescriptor(1,d.mode,"baseline",d.binarySHA256,null,d.configSHA256,"tcp://example.com:19001","4.7.1"),"remote endpoint");
    rejects(()->new ProviderDescriptor(1,d.mode,"baseline",d.binarySHA256,null,null,d.endpoint,"4.7.1"),"null config");
    Clock t=new Clock();Sink s=new Sink();RunLifecycle.Context c=ctx("1");RunLifecycle l=opened(t,s,c);
    double[] zero={0,0,0,0};RunLifecycle.Neutral neutral=l.observeNeutral(c,1,t.mono,zero);l.grantLease(c,"lease1",neutral,t.mono+100);
    double[] axes={.1,.2,.3,.4};l.acceptInput(c,"lease1",2,t.mono,axes);axes[0]=.9;
    List<?> retained=(List<?>)s.rows.get(s.rows.size()-1).get("axes");check(((Double)retained.get(0))==.1,"input copy");
    rejects(()->((List)retained).set(0,1.0),"immutable retained axes");
    rejects(()->l.acceptInput(ctx("foreign"),"lease1",3,t.mono,zero),"foreign context");
    rejects(()->l.acceptInput(c,"lease1",2,t.mono,zero),"sequence replay");
    t.mono+=101;rejects(()->l.acceptInput(c,"lease1",3,t.mono,zero),"expired lease");check(!((Boolean)l.snapshot().get("leaseActive")),"expired no authority");
    rejects(()->l.grantLease(c,"lease2",neutral,t.mono+100),"used neutral token");
    RunLifecycle.Neutral n2=l.observeNeutral(c,3,t.mono,zero);l.grantLease(c,"lease2",n2,t.mono+100);l.revoke(c,"LINK_LOST");
    rejects(()->l.acceptInput(c,"lease2",4,t.mono,zero),"revoked input");rejects(()->l.activate(c),"revoked no reactivate");
    rejects(()->l.resourcesClosed(c,true),"close before request");rejects(()->l.reviewCommitted(c,sha('f')),"review before close");
    t.mono=300;l.requestClose(c,"USER_STOP");l.requestClose(c,"USER_STOP");t.mono=400;l.activityStopped(c);t.mono=500;l.resourcesClosed(c,true);
    long frozen=(Long)l.snapshot().get("activeElapsedNs");check(frozen==300,"activity vs resource boundary");
    t.wall=-10000;t.mono=600;l.reviewCommitted(c,sha('f'));int sealedEvents=s.rows.size();l.reviewCommitted(c,sha('f'));
    check(s.rows.size()==sealedEvents,"duplicate seal no append");t.wall=999999;t.mono=900;check((Long)l.snapshot().get("activeElapsedNs")==frozen,"closed elapsed immutable");
    check(l.history().authorityRestorable==false,"history no lease restore");
    Sink nextSink=new Sink();RunLifecycle next=l.newSession(c,ctx("2"),nextSink);check("NEW".equals(next.snapshot().get("phase")),"new run explicit begin required");
    check("SEALED".equals(l.snapshot().get("phase"))&&s.rows.size()==sealedEvents,"old sealed unchanged");
    rejects(()->next.activate(c),"old callback new run");rejects(()->l.newSession(c,ctx("2"),s),"sealed sink reuse");
    rejects(()->l.newSession(c,ctx("3"),new Sink()),"sealed parent cannot fork");
    Sink failed=new Sink();Clock t2=new Clock();RunLifecycle fault=opened(t2,failed,ctx("f"));failed.failKind="RESOURCES_CLOSED";fault.requestClose(ctx("f"),"TEST");
    rejects(()->fault.resourcesClosed(ctx("f"),true),"closure sink failure");
    check("FAILED_UNCOMMITTED".equals(fault.snapshot().get("phase")),"failed diagnostic readable");
    check(!((Boolean)fault.snapshot().get("leaseActive"))&&fault.history().authorityRestorable==false,"failed history no authority");
    rejects(()->fault.reviewCommitted(ctx("f"),sha('e')),"failed no review");
    check(failed.rows.stream().noneMatch(e->"RESOURCES_CLOSED".equals(e.get("kind"))),"not falsely closed");
    Clock t3=new Clock();Sink s3=new Sink();RunLifecycle regression=opened(t3,s3,ctx("r"));t3.mono=99;rejects(()->regression.revoke(ctx("r"),"TEST"),"clock regression");
    check(s3.rows.stream().anyMatch(e->"CLOCK_REGRESSION".equals(e.get("kind"))),"regression durable");
    Clock t4=new Clock();Sink s4=new Sink();RunLifecycle reads=opened(t4,s4,ctx("read"));RunLifecycle.Neutral rn=reads.observeNeutral(ctx("read"),1,t4.mono,zero);reads.grantLease(ctx("read"),"lease",rn,t4.mono+100);
    t4.mono=201;check(!((Boolean)reads.snapshot().get("leaseActive")),"read observes expiry");t4.mono=150;check(!((Boolean)reads.snapshot().get("leaseActive")),"read regression cannot revive lease");check("FAILED_UNCOMMITTED".equals(reads.snapshot().get("phase")),"read regression fences");
    check(s.rows.stream().noneMatch(e->Boolean.TRUE.equals(e.get("dispatched"))),"no actual dispatch");
    for(int i=0;i<s.rows.size();i++)check(((Number)s.rows.get(i).get("sequence")).longValue()==i+1,"sequence");
    System.out.println("PASS actual Java8 pure logic; assertions="+assertions+"; Android=0; sockets=0; dispatch=0");
  }
}
