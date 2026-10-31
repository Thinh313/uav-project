package vn.rtr.aeris.betaworkbench03;
public final class OperationGateTest {
 static void need(boolean x){if(!x)throw new AssertionError();}
 public static void main(String[] args){OperationGate g=new OperationGate();need(!g.busy());
  g.begin("session1:request1");need(g.busy());need(!g.finish("session2:request1")&&g.busy());need(!g.finish("session1:request2")&&g.busy());
  try{g.begin("session1:request2");throw new AssertionError();}catch(IllegalStateException expected){}need(g.busy());
  need(g.finish("session1:request1")&&!g.busy());need(!g.finish("session1:request1"));
  g.begin("session2:request1");need(!g.finish("session1:request1")&&g.busy());need(g.finish("session2:request1")&&!g.busy());
  try{g.begin(null);throw new AssertionError();}catch(IllegalArgumentException expected){}need(!g.busy());
  for(String terminal:new String[]{"success","io-error","readback-mismatch","cancel","session-changed"}){g.begin("owned:"+terminal);need(g.finish("owned:"+terminal)&&!g.busy());}
  System.out.println("PASS owner correlation, busy-no-queue, stale-session, duplicates, invalid key, five terminal releases; host model not SAF runtime");
 }
}
