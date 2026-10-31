package vn.rtr.aeris.native98;
import java.util.*;import java.util.function.Consumer;
/** Ordered, bounded, one-in-flight WebView delivery. Never retries a failed batch. */
public final class UiPump98{
 public interface Scheduler{void post(Runnable work);}public interface Evaluator{void evaluate(List<String>events,Runnable consumed)throws Exception;}
 private final Scheduler scheduler;private final Evaluator evaluator;private final Consumer<String>failure;private final ArrayDeque<String>queue=new ArrayDeque<>();private boolean scheduled,failed;private int totalCount,totalChars,inflightCount,inflightChars;private long serial,flight;
 public UiPump98(Scheduler scheduler,Evaluator evaluator,Consumer<String>failure){this.scheduler=scheduler;this.evaluator=evaluator;this.failure=failure;}
 public void enqueue(String event){boolean overflow=false;synchronized(this){if(failed)return;if(event==null||event.length()>16384||totalCount>=64||totalChars+event.length()>524288)overflow=true;else{queue.add(event);totalCount++;totalChars+=event.length();schedule();}}if(overflow)fail("UI_PUMP_BOUND_NO_RETRY");}
 private void schedule(){if(scheduled||flight!=0||queue.isEmpty()||failed)return;scheduled=true;scheduler.post(()->flush());}
 private void flush(){List<String>batch=new ArrayList<>();long id;synchronized(this){scheduled=false;if(failed||flight!=0||queue.isEmpty())return;while(batch.size()<8&&!queue.isEmpty()){String s=queue.remove();batch.add(s);inflightChars+=s.length();}inflightCount=batch.size();flight=++serial;id=flight;}try{evaluator.evaluate(Collections.unmodifiableList(batch),()->consumed(id));}catch(Exception e){fail("UI_PUMP_EVALUATE_FAILURE_NO_RETRY");}}
 private synchronized void consumed(long id){if(failed||flight!=id)return;totalCount-=inflightCount;totalChars-=inflightChars;inflightCount=inflightChars=0;flight=0;schedule();}
 private void fail(String reason){synchronized(this){if(failed)return;failed=true;queue.clear();}failure.accept(reason);}
 public synchronized boolean failed(){return failed;}public synchronized int outstanding(){return totalCount;}
}
