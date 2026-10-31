package vn.rtr.aeris.operator01;
import android.os.SystemClock;import org.json.*;import java.io.*;import java.util.*;
/** Typed payload facade. No socket, reader, heartbeat producer or independent journal. */
public final class PayloadNative97{
 private final DirectTransport95 transport;public PayloadNative97(DirectTransport95 t){transport=t;}
 public boolean isOpen(){try{return new JSONObject(transport.payloadState()).optBoolean("open");}catch(Exception e){return false;}}
 private long integer(JSONObject q,String k)throws Exception{Object v=q.get(k);if(!(v instanceof Number))throw new IOException("INTEGER_TYPE");double d=((Number)v).doubleValue();long n=((Number)v).longValue();if(!Double.isFinite(d)||d!=n||n<0||n>9007199254740991L)throw new IOException("INTEGER_RANGE");return n;}
 private float number(JSONObject q,String k)throws Exception{Object v=q.get(k);if(!(v instanceof Number)||!Double.isFinite(((Number)v).doubleValue()))throw new IOException("NUMBER_TYPE");float n=((Number)v).floatValue();if(!Float.isFinite(n))throw new IOException("NUMBER_RANGE");return n;}
 private void exact(JSONObject q,String...keys)throws Exception{Set<String>a=new HashSet<>();Iterator<String>it=q.keys();while(it.hasNext())a.add(it.next());if(!a.equals(new HashSet<>(Arrays.asList(keys))))throw new IOException("PAYLOAD_REQUEST_SHAPE");}
 public String request(String action,String body)throws Exception{synchronized(transport){JSONObject q=new JSONObject(body);PayloadCore97 core=null;try{
  if(action.equals("state")){exact(q);return transport.payloadState();}
  if(action.equals("history")){exact(q);return transport.payloadHistory();}
  if(action.equals("close")){exact(q,"acknowledge");if(!q.getBoolean("acknowledge"))throw new IOException("EXPLICIT_CLOSE_REQUIRED");return transport.payloadDetach("EXPLICIT_PAYLOAD_DETACH_NO_RESTORE");}
  if(action.equals("open")){exact(q,"syntheticAcknowledged");if(!q.getBoolean("syntheticAcknowledged"))throw new IOException("SYNTHETIC_CONFIRMATION_REQUIRED");return transport.payloadAttach();}
  core=transport.payloadCore();long now=SystemClock.elapsedRealtime();
  if(action.equals("join")){exact(q,"actor");transport.nativeRecord98("PAYLOAD_JOIN_INTENT",q.toString());core.join(q.getString("actor"),now);}
  else if(action.equals("heartbeat")){exact(q,"sid");core.heartbeat(q.getString("sid"),now);}
  else if(action.equals("discover")){exact(q,"acknowledge");if(!q.getBoolean("acknowledge"))throw new IOException("EXPLICIT_DISCOVERY_REQUIRED");for(PayloadCore97.Tx t:core.discover(now))transport.payloadSend(t);}
  else if(action.equals("action")){exact(q,"sid","seq","revision","generation","kind","payload","to","acknowledge");if(!q.getBoolean("acknowledge"))throw new IOException("EXPLICIT_CONSENT_REQUIRED");transport.nativeRecord98("PAYLOAD_AUTHORITY_INTENT",q.toString());core.act(q.getString("sid"),integer(q,"seq"),integer(q,"revision"),q.getString("generation"),q.getString("kind"),q.getString("payload"),q.getString("to"),now);}
  else if(action.equals("command")){exact(q,"sid","seq","revision","generation","payload","operation","a","b","acknowledge");if(!q.getBoolean("acknowledge"))throw new IOException("EXPLICIT_COMMAND_CONFIRM_REQUIRED");transport.nativeRecord98("PAYLOAD_COMMAND_INTENT",q.toString());PayloadCore97.Tx t=core.command(q.getString("sid"),integer(q,"seq"),integer(q,"revision"),q.getString("generation"),q.getString("payload"),q.getString("operation"),number(q,"a"),number(q,"b"),now);transport.payloadSend(t);}
  else throw new IOException("PAYLOAD_ACTION_UNKNOWN");transport.nativeRecord98("PAYLOAD_STATE",transport.payloadState());return transport.payloadState();
 }catch(Exception e){if(transport.isOpen())try{transport.nativeRecord98("PAYLOAD_REJECTED",new JSONObject().put("action",action).put("error",String.valueOf(e.getMessage())).toString());}catch(Exception ignored){}if(core!=null&&core.isClosed())transport.close("UNIFIED_PAYLOAD_CORE_REVOKED");throw e;}}}
 public void close(String reason){synchronized(transport){try{transport.payloadDetach(reason);}catch(Exception ignored){}}}
}
