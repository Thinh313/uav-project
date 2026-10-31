package vn.rtr.aeris.mission;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.*;
import org.json.*;
import vn.rtr.aeris.beta01runtime.Values;
import vn.rtr.aeris.control01.ControlConfig;

/** Product setup only. It cannot connect, grant authority or dispatch a flight action. */
public final class MissionBootstrap {
    public static final int MAX_BYTES=32768;
    public final String nonce,processEpoch,sourceSHA256,sha256,existingDraftSHA256;
    public final long baseRevision;public final int viewEpoch;
    public final JSONObject context,provider,survey;
    public final byte[] bytes,bindingBytes;
    private MissionBootstrap(byte[] raw,JSONObject o)throws Exception{
        bytes=raw.clone();sha256=Values.hash(bytes);nonce=hex(o,"requestNonce",32);processEpoch=hex(o,"processEpoch",32);sourceSHA256=hex(o,"sourceSHA256",64);baseRevision=integer(o,"baseRevision",1,Long.MAX_VALUE);viewEpoch=(int)integer(o,"viewEpoch",1,1000000000);
        context=o.getJSONObject("context");keys(context,"run","epoch","boot","operator","generation","profileId");provider=o.getJSONObject("provider");keys(provider,"version","mode","profileId","binarySHA256","modelSHA256","configSHA256","endpoint","firmware","rootOwnedContainer","targetSystem","run","epoch","boot","operator","generation","inputProvenance");
        for(String key:Arrays.asList("run","epoch","boot","operator","generation","profileId")){String c=string(context,key);if(!c.matches("[A-Za-z0-9_.:-]{1,128}")||!c.equals(string(provider,key)))throw new IOException("BOOTSTRAP_PROVIDER_CONTEXT");}
        integer(provider,"version",1,1);integer(provider,"targetSystem",42,42);for(String key:Arrays.asList("binarySHA256","modelSHA256","configSHA256"))hex(provider,key,64);
        if(!Boolean.TRUE.equals(provider.get("rootOwnedContainer"))||!"tcp://10.0.2.2:5961".equals(string(provider,"endpoint"))||!"CANDIDATE_EXTERNAL".equals(string(provider,"mode"))||!"4.7.1".equals(string(provider,"firmware"))||!Arrays.asList("M1-COCKPIT04-NOMINAL","M1-COCKPIT04-LOSS").contains(string(provider,"profileId"))||!Arrays.asList("ROOT_INJECTED_ANDROID_TOUCH","LOCAL_ANDROID_TOUCH_NOT_HID_ATTESTED").contains(string(provider,"inputProvenance")))throw new IOException("BOOTSTRAP_SIMULATION_ONLY");
        bindingBytes=provider.toString().getBytes(StandardCharsets.UTF_8);
        survey=o.isNull("survey")?null:o.getJSONObject("survey");existingDraftSHA256=o.isNull("expectedDraftSHA256")?null:hex(o,"expectedDraftSHA256",64);
        if((survey==null)==(existingDraftSHA256==null))throw new IOException("BOOTSTRAP_SURVEY_XOR_EXISTING");
        if(survey!=null)integer(survey,"revision",0,999998);
    }
    public static MissionBootstrap parse(String raw)throws Exception{
        if(raw==null)throw new IOException("BOOTSTRAP_MISSING");byte[] bytes=raw.getBytes(StandardCharsets.UTF_8);if(bytes.length==0||bytes.length>MAX_BYTES)throw new IOException("BOOTSTRAP_BYTES");JSONObject o=new JSONObject(raw);keys(o,"version","requestNonce","processEpoch","viewEpoch","baseRevision","sourceSHA256","context","provider","survey","expectedDraftSHA256");integer(o,"version",1,1);return new MissionBootstrap(bytes,o);
    }
    public static String status(String raw)throws Exception{if(raw==null||raw.getBytes(StandardCharsets.UTF_8).length>512)throw new IOException("STATUS_BYTES");JSONObject o=new JSONObject(raw);keys(o,"version","requestNonce");integer(o,"version",1,1);return hex(o,"requestNonce",32);}
    public void validateIdentity(String actualEpoch,int actualViewEpoch,long currentRevision,String actualSource)throws IOException{if(!processEpoch.equals(actualEpoch)||viewEpoch!=actualViewEpoch||!sourceSHA256.equals(actualSource))throw new IOException("BOOTSTRAP_FOREIGN_PROCESS_OR_SOURCE");if(baseRevision!=currentRevision)throw new IOException("BOOTSTRAP_REVISION");}
    public ControlConfig config(byte[]expected,ControlConfig.Asset assets)throws Exception{return new ControlConfig(expected,bindingBytes,Values.hash(bindingBytes),assets);}
    public static long integer(JSONObject o,String k,long min,long max)throws Exception{Object v=o.get(k);if(!(v instanceof Integer||v instanceof Long))throw new IOException("INTEGER_TYPE:"+k);long n=((Number)v).longValue();if(n<min||n>max)throw new IOException("INTEGER_BOUND:"+k);return n;}
    public static String hex(JSONObject o,String key,int len)throws Exception{Object v=o.get(key);if(!(v instanceof String)||!((String)v).matches("[a-f0-9]{"+len+"}"))throw new IOException("HEX:"+key);return(String)v;}
    public static String string(JSONObject o,String key)throws Exception{Object v=o.get(key);if(!(v instanceof String))throw new IOException("STRING_TYPE:"+key);return(String)v;}
    public static void keys(JSONObject o,String...names)throws Exception{Set<String> expected=new HashSet<>(Arrays.asList(names));if(o.length()!=expected.size())throw new IOException("SCHEMA_FIELD_COUNT");Iterator<String> it=o.keys();while(it.hasNext())if(!expected.contains(it.next()))throw new IOException("SCHEMA_UNKNOWN_FIELD");}
    /** Setup-only transport fence. Original receipt is never refreshed by duplicate delivery. */
    public static final class Dispatch{public final String action,raw,nonce;public final long receivedNs,queuedNs;private Dispatch(String a,String r,String n,long received,long queued){action=a;raw=r;nonce=n;receivedNs=received;queuedNs=queued;}}
    public static final class IntentQueue{
        private final LinkedHashMap<String,Dispatch> recent=new LinkedHashMap<>();private Dispatch pending;private long last=-1;private boolean failed;
        private void time(long now)throws IOException{if(failed||now<0||now<last){failed=true;pending=null;throw new IOException("MISSION_DISPATCH_CLOCK");}last=now;}
        public synchronized void enqueue(String action,String raw,long now)throws Exception{time(now);if(!Arrays.asList("STATUS","BOOTSTRAP").contains(action))throw new IOException("MISSION_DISPATCH_ACTION");String nonce=action.equals("STATUS")?status(raw):parse(raw).nonce;Dispatch old=recent.get(nonce);if(old!=null&&(!old.action.equals(action)||!old.raw.equals(raw)))throw new IOException("MISSION_NONCE_CONFLICT");if(old!=null&&now-old.receivedNs>10000000000L)throw new IOException("MISSION_REPLAY_EXPIRED");if(pending!=null&&!pending.nonce.equals(nonce))throw new IOException("MISSION_PENDING_CAPACITY");Dispatch d=new Dispatch(action,raw,nonce,old==null?now:old.receivedNs,old==null?now:old.queuedNs);pending=d;recent.put(nonce,d);while(recent.size()>16)recent.remove(recent.keySet().iterator().next());}
        public synchronized Dispatch consume(long now,boolean foreground)throws IOException{time(now);if(pending==null)return null;if(now-pending.queuedNs>2000000000L||now-pending.receivedNs>10000000000L){pending=null;throw new IOException("MISSION_DISPATCH_EXPIRED");}if(!foreground)return null;Dispatch d=pending;pending=null;return d;}
        public synchronized void cancel(String reason){pending=null;}
    }
}
