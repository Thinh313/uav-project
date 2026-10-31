import vn.rtr.aeris.beta01runtime.*;
import vn.rtr.aeris.betaintegrated01.*;
import vn.rtr.aeris.native98.Dialect95;
import java.io.*;
import java.nio.*;
import java.nio.channels.*;
import java.nio.file.*;
import java.util.*;

/** Independent pure-JVM adapter/fault checks. No SocketOwner or Android process. */
public final class NativeAdapterQA {
    interface Op {void run()throws Exception;}
    static final class C implements RunLifecycle.Clock,NativeSegments.Clock {
        long n=1000000000L;public long monotonicNs(){return n;}public long wallUtcMs(){return 1700000000000L+n/1000000;}public long nowNs(){return n;}
    }
    static final class S implements NativeSegments.Sync {
        boolean failFile,failDir;int syncs;
        public void file(FileDescriptor fd)throws IOException {if(failFile)throw new IOException("QA_FSYNC");fd.sync();syncs++;}
        public void directory(File p)throws IOException {if(failDir)throw new IOException("QA_DIRSYNC");try(FileChannel c=FileChannel.open(p.toPath(),StandardOpenOption.READ)){c.force(true);}}
    }
    static File root;static int group;static List<Map<String,Object>> results=new ArrayList<>();
    static void check(boolean ok,String why){if(!ok)throw new AssertionError(why);}
    static void denied(Op o,String why)throws Exception {boolean denied=false;try{o.run();}catch(Exception e){denied=true;}check(denied,why);}
    static NativeSegments journal(String id,C c,S s)throws Exception{return new NativeSegments(new File(root,id),id,"epoch01",c,s,32768,524288,128);}
    static String lines(File d)throws Exception{StringBuilder s=new StringBuilder();File[]f=d.listFiles((p,n)->n.endsWith(".jsonl"));Arrays.sort(f);for(File x:f)s.append(new String(Files.readAllBytes(x.toPath()),java.nio.charset.StandardCharsets.UTF_8));return s.toString();}
    static void test(String id,Op o)throws Exception{try{o.run();results.add(Values.map("id",id,"pass",true));}catch(Throwable t){results.add(Values.map("id",id,"pass",false,"error",t.toString()));}}
    static byte[] ap(int id,int seq,byte[]p){byte[]b=Mavlink.packet(id,p,seq);b[5]=42;b[6]=1;int len=b[1]&255,c=Mavlink.crc(b,10+len,Dialect95.D.get(id)[2]);b[10+len]=(byte)c;b[11+len]=(byte)(c>>8);return b;}
    static byte[] payload(int id){return new byte[Dialect95.D.get(id)[1]];}
    static byte[] hb(int seq){byte[]p=payload(0);ByteBuffer.wrap(p).order(ByteOrder.LITTLE_ENDIAN).putInt(0,4);p[4]=2;p[5]=3;p[7]=4;p[8]=3;return ap(0,seq,p);}
    static byte[] version(int seq){byte[]p=payload(148);ByteBuffer.wrap(p).order(ByteOrder.LITTLE_ENDIAN).putInt(Dialect95.at(148,"flight_sw_version"),67568127);System.arraycopy("dbe79216".getBytes(java.nio.charset.StandardCharsets.US_ASCII),0,p,Dialect95.at(148,"flight_custom_version"),8);return ap(148,seq,p);}
    static byte[] position(int seq){byte[]p=payload(33);ByteBuffer.wrap(p).order(ByteOrder.LITTLE_ENDIAN).putInt(0,1000).putInt(4,370000000).putInt(8,-1220000000);return ap(33,seq,p);}
    static final String H1=String.join("",Collections.nCopies(64,"1")),H2=String.join("",Collections.nCopies(64,"2")),H3=String.join("",Collections.nCopies(64,"3"));
    static ProviderDescriptor descriptor(){return new ProviderDescriptor(1,ProviderDescriptor.Mode.CANDIDATE_EXTERNAL,"qa-profile",H1,H2,H3,"tcp://10.0.2.2:5937","4.7.1");}
    static ProviderDescriptor.Observation observed(String hash){return new ProviderDescriptor.Observation(1,ProviderDescriptor.Mode.CANDIDATE_EXTERNAL,"qa-profile",hash,H2,H3,"tcp://10.0.2.2:5937","4.7.1",true);}
    static RuntimeSession session(String id,C c,S s,boolean[]fg,int[]sends,boolean manual)throws Exception{return new RuntimeSession(new RunLifecycle.Context(id,"epoch01","boot01","operator01","generation01","qa-profile"),c,descriptor(),observed(H1),journal(id,c,s),()->fg[0],b->{sends[0]++;},1800000000000L,manual);}
    static Map<?,?> child(Map<?,?>m,String k){return (Map<?,?>)m.get(k);}
    public static void main(String[]args)throws Exception{
        root=new File(args[0]);if(!root.mkdir())throw new IOException("QA_OUTPUT_EXCLUSIVE");
        test("N01_ROTATE_GLOBAL_ORDER",()->{C c=new C();S s=new S();NativeSegments j=journal("normal",c,s);for(int i=0;i<120;i++)j.append("RX",new byte[200]);String a=j.finish("QA_CLOSE");check(a.length()==64,"anchor");String l=lines(new File(root,"normal"));int n=0;for(String line:l.split("\n")){n++;check(line.contains("\"n\":"+n+","),"global sequence "+n);}check(n>120,"headers+close");check(((Number)j.snapshot().get("segments")).intValue()>1,"rotation");for(File f:new File(root,"normal").listFiles((p,name)->name.endsWith(".jsonl")))check(f.length()<=32768,"segment max");j.close();});
        test("N02_INTENT_SYNC_BEFORE_CALLBACK",()->{C c=new C();S s=new S();NativeSegments j=journal("barrier",c,s);int old=s.syncs;j.intentSend(new byte[]{1,2,3},b->{check(s.syncs>old,"sync missing");check(lines(new File(root,"barrier")).contains("\"kind\":\"TX_INTENT\""),"intent absent");});j.finish("QA_CLOSE");j.close();});
        test("N03_FSYNC_FAIL_ZERO_SEND",()->{C c=new C();S s=new S();NativeSegments j=journal("sync-fail",c,s);int[]send={0};s.failFile=true;denied(()->j.intentSend(new byte[]{1},b->{send[0]++;}),"fsync must fail");check(send[0]==0,"sent on fsync fail");check(Boolean.TRUE.equals(j.snapshot().get("failed")),"not fenced");j.close();});
        test("N04_UNKNOWN_SEND_FENCES",()->{C c=new C();S s=new S();NativeSegments j=journal("send-fail",c,s);denied(()->j.intentSend(new byte[]{1},b->{throw new IOException("QA_SEND_UNKNOWN");}),"send fail");check(lines(new File(root,"send-fail")).contains("\"kind\":\"TX_UNKNOWN\""),"no unknown");denied(()->j.append("RX",new byte[1]),"append after poison");check(!new File(root,"send-fail/session.json").exists(),"false complete");j.close();});
        test("N05_POLICY_BOUNDS",()->{C c=new C();S s=new S();denied(()->new NativeSegments(new File(root,"overflow"),"overflow","epoch01",c,s,Long.MAX_VALUE,Long.MAX_VALUE,3),"overflow policy");denied(()->new NativeSegments(new File(root,"oversize"),"oversize","epoch01",c,s,16L*1024*1024,64L*1024*1024,3),"unbounded segment");});
        test("N06_RUNTIME_RX_AND_READONLY_SEND",()->{C c=new C();S s=new S();int[]sends={0};boolean[]fg={true};RuntimeSession r=session("runtime",c,s,fg,sends,false);r.receive(hb(20));r.receive(version(21));r.receive(position(22));check("ACTIVE".equals(child(r.snapshot(),"lifecycle").get("phase")),"not activated");r.sendReadOnly(Mavlink.heartbeat(0));check(sends[0]==1,"readOnly send");r.beginClose("QA_CLOSE");r.resourcesClosed(true);});
        test("N07_DUPLICATE_OLD_RX_NO_FRESHNESS",()->{C c=new C();S s=new S();RuntimeSession r=session("duplicate",c,s,new boolean[]{true},new int[1],false);byte[]oldHB=hb(20);r.receive(oldHB);r.receive(version(21));r.receive(position(22));long before=((Number)child(r.snapshot(),"flight").get("heartbeatMs")).longValue();c.n+=500000000L;r.receive(oldHB);long after=((Number)child(r.snapshot(),"flight").get("heartbeatMs")).longValue();check(before==after,"stale sequence refreshed hb: "+before+" -> "+after);r.beginClose("QA_CLOSE");r.resourcesClosed(true);});
        test("N08_MANUAL_DEFAULT_DISABLED",()->{C c=new C();S s=new S();int[]sends={0};RuntimeSession r=session("manual-disabled",c,s,new boolean[]{true},sends,false);r.receive(hb(20));r.receive(version(21));r.receive(position(22));denied(()->r.consentManual(),"manual enabled");denied(()->r.neutral(),"neutral without consent");denied(()->r.manual("ARM",0,new double[4],c.n),"ARM without consent");check(sends[0]==0,"manual dispatched");r.beginClose("QA_CLOSE");r.resourcesClosed(true);});
        test("N09_BACKGROUND_SEND_ZERO",()->{C c=new C();S s=new S();int[]sends={0};boolean[]fg={true};RuntimeSession r=session("background",c,s,fg,sends,false);fg[0]=false;denied(()->r.sendReadOnly(Mavlink.heartbeat(0)),"background send");check(sends[0]==0,"background dispatch");r.failClose("QA_BACKGROUND",true);});
        test("N10_CLOSED_TIME_AND_LATE_RX",()->{C c=new C();S s=new S();RuntimeSession r=session("closed-time",c,s,new boolean[]{true},new int[1],false);r.receive(hb(20));r.receive(version(21));r.receive(position(22));c.n+=500000000L;r.beginClose("QA_CLOSE");r.resourcesClosed(true);long first=((Number)child(r.snapshot(),"lifecycle").get("activeElapsedNs")).longValue();c.n+=1000000000L;long second=((Number)child(r.snapshot(),"lifecycle").get("activeElapsedNs")).longValue();check(first==second&&first==500000000L,"closed elapsed changed");denied(()->r.receive(hb(23)),"late rx");});
        test("N11_WRONG_PROVIDER_ZERO_SEND",()->{C c=new C();S s=new S();NativeSegments j=journal("foreign-provider",c,s);int[]send={0};denied(()->new RuntimeSession(new RunLifecycle.Context("foreign-provider","epoch01","boot01","operator01","generation01","qa-profile"),c,descriptor(),observed(H2),j,()->true,b->{send[0]++;},1800000000000L,false),"wrong provider");check(send[0]==0,"foreign dispatch");j.close();});
        System.out.println(Values.json(Values.map("format","aeris-independent-native-adapter-qa","results",results,"scope","PURE_JVM_NO_ANDROID_OR_SOCKET_RUNTIME")));
    }
}
