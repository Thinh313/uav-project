package vn.rtr.aeris.native96;
import java.util.*;
/** Pure mock-input preparation. No transport and no aircraft control output. */
public final class InputModel {
 public static final long MAX_AGE_MS=250; // Fixture policy, not a measured controller budget.
 public static final class Calibration {
  public final String revision,device; public final double min,center,max,deadzone; public final boolean inverted;
  public Calibration(String revision,String device,double min,double center,double max,double deadzone,boolean inverted){
   if(revision==null||revision.length()>64||revision.isEmpty()||device==null||!device.startsWith("mock:")||device.length()>64||!finite(min)||!finite(center)||!finite(max)||!finite(deadzone)||min>=center||center>=max||deadzone<0||deadzone>=1)throw new IllegalArgumentException("Invalid synthetic calibration");
   this.revision=revision;this.device=device;this.min=min;this.center=center;this.max=max;this.deadzone=deadzone;this.inverted=inverted;
  }
  public double normalize(double raw){if(!finite(raw)||raw<min||raw>max)throw new IllegalArgumentException("Axis out of calibrated range");double n=raw>=center?(raw-center)/(max-center):(raw-center)/(center-min);double a=Math.abs(n);double v=a<=deadzone?0:Math.copySign((a-deadzone)/(1-deadzone),n);return inverted?-v:v;}
 }
 public final String session;private Calibration calibration;private boolean focused=false,attached=false,deadman=false,owned=false;private int neutral=0;private long lastClock=-1,lastSample=-1;private Double axis=null;private String reason="NO_INPUT";private final ArrayDeque<String> history=new ArrayDeque<>();private long dropped=0;
 public InputModel(String session){if(session==null||session.isEmpty()||session.length()>64)throw new IllegalArgumentException("Session");this.session=session;}
 private static boolean finite(double v){return !Double.isNaN(v)&&!Double.isInfinite(v);}
 private void clock(long t){if(t<0||t<lastClock){revoke("CLOCK_REGRESSION");throw new IllegalArgumentException("Monotonic clock required");}lastClock=t;if(lastSample>=0&&t-lastSample>MAX_AGE_MS){revoke("STALE_INPUT");lastSample=-1;}}
 private void log(String s){if(history.size()==128){history.removeFirst();dropped++;}history.addLast(s);}
 private void revoke(String why){owned=false;deadman=false;neutral=0;axis=null;reason=why;log(why);}
 public void focus(boolean active,long t){clock(t);focused=active;if(!active)revoke("FOCUS_LOST");}
 public void attach(Calibration c,long t){clock(t);if(c==null)throw new IllegalArgumentException("Calibration");revoke("REDISCOVERED");calibration=c;attached=true;lastSample=-1;}
 public void detach(long t){clock(t);attached=false;revoke("DEVICE_LOST");lastSample=-1;}
 public boolean sample(String session,String device,double raw,long t){clock(t);if(!this.session.equals(session)||calibration==null||!calibration.device.equals(device)||!focused||!attached){log("FOREIGN_OR_UNAVAILABLE_SAMPLE");return false;}if(lastSample>=0&&t-lastSample<50){log("RATE_LIMITED");return false;}double value;try{value=calibration.normalize(raw);}catch(IllegalArgumentException e){revoke("INVALID_AXIS");throw e;}lastSample=t;axis=value;neutral=value==0?Math.min(3,neutral+1):0;reason=owned?"MOCK_GIMBAL_OWNER":"OBSERVED_MOCK_AXIS";log(reason);return true;}
 public void hold(boolean held,long t){clock(t);if(!focused||!attached){revoke("UNAVAILABLE_DEADMAN");return;}deadman=held;if(!held)revoke("DEADMAN_RELEASED");}
 public boolean acquire(long t){clock(t);if(!focused||!attached||!deadman||neutral<3||lastSample<0||t-lastSample>MAX_AGE_MS){log("ACQUIRE_REFUSED");return false;}owned=true;reason="MOCK_GIMBAL_OWNER";log(reason);return true;}
 public void tick(long t){clock(t);}
 public boolean owned(){return owned;} public Double axis(){return axis;}public String reason(){return reason;}public int neutral(){return neutral;} public long dropped(){return dropped;}public int historySize(){return history.size();}
 public String json(){return "{\"session\":"+Json.quote(session)+",\"calibrationRevision\":"+(calibration==null?"null":Json.quote(calibration.revision))+",\"device\":"+(calibration==null?"null":Json.quote(calibration.device))+",\"state\":"+Json.quote(reason)+",\"axis\":"+(axis==null?"null":axis.toString())+",\"neutralSamples\":"+neutral+",\"mockOwned\":"+owned+",\"historySize\":"+history.size()+",\"dropped\":"+dropped+",\"operational\":false,\"physicalMappingVerified\":false}";}
}
