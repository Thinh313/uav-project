import java.util.*;import java.nio.*;
import vn.rtr.aeris.control01.ControlFlight;
import vn.rtr.aeris.beta01runtime.Values;
import vn.rtr.aeris.native98.Dialect95;
public final class ControlFlightQA {
 interface Op{void run()throws Exception;}static List<Map<String,Object>>results=new ArrayList<>();
 static void check(boolean b,String s){if(!b)throw new AssertionError(s);}static void denied(Op o,String s)throws Exception{boolean fail=false;try{o.run();}catch(Exception e){fail=true;}check(fail,s);}
 static void test(String id,Op o){try{o.run();results.add(Values.map("id",id,"pass",true));}catch(Throwable e){results.add(Values.map("id",id,"pass",false,"error",e.toString()));}}
 static byte[] payload(int id){return new byte[Dialect95.D.get(id)[1]];}
 static ByteBuffer le(byte[]p){return ByteBuffer.wrap(p).order(ByteOrder.LITTLE_ENDIAN);}
 static class F {
  final ControlFlight flight=new ControlFlight(ProfileFixture.specs(),(k,e)->{});int seq;long now=1000;int altitudeHome=10000;
  F()throws Exception{hb(1000,false,4);byte[]v=payload(148);le(v).putInt(Dialect95.at(148,"flight_sw_version"),67568127);System.arraycopy("dbe79216".getBytes("US-ASCII"),0,v,Dialect95.at(148,"flight_custom_version"),8);emit(148,v,1000);for(Map.Entry<String,int[]>e:ProfileFixture.specs().entrySet())param(1000,e.getKey(),e.getValue()[0],e.getValue()[1]);home(1000,10000);land(1000,1);health(1000,true);gps(1000);ekf(1000);pos(1000,1000,0,108540000);}
  void emit(int id,byte[]p,long at)throws Exception{flight.frame(id,42,1,(seq++)&255,p,at);now=at;}
  void hb(long at,boolean armed,int mode)throws Exception{byte[]p=payload(0);le(p).putInt(0,mode);p[4]=2;p[5]=3;p[6]=(byte)(armed?128:0);p[7]=4;p[8]=3;emit(0,p,at);}
  void param(long at,String name,int type,int bits)throws Exception{byte[]p=payload(22);le(p).putInt(0,bits);byte[]key=name.getBytes("US-ASCII");System.arraycopy(key,0,p,8,key.length);p[24]=(byte)type;emit(22,p,at);}
  void home(long at,int alt)throws Exception{byte[]p=payload(242);le(p).putInt(0,108540000).putInt(4,1068070000).putInt(8,alt);emit(242,p,at);altitudeHome=alt;}
  void land(long at,int state)throws Exception{byte[]p=payload(245);p[1]=(byte)state;emit(245,p,at);}
  void health(long at,boolean prearm)throws Exception{byte[]p=payload(1);int m=1|2|4|8|32|2097152|(prearm?(1<<28):0);le(p).putInt(0,m).putInt(4,m).putInt(8,m).putShort(14,(short)24000);p[30]=80;emit(1,p,at);}
  void gps(long at)throws Exception{byte[]p=payload(24);le(p).putShort(20,(short)100);p[28]=3;p[29]=12;emit(24,p,at);}
  void ekf(long at)throws Exception{byte[]p=payload(193);le(p).putShort(Dialect95.at(193,"flags"),(short)55);emit(193,p,at);}
  void pos(long at,int boot,int rel,int lat)throws Exception{byte[]p=payload(33);le(p).putInt(0,boot).putInt(4,lat).putInt(8,1068070000).putInt(12,altitudeHome+rel).putInt(16,rel);emit(33,p,at);}
  void arm()throws Exception{flight.consent(1000);flight.action("ARM",1000);flight.armIntent();hb(1100,true,4);}
  void confirm()throws Exception{home(1200,10012);flight.confirmHome((String)flight.snapshot().get("homeHash"),1200,"root-home01");}
  void fresh(long at)throws Exception{hb(at,true,4);land(at,2);health(at,true);gps(at);ekf(at);home(at,altitudeHome);}
 }
 public static void main(String[]args)throws Exception{
  test("F01_EXACT_TYPED_HEALTHY_PREFLIGHT",()->{F f=new F();f.flight.ready(1000,true);f.flight.consent(1000);check(((Number)f.flight.snapshot().get("typedParameterCount")).intValue()==ProfileFixture.specs().size(),"profile count");});
  test("F02_DISABLED_FAILSAFE_READBACK_REFUSED",()->{F f=new F();f.param(1000,"FS_GCS_ENABLE",2,Float.floatToIntBits(0));denied(()->f.flight.ready(1000,true),"disabled GCS ready");});
  test("F03_WRONG_TYPED_FAILSAFE_REFUSED",()->{F f=new F();f.param(1000,"FS_OPTIONS",4,0);denied(()->f.flight.ready(1000,true),"wrong param type");});
  test("F04_NO_AP_PREARM_HEALTH_REFUSED",()->{F f=new F();f.health(1000,false);denied(()->f.flight.ready(1000,true),"missing real prearm health");});
  test("F05_POSTARM_HOME_REQUIRED_AND_EXACT",()->{F f=new F();String old=(String)f.flight.snapshot().get("homeHash");f.arm();denied(()->f.flight.action("TAKEOFF",1100),"takeoff before home");denied(()->f.flight.confirmHome(old,1150,"confirm-old"),"prearm home confirmed");f.home(1200,10012);denied(()->f.flight.confirmHome(old,1200,"confirm-wrong"),"wrong hash accepted");f.flight.confirmHome((String)f.flight.snapshot().get("homeHash"),1200,"confirm-current");f.flight.action("TAKEOFF",1200);});
  test("F06_CHANGED_CONFIRMED_HOME_REVOKES",()->{F f=new F();f.arm();f.confirm();denied(()->f.home(1201,10013),"confirmed home changed");check(Boolean.TRUE.equals(f.flight.snapshot().get("failed")),"no revoke");});
  test("F07_AP_BOOT_REGRESSION_REVOKES",()->{F f=new F();denied(()->f.pos(1100,500,0,108540000),"boot regression accepted");check(Boolean.TRUE.equals(f.flight.snapshot().get("failed")),"no reboot revoke");});
  test("F08_SINGLE_HOVER_POINT_CANNOT_PROVE_ONE_SECOND",()->{F f=new F();f.arm();f.confirm();f.hb(1300,true,4);f.land(1300,2);f.pos(1300,1300,3000,108540000);denied(()->f.flight.action("LOITER",2300),"elapsedtime falsely proves hover");});
  test("F09_OBSERVED_HOVER_SPAN_ACCEPTED",()->{F f=new F();f.arm();f.confirm();f.fresh(1300);f.pos(1300,1300,3000,108540000);f.fresh(1850);f.pos(1850,1850,3000,108540000);f.fresh(2350);f.pos(2350,2350,3000,108540000);f.flight.action("LOITER",2350);check(((Number)f.flight.snapshot().get("hoverObservedMs")).longValue()==1050,"wrong observed span");});
  test("F10_STALE_GROUND_FACTS_DO_NOT_ACCUMULATE",()->{F f=new F();f.hb(1000,false,4);f.hb(1300,false,4);check(((Number)f.flight.snapshot().get("disarmedGroundObservations")).intValue()>=2,"fresh ground count");f.hb(1701,false,4);check(((Number)f.flight.snapshot().get("disarmedGroundObservations")).intValue()==0,"stale ground kept");});
  test("F11_INVALID_WGS84_POSITION_REFUSED",()->{F f=new F();denied(()->{f.pos(1100,1100,0,910000000);f.flight.ready(1100,true);},"lat91deg preflight accepted");});
  test("F12_GUIDED_HOVER_CANNOT_OVERRIDE_LAND_MODE",()->{F f=new F();f.arm();f.confirm();f.fresh(1300);f.pos(1300,1300,3000,108540000);f.fresh(1850);f.pos(1850,1850,3000,108540000);f.fresh(2350);f.pos(2350,2350,3000,108540000);f.hb(2351,true,9);denied(()->f.flight.action("LOITER",2351),"LOITER overrides LAND with stale hover");});
  test("F13_UNKNOWN_SATELLITES_255_REFUSED",()->{F f=new F();byte[]p=payload(24);le(p).putShort(20,(short)100);p[28]=3;p[29]=(byte)255;f.emit(24,p,1000);denied(()->f.flight.ready(1000,true),"GPS satellites255 unknown accepted with independent healthy masks");});
  test("F14_RESERVED_GPS_FIX_255_REFUSED",()->{F f=new F();byte[]p=payload(24);le(p).putShort(20,(short)100);p[28]=(byte)255;p[29]=12;f.emit(24,p,1000);denied(()->f.flight.ready(1000,true),"GPS fix255 undefined accepted");});
  test("F15_EKF_GPS_GLITCH_REFUSED",()->{F f=new F();byte[]p=payload(193);le(p).putShort(Dialect95.at(193,"flags"),(short)(55|32768));f.emit(193,p,1000);denied(()->f.flight.ready(1000,true),"EKF GPS glitch accepted despite healthy positive bits");});
  test("F16_EKF_UNINITIALIZED_REFUSED",()->{F f=new F();byte[]p=payload(193);le(p).putShort(Dialect95.at(193,"flags"),(short)(55|1024));f.emit(193,p,1000);denied(()->f.flight.ready(1000,true),"EKF uninitialized accepted despite positive bits");});
  test("F17_STATIC_AND_RESERVED_GPS_FIX_REFUSED",()->{for(int fix:new int[]{7,9,254}){F f=new F();byte[]p=payload(24);le(p).putShort(20,(short)100);p[28]=(byte)fix;p[29]=12;f.emit(24,p,1000);denied(()->f.flight.ready(1000,true),"unqualified GPS fix accepted:"+fix);}});
  test("F18_CONST_POS_AND_UNKNOWN_EKF_BITS_REFUSED",()->{for(int bit:new int[]{128,2048,4096,8192,16384}){F f=new F();byte[]p=payload(193);le(p).putShort(Dialect95.at(193,"flags"),(short)(55|bit));f.emit(193,p,1000);denied(()->f.flight.ready(1000,true),"unqualified EKF mask accepted:"+bit);}});
  test("F19_APPROVED_GPS_FIX_AND_KNOWN_POSITIVE_EKF_FLAGS_ACCEPTED",()->{for(int fix:new int[]{3,4,5,6,8}){F f=new F();byte[]p=payload(24);le(p).putShort(20,(short)200);p[28]=(byte)fix;p[29]=(byte)254;f.emit(24,p,1000);p=payload(193);le(p).putShort(Dialect95.at(193,"flags"),(short)0x037f);f.emit(193,p,1000);f.flight.ready(1000,true);}});
  System.out.println(Values.json(Values.map("format","aeris-independent-control-flight-qa","results",results,"scope","PURE_JVM_PADDED_PROTOCOL_OBSERVATIONS_NO_FLIGHT_EXECUTION")));
 }
}
