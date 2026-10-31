package vn.rtr.aeris.operator01;
import java.io.*;import java.lang.reflect.*;import java.nio.*;import java.util.*;
/** Controlled transition-only fixture: does not bypass production guard in the app. */
public final class AutoTransition01Test {
 static int checks;static void ok(boolean b,String n){if(!b)throw new AssertionError(n);checks++;}
 static void field(Object o,String name,Object v)throws Exception{Field f=o.getClass().getDeclaredField(name);f.setAccessible(true);f.set(o,v);}
 static Object get(Object o,String name)throws Exception{Field f=o.getClass().getDeclaredField(name);f.setAccessible(true);return f.get(o);}
 static WireGate95 fresh()throws Exception{
  WireGate95 g=new WireGate95(new byte[0][]);field(g,"started",true);field(g,"last",1000L);field(g,"hb",1000L);field(g,"armed",true);field(g,"mode",4);field(g,"grantUntil",5000L);field(g,"cycles",2);field(g,"homeRaw",new long[]{0,0,0});field(g,"homeAt",1000L);
  byte[]p=autoPayload();g.transmit(frame(76,p,1),1000);return g;
 }
 static byte[]autoPayload(){byte[]p=new byte[33];ByteBuffer b=ByteBuffer.wrap(p).order(ByteOrder.LITTLE_ENDIAN);b.putFloat(0,1);b.putFloat(4,3);b.putShort(28,(short)176);p[30]=42;p[31]=1;return p;
 }
 static byte[]frame(int id,byte[]p,int seq){byte[]f=new byte[12+p.length];f[0]=(byte)253;f[1]=(byte)p.length;f[4]=(byte)seq;f[5]=(byte)(id==76?255:42);f[6]=(byte)(id==76?190:1);f[7]=(byte)id;f[8]=(byte)(id>>8);f[9]=(byte)(id>>16);System.arraycopy(p,0,f,10,p.length);int c=65535;for(int i=1;i<10+p.length+1;i++){int value=i==10+p.length?Dialect95.D.get(id)[2]:f[i]&255,t=value^(c&255);t^=(t<<4)&255;c=((c>>8)^(t<<8)^(t<<3)^(t>>4))&65535;}f[f.length-2]=(byte)c;f[f.length-1]=(byte)(c>>8);return f;}
 static byte[]hb(int mode,boolean armed,int seq){byte[]p=new byte[9];ByteBuffer.wrap(p).order(ByteOrder.LITTLE_ENDIAN).putInt(mode);p[4]=2;p[5]=3;p[6]=(byte)(armed?128:0);p[7]=4;p[8]=3;return frame(0,p,seq);}
 interface Act{void run()throws Exception;}static void reject(String reason,Act a)throws Exception{try{a.run();throw new AssertionError("accepted "+reason);}catch(IOException e){ok(e.getMessage().equals(reason),"reason "+e.getMessage());}}
 public static void main(String[]a)throws Exception{
  if(a.length>0){WireGate95 actual=fresh();byte[] hb=DirectTransport95.unhex(new String(java.nio.file.Files.readAllBytes(java.nio.file.Paths.get(a[0])),"US-ASCII").trim());if(a.length>1){reject("NATIVE_MODE_DEVIATION",()->actual.receive(hb,1013));System.out.println("{\"status\":\"REPRODUCED_OLD_FAILURE\",\"deltaFromRecordedTxWrittenMs\":13}");return;}actual.receive(hb,1013);ok(!Boolean.TRUE.equals(get(actual,"autoObserved01")),"actual recorded 13ms GUIDED pending allowed, not observed");}

  WireGate95 race=fresh();race.receive(hb(4,true,2),1013);ok(!Boolean.TRUE.equals(get(race,"autoObserved01")),"13ms pretransition GUIDED not observation");race.receive(hb(3,true,3),1400);ok(Boolean.TRUE.equals(get(race,"autoObserved01")),"AUTO observation locks state");reject("NATIVE_MODE_DEVIATION",()->race.receive(hb(4,true,4),1500));
  WireGate95 repeat=fresh();reject("NATIVE_AUTO_ALREADY_REQUESTED",()->repeat.transmit(frame(76,autoPayload(),2),1100));ok(((Long)get(repeat,"autoRequestedAt01"))==1000L,"repeat cannot extend deadline");
  WireGate95 timeout=fresh();timeout.tick(2500);reject("NATIVE_AUTO_TRANSITION_TIMEOUT",()->timeout.tick(2501));
  WireGate95 other=fresh();reject("NATIVE_MODE_DEVIATION",()->other.receive(hb(5,true,2),1013));
  WireGate95 disarm=fresh();reject("NATIVE_MODE_DEVIATION",()->disarm.receive(hb(4,false,2),1013));
  WireGate95 fakeAuto=fresh();reject("NATIVE_MODE_DEVIATION",()->fakeAuto.receive(hb(3,false,2),1013));
  WireGate95 clock=fresh();reject("NATIVE_CLOCK_REGRESSION",()->clock.tick(999));
  WireGate95 ack=fresh();byte[]p=new byte[10];ByteBuffer.wrap(p).order(ByteOrder.LITTLE_ENDIAN).putShort((short)176);ack.receive(frame(77,p,2),1013);ok(!Boolean.TRUE.equals(get(ack,"autoObserved01")),"ACK cannot promote");reject("NATIVE_AUTO_TRANSITION_TIMEOUT",()->ack.tick(2501));
  WireGate95 boundary=fresh();boundary.receive(hb(3,true,2),2500);ok(Boolean.TRUE.equals(get(boundary,"autoObserved01")),"AUTO exactly deadline permitted");boundary.receive(hb(0,false,3),2600);ok(!Boolean.TRUE.equals(get(boundary,"broken")),"observed final disarm preserves old behavior");
  WireGate95 late=fresh();reject("NATIVE_AUTO_TRANSITION_TIMEOUT",()->late.receive(hb(3,true,2),2501));
  WireGate95 incomplete=fresh();field(incomplete,"takeoff",true);field(incomplete,"terminal",true);field(incomplete,"armed",false);field(incomplete,"landed",1);field(incomplete,"land",1000L);field(incomplete,"position",1000L);field(incomplete,"lastLat",0d);field(incomplete,"lastLon",0d);ok(!incomplete.safeComplete(1100),"completion requires observed");
  System.out.println("{\"status\":\"PASS\",\"checks\":"+checks+",\"provenance\":\"CONTROLLED_NATIVE_TRANSITION_ONLY\"}");
 }
}
