package vn.rtr.aeris.phone06;
import java.util.*;
/** Proposed simulation test configuration. Actual AP values/types must be observed before use. */
public final class ManualProfile06{
 public static final Map<String,double[]>P=new LinkedHashMap<>();static{
 P.put("ARMING_RUDDER",new double[]{2,0,0});P.put("RC_OVERRIDE_TIME",new double[]{9,.19999,.20001});P.put("RC_FS_TIMEOUT",new double[]{9,1,1});P.put("FS_THR_ENABLE",new double[]{2,1,1});P.put("RC_OPTIONS",new double[]{6,0,0});P.put("FLTMODE_CH",new double[]{2,0,0});
 String[]names={"ROLL","PITCH","THROTTLE","YAW"};for(int i=0;i<4;i++){P.put("RCMAP_"+names[i],new double[]{2,i+1,i+1});String c="RC"+(i+1)+"_";P.put(c+"MIN",new double[]{4,1100,1100});P.put(c+"MAX",new double[]{4,1900,1900});P.put(c+"TRIM",new double[]{4,1500,1500});P.put(c+"REVERSED",new double[]{2,0,0});}}
}
