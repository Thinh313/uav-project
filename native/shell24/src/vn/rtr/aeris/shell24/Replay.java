package vn.rtr.aeris.shell24;
import java.util.*;
public final class Replay {
 public static String run(String id){InputModel i=new InputModel("native24-replay");i.focus(true,0);i.attach(new InputModel.Calibration("mock-cal-v1","mock:joystick",-1,0,1,.1,false),0);List<String> rows=new ArrayList<>();rows.add(i.json());i.sample(i.session,"mock:joystick",0,0);i.sample(i.session,"mock:joystick",0,50);i.sample(i.session,"mock:joystick",0,100);i.hold(true,100);i.acquire(100);rows.add(i.json());
 if(id.equals("normal")){i.sample(i.session,"mock:joystick",.55,150);rows.add(i.json());i.hold(false,200);}
 else if(id.equals("focus")){i.focus(false,150);rows.add(i.json());i.focus(true,200);}
 else if(id.equals("hotplug")){i.detach(150);rows.add(i.json());i.attach(new InputModel.Calibration("mock-cal-v2","mock:joystick",-1,0,1,.2,true),200);}
 else if(id.equals("stale")){i.tick(351);}
 else if(id.equals("foreign")){i.sample("old-session","mock:joystick",1,150);rows.add(i.json());i.tick(351);}
 else if(id.equals("reorder")){try{i.sample(i.session,"mock:joystick",1,99);}catch(IllegalArgumentException ignored){}}
 else throw new IllegalArgumentException("Replay id");rows.add(i.json());return "{\"id\":"+Json.quote(id)+",\"origin\":\"HOST_JAVA_SYNTHETIC_REPLAY\",\"operational\":false,\"states\":["+String.join(",",rows)+"]}";}
 public static void main(String[] args){StringBuilder b=new StringBuilder("{\"format\":\"aeris-native24-replays\",\"version\":1,\"scenarios\":[");String[] ids={"normal","focus","hotplug","stale","foreign","reorder"};for(int n=0;n<ids.length;n++){if(n>0)b.append(',');b.append(run(ids[n]));}System.out.println(b.append("]}").toString());}
}
