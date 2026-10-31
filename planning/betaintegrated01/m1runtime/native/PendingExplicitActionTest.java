import vn.rtr.aeris.beta01runtime.PendingExplicitAction;
public class PendingExplicitActionTest {
    static int checks;
    static void ok(boolean condition){checks++;if(!condition)throw new AssertionError("check"+checks);}
    static void rejects(Runnable action){boolean rejected=false;try{action.run();}catch(IllegalArgumentException|IllegalStateException expected){rejected=true;}ok(rejected);}
    public static void main(String[]args){
        PendingExplicitAction<String> p=new PendingExplicitAction<>(2000000000L,16);
        ok(p.consume(0,true)==null); // Ordinary resume never creates an action.
        p.enqueue("id01","CONNECT","bound-payload",10);
        ok(p.consume(20,false)==null); // onNewIntent before onResume waits.
        ok(p.snapshot().get("pending").equals(true));
        PendingExplicitAction.Ticket<String> t=p.consume(30,true);ok(t!=null&&t.id.equals("id01")&&t.action.equals("CONNECT")&&t.payload.equals("bound-payload"));
        ok(p.consume(31,true)==null);rejects(()->p.enqueue("id01","CONNECT","replay",32));
        p.enqueue("id02","CONNECT","old",40);p.enqueue("id03","CLOSE","replacement",41);
        ok(p.consume(42,true).id.equals("id03"));ok(p.snapshot().get("replaced").equals(1L));
        p.enqueue("id04","CONNECT","cancel",50);p.cancel("ACTIVITY_PAUSED");ok(p.consume(51,true)==null);
        p.enqueue("id05","CONNECT","expired",60);ok(p.consume(2000000061L,true)==null);ok(p.snapshot().get("expired").equals(1L));
        rejects(()->p.enqueue(null,"CONNECT","missing",2000000062L));rejects(()->p.enqueue("id06","UNKNOWN","unknown",2000000063L));
        p.enqueue("id07","CONNECT","clock",2000000070L);rejects(()->p.consume(2000000069L,true));ok(p.snapshot().get("failed").equals(true));rejects(()->p.consume(2000000080L,true));
        PendingExplicitAction<String> bounded=new PendingExplicitAction<>(2000000000L,16);for(int i=0;i<100;i++){bounded.enqueue("bounded-"+i,"STATUS","status",i);bounded.consume(i,true);}ok(bounded.snapshot().get("recentIds").equals(16));
        PendingExplicitAction<String> restarted=new PendingExplicitAction<>(2000000000L,16);ok(restarted.consume(1000,true)==null);
        PendingExplicitAction<String> invalid=new PendingExplicitAction<>(2000000000L,16);invalid.enqueue("valid","CONNECT","valid",0);rejects(()->invalid.enqueue(null,"CONNECT","invalid",1));ok(invalid.consume(2,true)==null);
        invalid.enqueue("new","CONNECT","new",3);rejects(()->invalid.enqueue("new","CONNECT","replay",4));ok(invalid.consume(5,true)==null);
        System.out.println("{\"status\":\"PASS\",\"checks\":"+checks+",\"scope\":\"PURE_ACTUAL_PENDING_ACTION_POLICY_NOT_ANDROID_LIFECYCLE\"}");
    }
}
