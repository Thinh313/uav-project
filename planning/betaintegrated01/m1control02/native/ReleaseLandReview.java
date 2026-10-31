import java.io.*;
import java.lang.reflect.*;
import java.nio.*;
import java.util.*;
import vn.rtr.aeris.control01.*;
import vn.rtr.aeris.beta01runtime.*;

/** Builder consumer checks. Shared previous QA fixture is disclosed, not independent review. */
public final class ReleaseLandReview {
    interface Op{void run()throws Exception;}
    static final List<Map<String,Object>> results=new ArrayList<>();
    static void check(boolean ok,String message){if(!ok)throw new AssertionError(message);}
    static void denied(Op op,String message)throws Exception{boolean yes=false;try{op.run();}catch(Exception expected){yes=true;}check(yes,message);}
    static void test(String id,Op op){try{op.run();results.add(Values.map("id",id,"pass",true));}catch(Throwable e){results.add(Values.map("id",id,"pass",false,"error",e.toString()));}}
    static Map<?,?> input(SessionQA.F f){return (Map<?,?>)f.s.snapshot().get("input");}
    static void uiSample(SessionQA.F f,boolean release,long oldMotion)throws Exception{
        long up=f.c.n-100000000L;
        f.s.input(new ControlAuthority.Input(f.context,SessionQA.SOURCE,"ANDROID_UPTIME_NS_SAMPLER",SessionQA.PROV,++f.inputseq,up,f.c.n,oldMotion,new double[4],0,1,release));
    }
    static long up(SessionQA.F f)throws Exception{f.c.n+=50000000L;long oldMotion=f.c.n-100000000L;uiSample(f,true,oldMotion);return oldMotion;}
    static void observedHold(SessionQA.F f,long delay)throws Exception{f.c.n+=delay;f.hb(true,17);f.land(2);f.health();f.home();f.pos(3000);}
    static void cleanup(SessionQA.F f){f.close();}
    public static void main(String[]args)throws Exception{
        SessionQA.root=new File(args[0]);check(SessionQA.root.mkdir(),"exclusive evidence fixture root");
        test("B01_UI_UP_FRESH_CENTERED_SECOND_CONSENT_THEN_LAND",()->{
            SessionQA.F f=new SessionQA.F("nominal-land",20000000000L);try{
                f.startPilot();String first=(String)input(f).get("leaseId");f.c.n+=50000000L;f.input(.6,1,false);int before=f.sent.size();
                long lastMotion=up(f);check(f.sent.size()==before+1,"UP did not send exactly one BRAKE intent");check(Boolean.FALSE.equals(input(f).get("consent")),"UP restored authority");
                observedHold(f,100000000L);check(f.sent.size()==before+3,"cleanup was not exactly3 packets");check("RELEASED".equals(f.s.snapshot().get("releaseState")),"release not complete");
                f.c.n+=50000000L;uiSample(f,false,lastMotion);check(Boolean.FALSE.equals(input(f).get("consent")),"fresh UI neutral auto-granted");
                f.action("CONSENT",null);String second=(String)input(f).get("leaseId");check(second!=null&&!second.equals(first),"second consent reused oldlease");
                f.c.n+=50000000L;uiSample(f,false,lastMotion);int at=f.sent.size();f.action("LAND",null);check(f.sent.size()==at+1,"LAND not one explicit packet");
                byte[] wire=f.sent.get(at),payload=SessionQA.data(wire);check(SessionQA.message(wire)==76&&SessionQA.u16(payload,28)==176&&SessionQA.le(payload).getFloat(4)==9,"LAND9 wire shape");check(Boolean.FALSE.equals(input(f).get("consent")),"LAND restored pilot authority");
            }finally{cleanup(f);}
        });
        test("B02_STOPPED_PRODUCER_OLD_UP_SAMPLE_CANNOT_CONSENT",()->{
            SessionQA.F f=new SessionQA.F("stale-center",20000000000L);try{f.startPilot();f.c.n+=50000000L;f.input(.6,1,false);up(f);observedHold(f,300000000L);int n=f.sent.size();denied(()->f.action("CONSENT",null),"old UP sample granted newlease");check(f.sent.size()==n,"consent refusal emitted flight command");check(Boolean.FALSE.equals(input(f).get("consent")),"stale sample restoredlease");}finally{cleanup(f);}
        });
        test("B03_FRESH_CENTER_WITHOUT_EXPLICIT_SECOND_CONSENT_CANNOT_LAND",()->{
            SessionQA.F f=new SessionQA.F("no-auto-consent",20000000000L);try{f.startPilot();f.c.n+=50000000L;f.input(.6,1,false);long event=up(f);observedHold(f,50000000L);uiSample(f,false,event);int n=f.sent.size();denied(()->f.action("LAND",null),"neutral sample silently restoredLANDauthority");check(f.sent.size()==n,"LAND written withoutsecondconsent");}finally{cleanup(f);}
        });
        test("B04_ACK_ONLY_DOES_NOT_ESTABLISH_BRAKE_OBSERVATION",()->{
            SessionQA.F f=new SessionQA.F("ack-not-brake",20000000000L);try{f.startPilot();f.c.n+=50000000L;f.input(.6,1,false);up(f);int n=f.sent.size();byte[]ack=SessionQA.p(77);SessionQA.le(ack).putShort(0,(short)176);ack[2]=0;f.emit(77,ack);check(f.sent.size()==n,"ACK triggeredneutral/release");check("WAIT_HOLD".equals(f.s.snapshot().get("releaseState")),"ACK promotedhold");f.c.n+=1501000000L;denied(()->f.s.tick(),"unobservedholdtimeoutaccepted");check(f.sent.size()==n,"cleanup retriedaftertimeout");}finally{cleanup(f);}
        });
        test("B05_UNKNOWN_BRAKE_SEND_PRESERVES_UNCERTAINTY_NO_RETRY",()->{
            SessionQA.F f=new SessionQA.F("brake-send-unknown",20000000000L);try{f.startPilot();f.c.n+=50000000L;f.input(.6,1,false);int n=f.sent.size();f.failSend=true;denied(()->up(f),"unknownBRAKEsendaccepted");check(f.sent.size()==n,"unknownwritecountedassent");check(Boolean.TRUE.equals(f.journal.snapshot().get("failed")),"journalnotfenced");check(SessionQA.lines(f.dir).contains("TX_UNKNOWN"),"unknownreceiptmissing");check(!f.s.actionRefusalRecoverable(new IOException("unknown")),"unknowncleanupwasrecoverable");f.s.fail("MOCK_BRAKE_SEND_UNKNOWN",true);denied(()->f.input(.6,1,false),"closednativefailureacceptedinput");check(f.sent.size()==n,"unknownsendretried");}finally{cleanup(f);}
        });
        test("B06_JOURNAL_FD_FAULT_BEFORE_UP_CANNOT_EMIT_CLEANUP",()->{
            SessionQA.F f=new SessionQA.F("up-journal-fault",20000000000L);try{f.startPilot();f.c.n+=50000000L;f.input(.6,1,false);int n=f.sent.size();Field field=NativeSegments.class.getDeclaredField("out");field.setAccessible(true);((FileOutputStream)field.get(f.journal)).close();denied(()->up(f),"closedjournalFDacceptedUP");check(f.sent.size()==n,"unjournaledcleanupemitted");check(Boolean.TRUE.equals(f.journal.snapshot().get("failed")),"IO faultnotfenced");f.s.fail("MOCK_JOURNAL_FD_FAULT",true);denied(()->f.input(.6,1,false),"nativefailureacceptednewinput");}finally{cleanup(f);}
        });
        test("B07_NATIVE_WAIT_ALLOWS_OBSERVED_HOLD_AFTER_RC_POINT5_BUT_IS_NOT_AP_PHYSICS_PROOF",()->{
            SessionQA.F f=new SessionQA.F("hold-observed700ms",20000000000L);try{f.startPilot();f.c.n+=50000000L;f.input(.6,1,false);up(f);int n=f.sent.size();observedHold(f,700000000L);check(f.sent.size()==n+2,"validobservedholdbefore1point5deadlinecouldnotfinish");check("RELEASED".equals(f.s.snapshot().get("releaseState")),"nativewaitnotreleased");}finally{cleanup(f);}
        });
        System.out.println(Values.json(Values.map("format","aeris-native-release-land-builder-review","results",results,"scope","CURRENT_APK02_PURE_JVM_REUSED_MOCK_AP_FIXTURE_REAL_FILESYSTEM_NOT_ANDROID_OR_AP_EXECUTION")));
    }
}
