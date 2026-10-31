import java.util.*;
import vn.rtr.aeris.control01.ControlAuthority;
import vn.rtr.aeris.betaintegrated01.RunLifecycle;
import vn.rtr.aeris.beta01runtime.Values;
public final class AuthorityQA {
 interface Op{void run()throws Exception;}
 static final String SOURCE="touch-11111111-1111-1111-1111-111111111111",PROV="ROOT_INJECTED_ANDROID_TOUCH";
 static final RunLifecycle.Context CTX=new RunLifecycle.Context("qa-run","epoch01","boot01","operator01","generation01","profile01");
 static final long BASE=1000000000L;static List<Map<String,Object>>results=new ArrayList<>();
 static void check(boolean b,String s){if(!b)throw new AssertionError(s);}
 static void denied(Op o,String s)throws Exception{boolean fail=false;try{o.run();}catch(Exception e){fail=true;}check(fail,s);}
 static void test(String id,Op o){try{o.run();results.add(Values.map("id",id,"pass",true));}catch(Throwable e){results.add(Values.map("id",id,"pass",false,"error",e.toString()));}}
 static ControlAuthority make(){return new ControlAuthority(CTX,SOURCE,PROV,(k,r)->{});}
 static ControlAuthority.Input sample(long seq,long elapsed,int pointers,int action,boolean release,double axis){return new ControlAuthority.Input(CTX,SOURCE,"ANDROID_UPTIME_NS_SAMPLER",PROV,seq,elapsed-100000000L,elapsed,action==-1?0:elapsed-100000000L,new double[]{axis,0,0,0},pointers,action,release);}
 static void neutral(ControlAuthority a)throws Exception{a.accept(sample(1,BASE,0,-1,false,0),BASE);a.consent(BASE,"consent01");}
 public static void main(String[]args)throws Exception{
  test("A01_FRESH_NEUTRAL_AND_CURRENT_HELD_INPUT",()->{ControlAuthority a=make();neutral(a);ControlAuthority.Input i=sample(2,BASE+50000000,1,2,false,.2);a.accept(i,BASE+50000000);check(a.requireFresh(BASE+50000001)==i,"not fresh");});
  test("A02_EXPIRED_CONSENT_CANNOT_REVIVE_IN_ACCEPT",()->{ControlAuthority a=make();neutral(a);long n=BASE+300000000L;try{a.accept(sample(2,n,1,2,false,.2),n);}catch(Exception allowed){}denied(()->a.requireFresh(n),"expired old consent revived");check(Boolean.FALSE.equals(a.snapshot().get("consent")),"consent remains active");});
  test("A03_UNHELD_NONZERO_INPUT_REJECTED",()->{ControlAuthority a=make();neutral(a);long n=BASE+50000000;denied(()->a.accept(sample(2,n,0,2,false,.2),n),"nonzero axes without pointer");check(Boolean.FALSE.equals(a.snapshot().get("consent")),"bad input did not revoke");});
  test("A04_UNKNOWN_MOTION_ACTION_REJECTED",()->{ControlAuthority a=make();neutral(a);long n=BASE+50000000;denied(()->a.accept(sample(2,n,1,9999,false,.2),n),"unknown action accepted");});
  test("A05_IMPOSSIBLE_ANDROID_CLOCK_ORDER_REJECTED",()->{ControlAuthority a=make();long n=BASE;ControlAuthority.Input i=new ControlAuthority.Input(CTX,SOURCE,"ANDROID_UPTIME_NS_SAMPLER",PROV,1,n+1,n,n,new double[4],0,2,false);denied(()->a.accept(i,n),"uptime greater than elapsed accepted");});
  test("A06_POINTER_RELEASE_NEVER_AUTO_RECONSENT",()->{ControlAuthority a=make();neutral(a);long n=BASE+50000000;a.accept(sample(2,n,0,1,true,0),n);n+=50000000;final long at=n;a.accept(sample(3,n,0,1,false,0),n);denied(()->a.requireFresh(at),"neutral restored consent");});
  test("A07_DUPLICATE_INPUT_REVOKES",()->{ControlAuthority a=make();neutral(a);denied(()->a.accept(sample(1,BASE+1,0,2,false,0),BASE+1),"duplicate accepted");check(Boolean.FALSE.equals(a.snapshot().get("consent")),"duplicate failed to revoke");});
  test("A08_SINK_FAILURE_REMOVES_AUTHORITY",()->{boolean[]fail={false};ControlAuthority a=new ControlAuthority(CTX,SOURCE,PROV,(k,r)->{if(fail[0])throw new java.io.IOException("QA_SINK_FAILED");});neutral(a);fail[0]=true;denied(()->a.accept(sample(2,BASE+1,1,2,false,.1),BASE+1),"sink fault accepted");check(Boolean.TRUE.equals(a.snapshot().get("failed"))&&Boolean.FALSE.equals(a.snapshot().get("consent")),"sink not failclosed");});
  System.out.println(Values.json(Values.map("format","aeris-independent-control-authority-qa","results",results,"scope","PURE_JVM_POLICY_NO_WIRE_OR_ANDROID")));
 }
}
