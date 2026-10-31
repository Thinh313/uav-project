package vn.rtr.aeris.control01;
import java.io.*;
import java.util.*;
import java.nio.charset.StandardCharsets;
import vn.rtr.aeris.beta01runtime.*;
import vn.rtr.aeris.native98.Dialect95;

/** Versioned4.7.1 no-bypass preflight and observed post-arm Home state. */
public final class ControlFlight {
    public interface Sink {void append(String kind,Map<String,Object> event)throws Exception;}
    private final Map<String,int[]> specs;private final Map<String,long[]> parameters=new LinkedHashMap<>(),sealed=new LinkedHashMap<>();
    private final Sink sink;private int previousSequence=-1,mode=-1,landed=-1,fix,satellites,hdop=65535,voltage=65535,ekfFlags;
    private long last=-1,hb=-1,position=-1,homeAt=-1,landAt=-1,gpsAt=-1,batteryAt=-1,ekfAt=-1,boot=-1,armAt=-1,hoverStart=-1,hoverLast=-1;
    private long sensorHealth,sensorEnabled,sensorPresent;private boolean firmware,armed,failed,homeConfirmed,armIntent;private long armIntentAt=-1;private String failure;
    private int groundObservations;private double relativeAltitude,altitudeMSL,lat,lon,horizontalSpeed,verticalSpeed;
    private long[] homeRaw,preArmHome;private String homeHash,confirmedHomeHash;
    public ControlFlight(Map<String,int[]> specs,Sink sink){if(specs==null||specs.size()<20||specs.size()>64||sink==null)throw new IllegalArgumentException("CONTROL_FLIGHT_PROFILE");this.specs=new LinkedHashMap<>();for(Map.Entry<String,int[]>e:specs.entrySet()){if(!e.getKey().matches("[A-Z0-9_]{1,16}")||e.getValue()==null||e.getValue().length!=2||e.getValue()[0]<1||e.getValue()[0]>10||!Float.isFinite(Float.intBitsToFloat(e.getValue()[1])))throw new IllegalArgumentException("PARAM_SPEC");this.specs.put(e.getKey(),e.getValue().clone());}this.sink=sink;}
    private void event(String kind,Map<String,Object> data)throws Exception{try{sink.append(kind,data);}catch(Exception e){failed=true;if(failure==null)failure="FLIGHT_JOURNAL_FAILED";throw e;}}
    private void fail(String reason)throws Exception{failed=true;failure=reason;event("FLIGHT_PROFILE_REVOKED",Values.map("reason",reason,"atMs",last,"authorityRestorable",false));throw new IOException(reason);}
    public void tick(long now)throws Exception{if(failed)throw new IOException(failure);if(now<0||now<last)fail("FLIGHT_CLOCK_REGRESSION");last=now;if(hb>=0&&now-hb>3000)fail("CONTROL_HEARTBEAT_LOST");}
    public void frame(int id,int sys,int comp,int sequence,byte[]p,long now)throws Exception{
        tick(now);int[]shape=Dialect95.D.get(id);if(shape==null||p==null||p.length!=shape[1]||sequence<0||sequence>255||sys<0||sys>255||comp<0||comp>255)fail("FLIGHT_FRAME_SHAPE");if(sys!=42||comp!=1)return;int delta=previousSequence<0?1:(sequence-previousSequence+256)%256;if(delta==128)fail("AP_SEQUENCE_AMBIGUOUS");if(delta==0||delta>128)return;previousSequence=sequence;
        if(id==0){if(Mavlink.u8(p,4)!=2||Mavlink.u8(p,5)!=3)fail("AP_IDENTITY_TYPE");boolean next=(p[6]&128)!=0;if(next&&!armed){if(!armIntent||armIntentAt<0||now-armIntentAt>5000)fail("UNREQUESTED_ARM_OBSERVED");armIntent=false;armAt=now;preArmHome=homeRaw==null?null:homeRaw.clone();homeConfirmed=false;confirmedHomeHash=null;groundObservations=0;event("POST_ARM_HOME_CONFIRMATION_REQUIRED",Values.map("atMs",now,"preArmHome",homeFields(preArmHome),"aircraftSafe",false));}if(armed&&!next)event("DISARM_OBSERVED",Values.map("atMs",now));armed=next;mode=(int)Mavlink.u32(p,0);if(mode!=4&&mode!=5&&mode!=17){hoverStart=-1;hoverLast=-1;}hb=now;if(!armed&&landed==1&&position>=0&&landAt>=0&&now-position<=500&&now-landAt<=500&&Math.abs(relativeAltitude)<=.4)groundObservations++;else groundObservations=0;}
        if(id==148){int v=Dialect95.at(id,"flight_custom_version");if(Mavlink.u32(p,Dialect95.at(id,"flight_sw_version"))!=67568127L||!new String(Arrays.copyOfRange(p,v,v+8),StandardCharsets.US_ASCII).equals("dbe79216"))fail("CONTROL_FIRMWARE_MISMATCH");firmware=true;}
        if(id==22){int end=8;while(end<24&&p[end]!=0)end++;String name=new String(p,8,end-8,StandardCharsets.US_ASCII);if(specs.containsKey(name)){int type=Mavlink.u8(p,24),bits=Mavlink.i32(p,0);float value=Float.intBitsToFloat(bits);if(!Float.isFinite(value))fail("NONFINITE_PARAM");long[]old=sealed.get(name);if(old!=null&&(old[0]!=type||old[1]!=bits))fail("CONTROL_PARAMETER_CHANGED:"+name);parameters.put(name,new long[]{type,bits,now});}}
        if(id==242){long[]next={Mavlink.i32(p,0),Mavlink.i32(p,4),Mavlink.i32(p,8)};if(Math.abs(next[0])>900000000L||Math.abs(next[1])>1800000000L||next[0]==0&&next[1]==0||Math.abs(next[2])>10000000L)fail("HOME_DOMAIN_UNKNOWN");String hash=Values.hash(Values.bytes(homeFields(next)));if(homeConfirmed&&!hash.equals(confirmedHomeHash))fail("HOME_CHANGED_AFTER_CONFIRMATION");if(homeHash==null||!hash.equals(homeHash))event("HOME_RAW_OBSERVED",Values.map("atMs",now,"home",homeFields(next),"homeHash",hash,"postArm",armed));homeRaw=next;homeHash=hash;homeAt=now;}
        if(id==245){landed=Mavlink.u8(p,1);landAt=now;}
        if(id==1){sensorPresent=Mavlink.u32(p,0);sensorEnabled=Mavlink.u32(p,4);sensorHealth=Mavlink.u32(p,8);voltage=Mavlink.u16(p,14);batteryAt=now;}
        if(id==24){fix=Mavlink.u8(p,28);satellites=Mavlink.u8(p,29);hdop=Mavlink.u16(p,20);gpsAt=now;}
        if(id==193){ekfFlags=Mavlink.u16(p,Dialect95.at(193,"flags"));ekfAt=now;}
        if(id==33){long next=Mavlink.u32(p,0);if(boot>=0&&(next-boot+4294967296L)%4294967296L>=2147483648L)fail("AP_REBOOT_TIME_REGRESSION");boot=next;position=now;lat=Mavlink.i32(p,4)/1e7;lon=Mavlink.i32(p,8)/1e7;if(Math.abs(lat)>90||Math.abs(lon)>180)fail("GLOBAL_POSITION_WGS84_DOMAIN");altitudeMSL=Mavlink.i32(p,12)/1000.0;relativeAltitude=Mavlink.i32(p,16)/1000.0;horizontalSpeed=Math.hypot((short)Mavlink.u16(p,20),(short)Mavlink.u16(p,22))/100.0;verticalSpeed=Math.abs((short)Mavlink.u16(p,24))/100.0;
            if(homeRaw!=null&&armed){double distance=Math.hypot((lat-homeRaw[0]/1e7)*111319,(lon-homeRaw[1]/1e7)*111319*Math.cos(lat*Math.PI/180));if(distance>10||relativeAltitude>5)fail("DECLARED_FLIGHT_ENVELOPE_EXCEEDED");}
            if(armed&&landed==2&&Math.abs(relativeAltitude-3)<=.75&&horizontalSpeed<=.5&&verticalSpeed<=.5&&(mode==4||mode==5||mode==17)){if(hoverStart<0||hoverLast<0||now-hoverLast>750)hoverStart=now;hoverLast=now;}else{hoverStart=-1;hoverLast=-1;}
        }
    }
    private static Map<String,Object> homeFields(long[]h){return h==null?null:Values.map("latE7",h[0],"lonE7",h[1],"altMSLmm",h[2],"datum","AP_HOME_MSL_IN_SYNTHETIC_EXTERNAL_PROFILE");}
    private void age(long at,long now,long maximum,String reason)throws IOException{if(at<0||now-at<0||now-at>maximum)throw new IOException(reason);}
    public boolean discovery(long now)throws Exception{tick(now);return firmware&&hb>=0&&now-hb<=1500&&position>=0&&now-position<=1500;}
    public void ready(long now,boolean ground)throws Exception{
        if(!discovery(now))throw new IOException("FRESH_DISCOVERY_REQUIRED");age(homeAt,now,3000,"FRESH_HOME_REQUIRED");age(landAt,now,1500,"FRESH_LAND_STATE_REQUIRED");age(gpsAt,now,1500,"FRESH_GPS_REQUIRED");age(batteryAt,now,1500,"FRESH_SYS_STATUS_REQUIRED");age(ekfAt,now,1500,"FRESH_EKF_REQUIRED");
        if(!Arrays.asList(3,4,5,6,8).contains(fix))throw new IOException("GPS_FIX_UNKNOWN_STATIC_OR_UNSUPPORTED:"+fix);
        if(satellites<6||satellites>254)throw new IOException("GPS_SATELLITES_INSUFFICIENT_OR_UNKNOWN:"+satellites);
        if(hdop<0||hdop>200)throw new IOException("GPS_HDOP_UNKNOWN_OR_ABOVE_THRESHOLD:"+hdop);
        if((ekfFlags&~0x037F)!=0)throw new IOException("EKF_FLAGS_UNKNOWN_OR_UNQUALIFIED:0x"+Integer.toHexString(ekfFlags));
        if(voltage==65535||voltage<21000||(ekfFlags&55)!=55)throw new IOException("BATTERY_EKF_PREFLIGHT");
        long prearm=1L<<28;if(ground&&((sensorPresent&prearm)==0||(sensorEnabled&prearm)==0||(sensorHealth&prearm)==0))throw new IOException("ACTUAL_AP_PREARM_HEALTH_REQUIRED");
        long active=sensorPresent&sensorEnabled;long critical=1|2|4|8|32|2097152;if((active&critical)!=critical||(sensorHealth&critical)!=critical)throw new IOException("ACTUAL_SENSOR_HEALTH_REQUIRED");
        if(homeRaw==null||Math.abs(altitudeMSL-homeRaw[2]/1000.0-relativeAltitude)>1.0)throw new IOException("HOME_RELATIVE_MSL_DATUM_INCONSISTENT");
        if(ground&&(Math.hypot((lat-homeRaw[0]/1e7)*111319,(lon-homeRaw[1]/1e7)*111319*Math.cos(lat*Math.PI/180))>10||armed||landed!=1||Math.abs(relativeAltitude)>.4))throw new IOException("DISARMED_GROUND_REQUIRED");
        for(Map.Entry<String,int[]>e:specs.entrySet()){long[]v=parameters.get(e.getKey());int[]q=e.getValue();if(v==null||now-v[2]>10000||v[0]!=q[0]||v[1]!=q[1])throw new IOException("CONTROL_TYPED_PROFILE:"+e.getKey());}
    }
    public void consent(long now)throws Exception{ready(now,!armed);if(armed&&(mode==9||mode==6))throw new IOException("AUTONOMOUS_FAILSAFE_MODE_NO_CONSENT");if(armed&&!homeConfirmed)throw new IOException("ARMED_HOME_UNCONFIRMED");for(Map.Entry<String,long[]>e:parameters.entrySet())sealed.put(e.getKey(),e.getValue().clone());}
    public void action(String action,long now)throws Exception{
        ready(now,"ARM".equals(action));
        if(armed&&(mode==9||mode==6)&&!"LAND".equals(action))throw new IOException("DO_NOT_OVERRIDE_OBSERVED_LAND_RTL");
        if("ARM".equals(action)&&(mode!=4||armed))throw new IOException("ARM_GUIDED_ON_GROUND_ONLY");
        if("TAKEOFF".equals(action)&&(!armed||mode!=4||landed!=1||!homeConfirmed))throw new IOException("POST_ARM_CONFIRMED_HOME_BEFORE_TAKEOFF");
        if("LOITER".equals(action)&&(!armed||mode!=4||landed!=2||hoverStart<0||hoverLast-hoverStart<1000||now-hoverLast>500||!homeConfirmed))throw new IOException("OBSERVED_GUIDED_HOVER_BEFORE_LOITER");
        if(!Arrays.asList("GUIDED","ARM","TAKEOFF","LOITER","HOLD","LAND").contains(action))throw new IOException("ACTION_NOT_ALLOWED");
        if(("HOLD".equals(action)||"LAND".equals(action))&&!armed)throw new IOException("ARMED_REQUIRED_FOR_FLIGHT_ACTION");
    }
    public void armIntent() {armIntent=true;armIntentAt=last;}
    public void confirmHome(String displayedHash,long now,String actionId)throws Exception{
        ready(now,false);if(!armed||armAt<0||homeAt<=armAt||homeRaw==null||!Objects.equals(displayedHash,homeHash)||actionId==null)throw new IOException("EXPLICIT_FRESH_POST_ARM_HOME_CONFIRMATION_REQUIRED");
        event("POST_ARM_HOME_EXPLICITLY_CONFIRMED",Values.map("actionId",actionId,"atMs",now,"armObservedAtMs",armAt,"postArmHomeObservedAtMs",homeAt,"preArmHome",homeFields(preArmHome),"confirmedHome",homeFields(homeRaw),"displayedHomeHash",displayedHash));homeConfirmed=true;confirmedHomeHash=homeHash;
    }
    public void pilot(long now)throws Exception{ready(now,false);if(!armed||landed!=2||mode!=5||!homeConfirmed)throw new IOException("LOITER_ASSISTED_PILOT_STATE_REQUIRED");}
    public void safety(long now)throws Exception{if(!discovery(now)||landAt<0||now-landAt>1500||!armed||landed!=2||!homeConfirmed||mode==9||mode==6)throw new IOException("FRESH_CURRENT_BOOT_AIRBORNE_CLEANUP_REQUIRED");}
    public boolean isArmed(){return armed;}public int mode(){return mode;}public boolean isAirborne(){return armed&&landed==2;}
    public boolean hasParameter(String name){return specs.containsKey(name);}
    public Map<String,Object> snapshot(){return Values.map("firmwareObserved",firmware,"heartbeatMs",hb,"positionMs",position,"APBootMs",boot,"mode",mode,"armed",armed,"landedState",landed,"relativeAltitudeM",relativeAltitude,"altitudeMSLM",altitudeMSL,"lat",lat,"lon",lon,"horizontalSpeedMps",horizontalSpeed,"verticalSpeedMps",verticalSpeed,"preArmHome",homeFields(preArmHome),"home",homeFields(homeRaw),"homeHash",homeHash,"homeObservedAtMs",homeAt,"postArmHomePending",armed&&!homeConfirmed,"homeConfirmed",homeConfirmed,"armObservedAtMs",armAt,"typedParameterCount",parameters.size(),"batteryWireMillivolts",voltage,"GPSFix",fix,"GPSHDOP100",hdop,"satellites",satellites,"EKFFlags",ekfFlags,"sensorPresent",sensorPresent,"sensorEnabled",sensorEnabled,"sensorHealth",sensorHealth,"hoverObservedMs",hoverStart<0?0:Math.max(0,hoverLast-hoverStart),"disarmedGroundObservations",groundObservations,"failed",failed,"failure",failure,"manualModeMeaning","LOITER_PILOT_STICKS_WITH_AP_POSITION_ATTITUDE_ASSISTANCE_NOT_ACRO");}
}
