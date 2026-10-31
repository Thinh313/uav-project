package vn.rtr.aeris.shell24;
/** Player generation/state ledger. Render-start event is not continuous frame freshness. */
public final class VideoModel {
 public static final long MAX_BYTES=64L*1024*1024,MAX_DURATION_MS=120000;
 public long generation=0;private long clock=-1;public String state="EMPTY",origin="NONE",sha=null;public boolean selected=false;public int width=0,height=0;public long bytes=0,duration=0;
 private void time(long t){if(t<0||t<clock){stop("CLOCK_REGRESSION");throw new IllegalArgumentException("Monotonic video time");}clock=t;}
 public long select(String origin,String sha,long bytes,long t){time(t);if(!("SYNTHETIC_FIXTURE".equals(origin)||"IMPORTED_LOCAL_UNATTESTED".equals(origin))||sha==null||!sha.matches("[a-f0-9]{64}")||bytes<=0||bytes>MAX_BYTES)throw new IllegalArgumentException("Local video descriptor refused");generation++;this.origin=origin;this.sha=sha;this.bytes=bytes;selected=true;width=height=0;duration=0;state="SELECTED_NOT_PLAYING";return generation;}
 public long prepare(long t){time(t);if(!selected)throw new IllegalStateException("No local video");generation++;state="PREPARING";return generation;}
 public boolean prepared(long g,int w,int h,long d,long t){time(t);if(g!=generation||!state.equals("PREPARING"))return false;if(w<=0||h<=0||w>1920||h>1080||d<=0||d>MAX_DURATION_MS){stop("UNSUPPORTED_LOCAL_VIDEO");return false;}width=w;height=h;duration=d;state="PREPARED";return true;}
 public boolean play(long g,long t){time(t);if(g!=generation||!state.equals("PREPARED"))return false;state="PLAYING_FRAME_AGE_UNKNOWN";return true;}
 public boolean rendered(long g,long t){time(t);if(g!=generation||!state.startsWith("PLAYING"))return false;state="PLAYING_RENDER_START_OBSERVED";return true;}
 public boolean ended(long g,long t){time(t);if(g!=generation||!state.startsWith("PLAYING"))return false;state="ENDED";return true;}
 public void stop(String reason){generation++;state=reason;}
 public String json(){return "{\"generation\":"+generation+",\"state\":"+Json.quote(state)+",\"origin\":"+Json.quote(origin)+",\"sha256\":"+Json.quote(sha)+",\"bytes\":"+bytes+",\"width\":"+width+",\"height\":"+height+",\"durationMs\":"+duration+",\"frameAgeMs\":null,\"cameraToDisplayLatencyMs\":null,\"physicalMediaVerified\":false,\"thermalRadiometryVerified\":false}";}
}
