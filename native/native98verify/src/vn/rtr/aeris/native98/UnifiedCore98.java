package vn.rtr.aeris.native98;
import java.io.*;import java.util.*;
/** Pure shared session policy. All caller operations are serialized by the sole native transport. */
public final class UnifiedCore98{
 public final WireGate95 flight;public final PayloadCore97 payload;public final String generation;private boolean closed=false,attached=false,used=false,detached=false;private int sequence=0;
 public UnifiedCore98(byte[][]items,String gen){generation=gen;flight=new WireGate95(items);payload=new PayloadCore97(gen,()->flight.payloadArmedAllowed98());}
 private void current()throws IOException{if(closed)throw new IOException("UNIFIED_CLOSED_NO_RESTORE");}
 public void attach(long now)throws IOException{current();if(used)throw new IOException("PAYLOAD_ATTACH_ONCE_NO_RESTORE");payload.tick(now);used=true;attached=true;}
 public boolean attached(){return attached&&!closed;}
 public void requirePayload()throws IOException{current();if(!attached)throw new IOException("EXPLICIT_PAYLOAD_ATTACH_REQUIRED");}
 public void detach(String reason){if(!used)return;attached=false;detached=true;payload.close(reason);}
 public void receive(byte[]b,long now)throws IOException{current();try{flight.receive(b,now);if(!detached)payload.receive(b,now);}catch(IOException|RuntimeException e){close("RX_"+e.getMessage());throw e;}}
 public void tick(long now)throws IOException{current();try{flight.tick(now);if(!detached)payload.tick(now);}catch(IOException|RuntimeException e){close("CLOCK_OR_STALE_"+e.getMessage());throw e;}}
 public void flightApprove(byte[]b,long now)throws IOException{current();try{flight.transmit(b,now);}catch(IOException|RuntimeException e){close("FLIGHT_POLICY_"+e.getMessage());throw e;}}
 public Map<String,Object>payloadApprove(PayloadCore97.Tx t,long now)throws IOException{requirePayload();flight.tick(now);return payload.approve(t.id,t.bytes,now);}
 public byte[] wire(byte[]raw)throws IOException{current();if(raw==null||raw.length<13||PayloadCore97.u8(raw,0)!=253||PayloadCore97.u8(raw,2)!=0||PayloadCore97.u8(raw,3)!=0||PayloadCore97.u8(raw,5)!=255||PayloadCore97.u8(raw,6)!=190)throw new IOException("UNIFIED_UNSIGNED_GCS_HEADER");int len=PayloadCore97.u8(raw,1),id=PayloadCore97.u8(raw,7)|PayloadCore97.u8(raw,8)<<8|PayloadCore97.u8(raw,9)<<16;int[]d=Dialect95.D.get(id);if(d==null||len<1||len>d[1]||raw.length!=len+12||PayloadCore97.crc(raw,1,10+len,d[2])!=PayloadCore97.u16(raw,10+len))throw new IOException("UNIFIED_FRAME_CRC_LENGTH");byte[]b=raw.clone();b[4]=(byte)(sequence++%256);int c=PayloadCore97.crc(b,1,10+len,d[2]);b[10+len]=(byte)c;b[11+len]=(byte)(c>>8);return b;}
 public void close(String reason){if(closed)return;closed=true;attached=false;flight.revoke(reason);payload.close(reason);}
 public boolean closed(){return closed;}
 public Map<String,Object>payloadState(long now){Map<String,Object>m=payload.snapshot(now);m.put("open",attached());m.put("unifiedTransport",true);m.put("transportGeneration",generation);m.put("aircraftControlMapped",false);return m;}
}
