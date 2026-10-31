import vn.rtr.aeris.betaintegrated01.*;
public class LifecycleEdgeQA {
 interface Check {void run()throws Exception;}
 static int failures=0;
 static void one(String id,Check c){try{c.run();System.out.println("PASS "+id);}catch(Throwable e){failures++;System.out.println("FAIL "+id+" "+e);}}
 public static void main(String[] args){
  one("LE01_expired_lease_read_cannot_restore_after_clock_regression",()->{
   LifecycleQA.Time t=new LifecycleQA.Time();LifecycleQA.Sink s=new LifecycleQA.Sink();RunLifecycle.Context c=LifecycleQA.ctx("read");RunLifecycle l=LifecycleQA.active(c,t,s);
   RunLifecycle.Neutral n=l.observeNeutral(c,1,t.mono,new double[4]);l.grantLease(c,"lease",n,t.mono+100);
   long grant=t.mono;t.mono=grant+101;LifecycleQA.check(Boolean.FALSE.equals(l.snapshot().get("leaseActive")),"expiry read");t.mono=grant+50;
   try{LifecycleQA.check(Boolean.FALSE.equals(l.snapshot().get("leaseActive")),"expired lease restored on read-clock regression");}catch(IllegalStateException e){if(!e.getMessage().contains("CLOCK_REGRESSION"))throw e;}
  });
  one("LE02_parent_can_issue_only_one_successor",()->{
   LifecycleQA.Time t=new LifecycleQA.Time();LifecycleQA.Sink s=new LifecycleQA.Sink();RunLifecycle.Context c=LifecycleQA.ctx("old");RunLifecycle l=LifecycleQA.active(c,t,s);LifecycleQA.close(l,c,t);
   l.newSession(c,LifecycleQA.ctx("new"),new LifecycleQA.Sink());LifecycleQA.reject(()->l.newSession(c,LifecycleQA.ctx("other"),new LifecycleQA.Sink()));
  });
  one("LE03_same_observed_boot_fresh_session_allowed",()->{
   LifecycleQA.Time t=new LifecycleQA.Time();LifecycleQA.Sink s=new LifecycleQA.Sink();RunLifecycle.Context c=LifecycleQA.ctx("oldboot");RunLifecycle l=LifecycleQA.active(c,t,s);LifecycleQA.close(l,c,t);
   RunLifecycle.Context next=new RunLifecycle.Context("newrun","newepoch",c.boot,c.operator,"newgen",c.profileId);l.newSession(c,next,new LifecycleQA.Sink());
  });
  one("LE04_failed_history_remains_inspectable",()->{
   LifecycleQA.Time t=new LifecycleQA.Time();LifecycleQA.Sink s=new LifecycleQA.Sink();RunLifecycle.Context c=LifecycleQA.ctx("failed");RunLifecycle l=LifecycleQA.active(c,t,s);s.fail=true;LifecycleQA.reject(()->l.revoke(c,"drop"));
   LifecycleQA.check("FAILED_UNCOMMITTED".equals(l.snapshot().get("phase")),"terminal snapshot");LifecycleQA.check(!l.history().authorityRestorable,"terminal history has no authority");
  });
  System.out.println("scope=PURE_JAVA_MOCK failures="+failures);if(failures>0)System.exit(2);
 }
}
