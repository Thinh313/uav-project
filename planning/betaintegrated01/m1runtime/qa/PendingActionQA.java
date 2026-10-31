import vn.rtr.aeris.beta01runtime.PendingExplicitAction;
import java.util.*;
public final class PendingActionQA {
 interface O{void run()throws Exception;}
 static List<String> passed=new ArrayList<>();static void check(boolean b){if(!b)throw new AssertionError();}
 static void deny(O o)throws Exception{boolean got=false;try{o.run();}catch(IllegalArgumentException|IllegalStateException e){got=true;}check(got);}
 static PendingExplicitAction<String> q(){return new PendingExplicitAction<>(2000000000L,16);}
 static void t(String id,O o)throws Exception{o.run();passed.add(id);}
 public static void main(String[]a)throws Exception{
  t("P01_QUEUE_BEFORE_RESUME_ONCE",()->{PendingExplicitAction<String>q=q();q.enqueue("one","CONNECT","payload",1);check(q.consume(2,false)==null);check(q.consume(3,true).id.equals("one"));check(q.consume(4,true)==null);});
  t("P02_EXPIRY_NO_DISPATCH",()->{PendingExplicitAction<String>q=q();q.enqueue("one","CONNECT","payload",1);check(q.consume(2000000002L,true)==null);check(q.consume(2000000003L,true)==null);check(((Number)q.snapshot().get("expired")).longValue()==1);});
  t("P03_PAUSE_CANCEL_NO_RESTORE",()->{PendingExplicitAction<String>q=q();q.enqueue("one","CONNECT","payload",1);q.cancel("ACTIVITY_PAUSED");check(q.consume(2,true)==null);});
  t("P04_REPLACEMENT_ONLY_LATEST",()->{PendingExplicitAction<String>q=q();q.enqueue("one","CONNECT","payload",1);q.enqueue("two","CLOSE","payload",2);check(q.consume(3,true).id.equals("two"));check(((Number)q.snapshot().get("replaced")).longValue()==1);});
  t("P05_INVALID_NEW_CANCELS_OLD",()->{PendingExplicitAction<String>q=q();q.enqueue("one","CONNECT","payload",1);deny(()->q.enqueue("two","FOREIGN","payload",2));check(q.consume(3,true)==null);});
  t("P06_REPLAY_CANCELS_OLD",()->{PendingExplicitAction<String>q=q();q.enqueue("one","CONNECT","payload",1);check(q.consume(2,true)!=null);q.enqueue("two","CLOSE","payload",3);deny(()->q.enqueue("one","CONNECT","payload",4));check(q.consume(5,true)==null);});
  t("P07_REGRESSION_POISONS",()->{PendingExplicitAction<String>q=q();q.enqueue("one","CONNECT","payload",100);deny(()->q.consume(99,true));deny(()->q.enqueue("two","CONNECT","payload",101));check(Boolean.TRUE.equals(q.snapshot().get("failed")));});
  t("P08_BOUNDED_RECENT_AND_SNAPSHOT",()->{PendingExplicitAction<String>q=q();for(int i=0;i<100;i++){q.enqueue("id-"+i,"STATUS","payload",i*2);q.consume(i*2+1,true);}check(((Number)q.snapshot().get("recentIds")).intValue()==16);try{q.snapshot().put("pending",true);throw new AssertionError();}catch(UnsupportedOperationException expected){}});
  System.out.println("{\"status\":\"PASS\",\"groups\":8,\"ids\":\""+passed.toString()+"\"}");
 }
}
