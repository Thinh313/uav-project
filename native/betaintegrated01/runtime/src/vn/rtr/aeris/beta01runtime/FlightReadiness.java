package vn.rtr.aeris.beta01runtime;
import java.io.*;
import java.util.*;
import java.nio.charset.StandardCharsets;
import vn.rtr.aeris.native98.Profile95;
import vn.rtr.aeris.native98.Dialect95;
/** New versioned manual policy: same typed Native98 profile, not its AUTO gate. */
public final class FlightReadiness {
    private long hb=-1,position=-1,home=-1,land=-1,boot=-1,last=-1;
    private boolean version,armed,broken;private int mode=-1,landed=-1,previousSequence=-1;
    private String failure;private double altitude,lat,lon;
    private final Map<String,long[]> params=new HashMap<>(),sealed=new HashMap<>();
    private long[] homeRaw,boundHome;
    public void tick(long now)throws IOException{if(broken)throw new IOException(failure);if(now<last)fail("MONOTONIC_REGRESSION");last=now;if(hb>=0&&now-hb>3000)fail("HEARTBEAT_LOST");}
    private void fail(String r)throws IOException{broken=true;failure=r;throw new IOException(r);}
    public void frame(int id,int sys,int comp,int sequence,byte[]p,long now)throws IOException {
        tick(now);if(sys!=42||comp!=1)return;
        int delta=previousSequence<0?1:(sequence-previousSequence+256)%256;
        if(delta==128)fail("AP_SEQUENCE_AMBIGUOUS");
        if(delta==0||delta>128)return;
        previousSequence=sequence;
        if(id==0){if(Mavlink.u8(p,4)!=2||Mavlink.u8(p,5)!=3)fail("WRONG_AUTOPILOT");hb=now;armed=(p[6]&128)!=0;mode=(int)Mavlink.u32(p,0);}
        if(id==148){int v=Dialect95.at(id,"flight_custom_version");if(Mavlink.u32(p,Dialect95.at(id,"flight_sw_version"))!=67568127L||!new String(Arrays.copyOfRange(p,v,v+8),StandardCharsets.US_ASCII).equals("dbe79216"))fail("FIRMWARE_BINDING");version=true;}
        if(id==22){int end=8;while(end<24&&p[end]!=0)end++;String name=new String(p,8,end-8,StandardCharsets.US_ASCII);if(Profile95.P.containsKey(name)){int bits=Mavlink.i32(p,0),type=Mavlink.u8(p,24);if(!Float.isFinite(Float.intBitsToFloat(bits)))fail("NONFINITE_PARAMETER");long[] old=sealed.containsKey(name)?sealed.get(name):params.get(name);if(old!=null&&(!sealed.isEmpty()||armed)&&(old[0]!=type||old[1]!=bits))fail("PARAMETER_CHANGED_AFTER_CONSENT");params.put(name,new long[]{type,bits,now});}}
        if(id==242){homeRaw=new long[]{Mavlink.i32(p,0),Mavlink.i32(p,4),Mavlink.i32(p,8)};if(boundHome!=null&&!Arrays.equals(homeRaw,boundHome))fail("HOME_CHANGED_AFTER_CONSENT");home=now;}
        if(id==245){land=now;landed=Mavlink.u8(p,1);}
        if(id==33){long b=Mavlink.u32(p,0);if(boot>=0&&(b-boot+4294967296L)%4294967296L>=2147483648L)fail("AP_BOOT_REGRESSION");boot=b;position=now;lat=Mavlink.i32(p,4)/1e7;lon=Mavlink.i32(p,8)/1e7;altitude=Mavlink.i32(p,16)/1000.0;}
    }
    public boolean discoveryReady(long now)throws IOException {tick(now);return version&&hb>=0&&now-hb<=1500&&position>=0&&now-position<=1500;}
    public void requireProfile(long now,boolean onGround)throws IOException {
        if(!discoveryReady(now)||home<0||now-home>3000||land<0||now-land>1500||(onGround&&(armed||landed!=1)))throw new IOException("READONLY_PROFILE_OBSERVATIONS_REQUIRED");
        for(Map.Entry<String,double[]>e:Profile95.P.entrySet()){long[]v=params.get(e.getKey());double[]q=e.getValue();if(v==null||now-v[2]>10000||v[0]!=(int)q[0]||Float.intBitsToFloat((int)v[1])<q[1]||Float.intBitsToFloat((int)v[1])>q[2])throw new IOException("TYPED_PROFILE:"+e.getKey());}
    }
    public void requireManualCommand(String action,long now)throws IOException {
        requireProfile(now,"ARM".equals(action));
        if("ARM".equals(action)&&mode!=4)throw new IOException("GUIDED_BEFORE_ARM");
        if("TAKEOFF".equals(action)&&(!armed||mode!=4||landed!=1))throw new IOException("TAKEOFF_STATE");
        if("PULSE".equals(action)&&(!armed||landed!=2||!(mode==4||mode==5)))throw new IOException("MANUAL_AIRBORNE_STATE");
        if(!Arrays.asList("GUIDED","ARM","TAKEOFF","PULSE","LAND").contains(action))throw new IOException("MANUAL_ACTION_ALLOWLIST");
    }
    public void sealProfile(long now)throws IOException {requireProfile(now,true);for(Map.Entry<String,long[]>e:params.entrySet())sealed.put(e.getKey(),e.getValue().clone());boundHome=homeRaw.clone();}
    public Map<String,Object> snapshot(){return Values.map("firmwareObserved",version,"heartbeatMs",hb,"positionMs",position,"APBootMs",boot,"homeMs",home,"landMs",land,"mode",mode,"armed",armed,"landedState",landed,"relativeAltitudeM",altitude,"lat",lat,"lon",lon,"typedParameters",params.size(),"broken",broken,"failure",failure);}
}
