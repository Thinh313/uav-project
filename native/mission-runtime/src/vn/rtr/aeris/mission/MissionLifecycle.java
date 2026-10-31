package vn.rtr.aeris.mission;

import java.io.IOException;
import org.json.*;

/** Derived presentation state, never an authority/lease owner. */
public final class MissionLifecycle {
    private String nonce,descriptorSHA,sourceSHA;private JSONObject context;private String failure;
    public synchronized boolean duplicate(MissionBootstrap b)throws IOException{if(nonce==null||!nonce.equals(b.nonce))return false;if(!descriptorSHA.equals(b.sha256))throw new IOException("BOOTSTRAP_NONCE_CONFLICT");return true;}
    public synchronized void stage(MissionBootstrap b)throws IOException{if(failure!=null)throw new IOException("MISSION_FAILED");if(context!=null&&!same(context,b.context,"run","epoch","boot","operator","generation","profileId"))throw new IOException("GENERATION_ALREADY_STAGED_RESTART_REQUIRED");nonce=b.nonce;descriptorSHA=b.sha256;sourceSHA=b.sourceSHA256;try{context=new JSONObject(b.context.toString());}catch(Exception e){throw new IOException(e);}}
    public synchronized JSONObject context()throws Exception{return context==null?null:new JSONObject(context.toString());}
    public synchronized String descriptorSHA(){return descriptorSHA;}
    public synchronized boolean healthy(){return failure==null;}
    public synchronized void fail(String reason){if(failure==null)failure=reason;}
    public synchronized JSONObject derive(JSONObject nativeState,JSONObject checkpoint,boolean ownerActive,boolean rendered,boolean foreground,boolean stopped)throws Exception{
        JSONObject journal=nativeState.optJSONObject("journal"),life=nativeState.optJSONObject("lifecycle"),input=nativeState.optJSONObject("input");
        boolean sealed=context!=null&&!ownerActive&&same(context,nativeState,"run","epoch","boot","generation")&&nativeState.optBoolean("closed")&&journal!=null&&same(context,journal,"run","epoch")&&journal.optBoolean("closed")&&!journal.optBoolean("failed")&&journal.optString("commitAnchor").matches("[a-f0-9]{64}")&&life!=null&&same(context,life,"run","generation")&&life.optLong("resourcesClosedNs",-1)>=0&&input!=null&&Boolean.FALSE.equals(input.opt("consent"))&&input.has("leaseId")&&input.isNull("leaseId")&&!nativeState.optBoolean("rcOverrideActiveLocally");
        JSONObject cpContext=checkpoint.optJSONObject("context");String phase="STARTING";boolean terminal=sealed&&cpContext!=null&&same(context,cpContext,"run","epoch","boot","operator","generation","profileId")&&sourceSHA.equals(checkpoint.optString("APKSourceSHA256"))&&journal.getString("commitAnchor").equals(checkpoint.optString("terminalAnchor"))&&"COMMITTED".equals(checkpoint.optString("phase"))&&checkpoint.optLong("ackElapsedNs",-1)>=0;
        if(failure!=null||"FAILED".equals(checkpoint.optString("phase"))||"REVIEW_FAILED".equals(checkpoint.optString("phase")))phase="FAILED";
        else if(terminal&&"DURABLE".equals(checkpoint.optString("reviewStatus")))phase="REVIEW_READY";
        else if(terminal)phase="TERMINAL_DURABLE";
        else if(sealed)phase="NATIVE_SEALED";
        else if(ownerActive)phase=nativeState.optString("firstFailure","").isEmpty()||nativeState.isNull("firstFailure")?"CONNECTED":"CLOSING";
        else if(stopped)phase="STOPPED";
        else if(context!=null&&rendered&&foreground&&("READY".equals(checkpoint.optString("phase"))||"RECOVERED_NOT_LIVE_ACK".equals(checkpoint.optString("phase"))))phase="READY";
        return new JSONObject().put("phase",phase).put("failure",failure==null?JSONObject.NULL:failure).put("authorityRestorable",false).put("completionClaim",false);
    }
    private static boolean same(JSONObject a,JSONObject b,String...keys){try{for(String key:keys)if(!MissionBootstrap.string(a,key).equals(MissionBootstrap.string(b,key)))return false;return true;}catch(Exception e){return false;}}
}
