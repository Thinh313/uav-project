import vn.rtr.aeris.betaintegrated01.*;
import java.util.*;
import java.util.concurrent.*;
public final class LifecycleQA {
 static final String HASH=String.join("",Collections.nCopies(64,"a"));
 static final String OTHER=String.join("",Collections.nCopies(64,"b"));
 static final class Time implements RunLifecycle.Clock {long mono=100,wall=200;public long monotonicNs(){return mono;}public long wallUtcMs(){return wall;}}
 static final class Sink implements RunLifecycle.DurableSink {final List<Map<String,Object>> rows=new ArrayList<>();boolean fail;public void append(Map<String,Object> e)throws Exception{if(fail)throw new Exception("QA_FAIL");rows.add(e);}}
 static void check(boolean b,String s){if(!b)throw new AssertionError(s);}
 static String reject(Runnable r){try{r.run();}catch(RuntimeException e){return e.getMessage();}throw new AssertionError("EXPECTED_REJECTION");}
 static RunLifecycle.Context ctx(String n){return new RunLifecycle.Context("run"+n,"epoch"+n,"boot"+n,"operator","generation"+n,"profile");}
 static ProviderDescriptor descriptor(){return new ProviderDescriptor(1,ProviderDescriptor.Mode.INTERNAL_REGRESSION,"profile",ProviderDescriptor.INTERNAL_AP,null,HASH,"tcp://127.0.0.1:17600","4.7.1");}
 static ProviderDescriptor.Binding binding(){ProviderDescriptor d=descriptor();return d.validateObserved(new ProviderDescriptor.Observation(1,d.mode,d.profileId,d.binarySHA256,d.modelSHA256,d.configSHA256,d.endpoint,d.firmware,true));}
 static RunLifecycle active(RunLifecycle.Context c,Time t,Sink s){RunLifecycle l=new RunLifecycle(c,t,s,1000000000L);l.begin(c,binding());t.mono+=10;l.activate(c);return l;}
 static void close(RunLifecycle l,RunLifecycle.Context c,Time t){t.mono+=10;l.requestClose(c,"user");t.mono+=10;l.activityStopped(c);t.mono+=10;l.resourcesClosed(c,true);t.mono+=10;l.reviewCommitted(c,HASH);}
 public static void main(String[] args)throws Exception {
  List<String> passed=new ArrayList<String>(){public boolean add(String s){System.out.println("PASS "+s);return super.add(s);}};
  ProviderDescriptor d=descriptor();reject(()->d.validateObserved(new ProviderDescriptor.Observation(1,d.mode,d.profileId,d.binarySHA256,d.modelSHA256,d.configSHA256,d.endpoint,d.firmware,false)));
  ProviderDescriptor unbuilt=new ProviderDescriptor(1,ProviderDescriptor.Mode.CANDIDATE_EXTERNAL,"profile",null,null,HASH,"tcp://127.0.0.1:17600","4.7.1");reject(()->unbuilt.validateObserved(new ProviderDescriptor.Observation(1,unbuilt.mode,"profile",null,null,HASH,unbuilt.endpoint,"4.7.1",true)));
  reject(()->new ProviderDescriptor(1,d.mode,"profile",ProviderDescriptor.INTERNAL_AP,null,HASH,"tcp://evil.example:17600","4.7.1"));passed.add("P01_provider_structural_mismatch_and_unbuilt_refused");
  Time t=new Time();Sink s=new Sink();RunLifecycle.Context c=ctx("1");RunLifecycle l=active(c,t,s);close(l,c,t);long elapsed=(Long)l.snapshot().get("activeElapsedNs");int count=s.rows.size();t.mono+=50000000;t.wall=-999999999;check((Long)l.snapshot().get("activeElapsedNs")==elapsed,"elapsed must freeze");check(!l.history().authorityRestorable,"history authority");check(s.rows.size()==count,"reads do not append");passed.add("L01_closed_elapsed_walljump_stable");
  reject(()->l.snapshot().put("phase","ACTIVE"));reject(()->s.rows.get(0).put("run","forged"));passed.add("L02_immutable_snapshots_and_events");
  RunLifecycle.Context next=ctx("2");Sink ns=new Sink();RunLifecycle n=l.newSession(c,next,ns);check("NEW".equals(n.snapshot().get("phase")),"new phase");check(Boolean.FALSE.equals(n.snapshot().get("leaseActive")),"lease not restored");reject(()->n.activate(c));check(s.rows.size()==count,"old sealed sink unchanged");reject(()->l.newSession(c,next,s));passed.add("L03_new_session_fenced_old_callbacks_no_grant_restore");
  Time lt=new Time();Sink ls=new Sink();RunLifecycle.Context lc=ctx("3");RunLifecycle live=active(lc,lt,ls);double[] axes={0,0,0,0};RunLifecycle.Neutral neutral=live.observeNeutral(lc,1,lt.mono,axes);live.grantLease(lc,"lease",neutral,lt.mono+100000000);axes[0]=1;
  live.acceptInput(lc,"lease",2,lt.mono,new double[]{.1,.2,.3,.4});Object axis=ls.rows.get(ls.rows.size()-1).get("axes");reject(()->((List)axis).set(0,99));live.revoke(lc,"lost-link");reject(()->live.acceptInput(lc,"lease",3,lt.mono,new double[4]));reject(()->live.grantLease(lc,"lease2",neutral,lt.mono+100));check(Boolean.FALSE.equals(live.snapshot().get("leaseActive")),"revoke clears");passed.add("L04_neutral_one_use_mutable_alias_and_revoke");
  Time st=new Time();Sink ss=new Sink();RunLifecycle.Context sc=ctx("4");RunLifecycle sl=active(sc,st,ss);reject(()->sl.observeNeutral(sc,1,st.mono,new double[]{Double.NaN,0,0,0}));reject(()->sl.observeNeutral(sc,1,st.mono+1,new double[4]));st.mono+=300000001;reject(()->sl.observeNeutral(sc,1,1,new double[4]));passed.add("L05_stale_future_nonfinite_input_refused");
  Time ft=new Time();Sink fs=new Sink();RunLifecycle.Context fc=ctx("5");RunLifecycle fl=active(fc,ft,fs);fs.fail=true;reject(()->fl.revoke(fc,"drop"));check("FAILED_UNCOMMITTED".equals(fl.history().phase.name()),"sinkfail terminal");check(!fl.history().authorityRestorable,"failure authority");reject(()->fl.activate(fc));passed.add("L06_sink_failure_poisons_without_restore");
  Time rt=new Time();Sink rs=new Sink();RunLifecycle.Context rc=ctx("6");RunLifecycle race=active(rc,rt,rs);RunLifecycle.Neutral rn=race.observeNeutral(rc,1,rt.mono,new double[4]);race.grantLease(rc,"lease",rn,rt.mono+100000000);
  CountDownLatch go=new CountDownLatch(1);List<String> outcomes=Collections.synchronizedList(new ArrayList<>());
  Thread a=new Thread(()->{try{go.await();race.acceptInput(rc,"lease",2,rt.mono,new double[4]);outcomes.add("input");}catch(Exception e){outcomes.add("refused");}});
  Thread b=new Thread(()->{try{go.await();race.revoke(rc,"drop");}catch(Exception e){throw new RuntimeException(e);}});a.start();b.start();go.countDown();a.join();b.join();int revoked=-1,lastInput=-1;for(int i=0;i<rs.rows.size();i++){if("REVOKED".equals(rs.rows.get(i).get("kind")))revoked=i;if("INPUT_ACCEPTED_POLICY_ONLY".equals(rs.rows.get(i).get("kind")))lastInput=i;}
  check(revoked>=0&&lastInput<revoked,"no accepted input after revoke");check(!((Boolean)race.snapshot().get("leaseActive")),"race lease cleared");passed.add("L07_serialized_revoke_input_race");
  Time ct=new Time();Sink cs=new Sink();RunLifecycle.Context cc=ctx("7");RunLifecycle cl=active(cc,ct,cs);cl.requestClose(cc,"user");reject(()->cl.resourcesClosed(cc,false));check("CLOSING".equals(cl.snapshot().get("phase")),"unknown closure not closed");reject(()->cl.reviewCommitted(cc,HASH));cl.resourcesClosed(cc,true);cl.reviewCommitted(cc,HASH);int end=cs.rows.size();cl.reviewCommitted(cc,HASH);check(cs.rows.size()==end,"idempotent review");reject(()->cl.reviewCommitted(cc,OTHER));passed.add("L08_unknown_close_and_duplicate_commit_fenced");
  for(String p:passed)System.out.println("PASS "+p);System.out.println("SCOPE PURE_JAVA_MOCK_NO_TRANSPORT_OR_AIRCRAFT_AUTHENTICATION");
 }
}
