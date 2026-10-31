package vn.rtr.aeris.shell24;
import java.util.*;
public final class ModelTest {
 static int count=0;static void test(String name,Runnable run){run.run();count++;System.out.println("PASS "+name);}static void yes(boolean b){if(!b)throw new AssertionError();}static void eq(double a,double b){yes(Math.abs(a-b)<0.00001);}static void refuses(Runnable r){try{r.run();}catch(IllegalArgumentException|IllegalStateException e){return;}throw new AssertionError("Expected refusal");}
 static InputModel.Calibration c(){return new InputModel.Calibration("mock-cal-v1","mock:joystick",-1,0,1,.1,false);}static InputModel ready(){InputModel i=new InputModel("s1");i.focus(true,0);i.attach(c(),0);i.sample("s1","mock:joystick",0,0);i.sample("s1","mock:joystick",0,50);i.sample("s1","mock:joystick",0,100);i.hold(true,100);return i;}
 static VideoModel video(){VideoModel v=new VideoModel();v.select("SYNTHETIC_FIXTURE",String.join("",Collections.nCopies(64,"a")),1024,0);return v;}
 public static void main(String[] args){
 test("center/deadzone",()->{eq(c().normalize(0),0);eq(c().normalize(.1),0);eq(c().normalize(-.05),0);});
 test("rescaled positive/negative endpoints",()->{eq(c().normalize(1),1);eq(c().normalize(-1),-1);eq(c().normalize(.55),.5);});
 test("asymmetric calibrated range",()->{eq(new InputModel.Calibration("v2","mock:x",-50,0,100,0,false).normalize(50),.5);});
 test("inversion",()->eq(new InputModel.Calibration("v2","mock:x",-1,0,1,0,true).normalize(.5),-.5));
 test("real device calibration prohibited",()->refuses(()->new InputModel.Calibration("v1","real:joystick",-1,0,1,0,false)));
 test("NaN range refused",()->refuses(()->new InputModel.Calibration("v1","mock:x",Double.NaN,0,1,0,false)));
 test("invalid center/deadzone refused",()->{refuses(()->new InputModel.Calibration("v1","mock:x",0,0,1,0,false));refuses(()->new InputModel.Calibration("v1","mock:x",-1,0,1,1,false));});
 test("neutral and deadman required",()->{InputModel i=new InputModel("s1");i.focus(true,0);i.attach(c(),0);i.hold(true,0);yes(!i.acquire(0));});
 test("three neutral samples allow explicit mock ownership",()->yes(ready().acquire(100)));
 test("ownership no operational output",()->{InputModel i=ready();i.acquire(100);yes(i.json().contains("\"operational\":false"));yes(i.json().contains("\"physicalMappingVerified\":false"));});
 test("off-neutral cannot acquire",()->{InputModel i=ready();i.sample("s1","mock:joystick",.8,150);yes(!i.acquire(150));});
 test("foreign session ignored",()->{InputModel i=ready();yes(!i.sample("old","mock:joystick",1,150));eq(i.axis(),0);});
 test("foreign device ignored",()->{InputModel i=ready();yes(!i.sample("s1","mock:other",1,150));eq(i.axis(),0);});
 test("axis rate bounded20Hz",()->{InputModel i=ready();yes(!i.sample("s1","mock:joystick",1,125));eq(i.axis(),0);});
 test("NaN input revokes",()->{InputModel i=ready();i.acquire(100);refuses(()->i.sample("s1","mock:joystick",Double.NaN,150));yes(!i.owned()&&i.axis()==null);});
 test("out-of-range not clamped into control",()->{InputModel i=ready();refuses(()->i.sample("s1","mock:joystick",2,150));yes(!i.owned());});
 test("stale input revokes and removes axis",()->{InputModel i=ready();i.acquire(100);i.tick(351);yes(!i.owned()&&i.axis()==null&&i.reason().equals("STALE_INPUT"));});
 test("unowned stale axis unavailable",()->{InputModel i=ready();i.tick(351);yes(i.axis()==null);});
 test("focus regain never reacquires",()->{InputModel i=ready();i.acquire(100);i.focus(false,150);i.focus(true,200);yes(!i.owned()&&!i.acquire(200));});
 test("hotplug revokes calibration qualification",()->{InputModel i=ready();i.acquire(100);i.detach(150);i.attach(c(),200);i.hold(true,200);yes(!i.acquire(200));});
 test("release deadman revokes",()->{InputModel i=ready();i.acquire(100);i.hold(false,150);yes(!i.owned());});
 test("timestamp regression revokes",()->{InputModel i=ready();i.acquire(100);refuses(()->i.tick(99));yes(!i.owned());});
 test("calibration replacement revokes",()->{InputModel i=ready();i.acquire(100);i.attach(new InputModel.Calibration("v2","mock:joystick",-1,0,1,.2,false),150);yes(!i.owned()&&i.neutral()==0);});
 test("input history bounded and drops visible",()->{InputModel i=ready();for(int n=1;n<400;n++)i.sample("s1","mock:joystick",0,100+n*50);yes(i.historySize()==128&&i.dropped()>0);});
 test("video absent source refused",()->refuses(()->new VideoModel().prepare(0)));
 test("video physical origin refused",()->refuses(()->new VideoModel().select("PHYSICAL_VERIFIED",String.join("",Collections.nCopies(64,"a")),10,0)));
 test("invalid hash/byte cap refused",()->{refuses(()->new VideoModel().select("SYNTHETIC_FIXTURE","bad",10,0));refuses(()->new VideoModel().select("SYNTHETIC_FIXTURE",String.join("",Collections.nCopies(64,"a")),VideoModel.MAX_BYTES+1,0));});
 test("prepare metadata limits",()->{VideoModel v=video();long g=v.prepare(0);yes(!v.prepared(g,3840,2160,1000,1));yes(v.state.equals("UNSUPPORTED_LOCAL_VIDEO"));});
 test("unknown duration refused",()->{VideoModel v=video();long g=v.prepare(0);yes(!v.prepared(g,640,360,0,1));});
 test("duration cap",()->{VideoModel v=video();long g=v.prepare(0);yes(!v.prepared(g,640,360,120001,1));});
 test("play requires prepared",()->{VideoModel v=video();long g=v.prepare(0);yes(!v.play(g,1));});
 test("render-start is not continuous frame age",()->{VideoModel v=video();long g=v.prepare(0);yes(v.prepared(g,640,360,1000,1));yes(v.play(g,2)&&v.rendered(g,3));yes(v.json().contains("\"frameAgeMs\":null")&&v.json().contains("\"physicalMediaVerified\":false"));});
 test("stopped generation ignores stale callbacks",()->{VideoModel v=video();long g=v.prepare(0);v.stop("FOCUS_LOST");yes(!v.prepared(g,640,360,1000,1)&&!v.rendered(g,2));});
 test("end needs current playing generation",()->{VideoModel v=video();long g=v.prepare(0);yes(v.prepared(g,640,360,1000,1));yes(v.play(g,2));yes(!v.ended(g-1,3));yes(v.ended(g,4));});
 test("video clock regression invalidates generation",()->{VideoModel v=video();long g=v.prepare(10);refuses(()->v.prepared(g,640,360,1000,9));yes(v.state.equals("CLOCK_REGRESSION"));});
 test("shell lifecycle cancels mock input/video",()->{ShellState s=new ShellState();s.focus(true,0);s.video.select("SYNTHETIC_FIXTURE",String.join("",Collections.nCopies(64,"a")),10,0);s.focus(false,1);yes(!s.input.owned()&&s.video.state.equals("LIFECYCLE_STOPPED"));});
 test("historical checkpoint has no restored authority",()->{ShellState s=new ShellState();s.navigate("Review");yes(s.checkpoint().contains("\"authorityRestorable\":false"));ShellState reopened=new ShellState();yes(!s.session.equals(reopened.session)&&!reopened.input.owned()&&!reopened.video.selected);});
 test("workspace whitelist and JSON escaping",()->{refuses(()->new ShellState().navigate("ARM"));yes(Json.quote("a\"\nb").equals("\"a\\\"\\u000ab\""));});
 System.out.println("TOTAL "+count+" PASS; host pure-Java only; Android runtime NOT_CHECKED");
 }
}
