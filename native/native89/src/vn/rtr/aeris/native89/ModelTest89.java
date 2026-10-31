package vn.rtr.aeris.native89;
import java.util.*;
public final class ModelTest89 {
 private int count=0;private final ArrayList<String> names=new ArrayList<>();private void test(String name,Runnable r){r.run();count++;names.add(name);}static void yes(boolean b){if(!b)throw new AssertionError("Expected true");}static void refuses(Runnable r){try{r.run();}catch(IllegalArgumentException|IllegalStateException e){return;}throw new AssertionError("Expected refusal");}
 static InputModel.Calibration cal(){return new InputModel.Calibration("fixture-v1","mock:bench89",-1,0,1,.1,false);}static InputModel ready(){InputModel m=new InputModel("session");m.focus(true,0);m.attach(cal(),0);for(long t:new long[]{0,50,100})yes(m.sample("session","mock:bench89",0,t));m.hold(true,100);return m;}
 static VideoWatch89 playing(){VideoWatch89 v=new VideoWatch89();long g=v.prepare(0);yes(v.prepared(g,640,360,1500,1));yes(v.start(g,2));return v;}
 public static String run(){ModelTest89 q=new ModelTest89();q.all();StringJoiner names=new StringJoiner(",");for(String n:q.names)names.add(Json.quote(n));return "{\"status\":\"PASS\",\"checks\":"+q.count+",\"names\":["+names+"],\"physicalInputVerified\":false,\"flightAuthority\":false}";}
 private void all(){
 test("calibration endpoints/deadzone",()->{yes(cal().normalize(-1)==-1&&cal().normalize(1)==1&&cal().normalize(.05)==0);});
 test("calibration asymmetry and inversion",()->{InputModel.Calibration c=new InputModel.Calibration("v2","mock:x",-50,0,100,0,true);yes(c.normalize(50)==-.5);});
 test("no physical calibration claim",()->refuses(()->new InputModel.Calibration("v1","real:hub",-1,0,1,0,false)));
 test("nonfinite calibration refused",()->refuses(()->new InputModel.Calibration("v1","mock:x",Double.NaN,0,1,0,false)));
 test("acquire requires neutral and deadman",()->{InputModel m=new InputModel("session");m.focus(true,0);m.attach(cal(),0);yes(!m.acquire(0));});
 test("explicit mock acquire",()->yes(ready().acquire(100)));
 test("deadman release revokes",()->{InputModel m=ready();m.acquire(100);m.hold(false,110);yes(!m.owned()&&m.axis()==null);});
 test("freshness exact250 boundary",()->{InputModel m=ready();m.acquire(100);m.tick(350);yes(m.owned());m.tick(351);yes(!m.owned()&&m.axis()==null);});
 test("focus loss no restore",()->{InputModel m=ready();m.acquire(100);m.focus(false,110);m.focus(true,120);yes(!m.owned()&&!m.acquire(120));});
 test("detach attach no restore",()->{InputModel m=ready();m.acquire(100);m.detach(110);m.attach(cal(),120);yes(!m.owned()&&!m.acquire(120));});
 test("foreign session/device refused",()->{InputModel m=ready();yes(!m.sample("old","mock:bench89",1,160));yes(!m.sample("session","mock:other",1,210));});
 test("nonfinite axis revokes",()->{InputModel m=ready();m.acquire(100);refuses(()->m.sample("session","mock:bench89",Double.NaN,160));yes(!m.owned());});
 test("range not clamped",()->{InputModel m=ready();m.acquire(100);refuses(()->m.sample("session","mock:bench89",2,160));yes(!m.owned());});
 test("input rate bound",()->{InputModel m=ready();yes(!m.sample("session","mock:bench89",1,125));});
 test("input clock regression revokes",()->{InputModel m=ready();m.acquire(100);refuses(()->m.tick(99));yes(!m.owned());});
 test("new input session no restoration",()->yes(!new InputModel("new").owned()));
 test("video requires prepare/start",()->{VideoWatch89 v=new VideoWatch89();yes(!v.start(0,0)&&!v.frame(0,1,1));});
 test("video metadata bound",()->{VideoWatch89 v=new VideoWatch89();long g=v.prepare(0);yes(!v.prepared(g,1920,1080,1500,1));yes(v.state.equals("METADATA_REFUSED"));});
 test("zero and excessive duration refused",()->{for(long d:new long[]{0,10001}){VideoWatch89 v=new VideoWatch89();long g=v.prepare(0);yes(!v.prepared(g,640,360,d,1));}});
 test("render first callback",()->{VideoWatch89 v=playing();yes(v.frame(v.generation,10,10)&&v.frames==1);});
 test("duplicate texture timestamp never freshens",()->{VideoWatch89 v=playing();long g=v.generation;v.frame(g,10,10);yes(!v.frame(g,10,400));yes(v.callbackAge(400)==390);});
 test("stale exact500 boundary",()->{VideoWatch89 v=playing();long g=v.generation;v.frame(g,10,10);v.tick(510);yes(v.playing());v.tick(511);yes(!v.playing());});
 test("stale late callback no recovery",()->{VideoWatch89 v=playing();long g=v.generation;v.frame(g,10,10);v.tick(511);yes(!v.frame(g,20,520)&&v.state.equals("STALLED_NO_AUTO_RESUME"));});
 test("first frame timeout",()->{VideoWatch89 v=playing();v.tick(2003);yes(v.state.equals("STALLED_NO_AUTO_RESUME"));});
 test("stopped old generation cannot prepare/render/end",()->{VideoWatch89 v=playing();long g=v.generation;v.stop("FOCUS_LOST");yes(!v.prepared(g,640,360,1500,5)&&!v.frame(g,10,6)&&!v.end(g,7));});
 test("explicit new generation after stopped",()->{VideoWatch89 v=playing();long old=v.generation;v.stop("FOCUS_LOST");long g=v.prepare(5);yes(g>old&&v.prepared(g,640,360,1500,6)&&v.start(g,7));});
 test("ended needs callback proof",()->{VideoWatch89 v=playing();yes(!v.end(v.generation,10)&&v.state.equals("ENDED_NO_CALLBACK_PROOF"));});
 test("normal ended keeps provenance",()->{VideoWatch89 v=playing();v.frame(v.generation,10,10);yes(v.end(v.generation,20));yes(v.json(20).contains("\"cameraAgeMs\":null"));});
 test("video clock regression holds",()->{VideoWatch89 v=playing();refuses(()->v.tick(1));yes(v.state.equals("CLOCK_INVALID"));});
 test("negative producer timestamp refused",()->{VideoWatch89 v=playing();yes(!v.frame(v.generation,-1,10));});
 test("JSON control escaping",()->yes(Json.quote("a\n\"").equals("\"a\\u000a\\\"\"")));
 }
 public static void main(String[]args){System.out.println(run());}
}
