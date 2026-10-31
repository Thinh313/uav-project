package vn.rtr.aeris.native94;
/** Render callback watchdog only. A producer timestamp is never a camera/host clock mapping. */
public final class VideoWatch89 {
 public static final long STALE_MS=500,FIRST_FRAME_MS=2000;public long generation=0,frames=0,rejected=0;public String state="EMPTY";private long clock=-1,started=-1,last=-1,producer=-1;
 private void time(long t){if(t<0||t<clock){stop("CLOCK_INVALID");throw new IllegalArgumentException("Monotonic callback clock");}clock=t;}
 public long prepare(long t){time(t);generation++;frames=rejected=0;last=producer=-1;started=t;state="PREPARING";return generation;}
 public boolean prepared(long g,int w,int h,long duration,long t){time(t);if(g!=generation||!state.equals("PREPARING"))return false;if(w!=640||h!=360||duration<=0||duration>10000){stop("METADATA_REFUSED");return false;}state="PREPARED";return true;}
 public boolean start(long g,long t){time(t);if(g!=generation||!state.equals("PREPARED"))return false;started=t;state="WAITING_RENDER_CALLBACK";return true;}
 public boolean frame(long g,long pts,long t){time(t);tick(t);if(g!=generation||!(state.equals("WAITING_RENDER_CALLBACK")||state.equals("RENDER_CALLBACK_OBSERVED"))||pts<0||pts<=producer){rejected++;return false;}producer=pts;last=t;frames++;state="RENDER_CALLBACK_OBSERVED";return true;}
 public boolean end(long g,long t){time(t);if(g!=generation||!playing())return false;state=frames>0?"ENDED_WITH_CALLBACKS":"ENDED_NO_CALLBACK_PROOF";return frames>0;}
 public boolean playing(){return state.equals("WAITING_RENDER_CALLBACK")||state.equals("RENDER_CALLBACK_OBSERVED");}
 public void tick(long t){time(t);if(state.equals("PREPARING")&&t-started>FIRST_FRAME_MS){stop("PREPARE_TIMEOUT");return;}if(playing()&&((last<0&&t-started>FIRST_FRAME_MS)||(last>=0&&t-last>STALE_MS)))stop("STALLED_NO_AUTO_RESUME");}
 public void stop(String reason){generation++;state=reason;}
 public Long callbackAge(long t){time(t);return last<0?null:Math.max(0,t-last);}
 public String json(long t){tick(t);return peekJson(t);}
 public String peekJson(long t){Long age=callbackAge(t);return "{\"generation\":"+generation+",\"state\":"+Json.quote(state)+",\"frameCallbacks\":"+frames+",\"rejectedCallbacks\":"+rejected+",\"callbackAgeMs\":"+age+",\"producerTimestampNs\":"+(producer<0?"null":String.valueOf(producer))+",\"cameraAgeMs\":null,\"cameraToDisplayLatencyMs\":null,\"displayScanoutMeasured\":false,\"source\":\"SYNTHETIC_FIXTURE\",\"actualImages\":0}";}
}
