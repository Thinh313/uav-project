import java.io.*;import java.lang.reflect.*;import java.nio.*;import java.nio.channels.*;import java.nio.file.*;import java.util.*;import java.util.concurrent.atomic.*;
import vn.rtr.aeris.control01.*;import vn.rtr.aeris.betaintegrated01.*;import vn.rtr.aeris.beta01runtime.*;import vn.rtr.aeris.native98.Dialect95;
public final class OwnerCloseQA {
 static List<Map<String,Object>>results=new ArrayList<>();static File root;interface Op{void run()throws Exception;}
 static void check(boolean b,String s){if(!b)throw new AssertionError(s);}static void test(String id,Op o){try{o.run();results.add(Values.map("id",id,"pass",true));}catch(Throwable e){results.add(Values.map("id",id,"pass",false,"error",e.toString()));}}
 static String lines(File root)throws Exception{StringBuilder b=new StringBuilder();try(java.util.stream.Stream<Path>s=Files.walk(root.toPath())){s.filter(p->p.toString().endsWith(".jsonl")).sorted().forEach(p->{try{b.append(new String(Files.readAllBytes(p),"UTF-8"));}catch(Exception e){throw new RuntimeException(e);}});}return b.toString();}
 static class F {
  final File files;final AtomicBoolean fg=new AtomicBoolean(true),trigger=new AtomicBoolean();final ControlOwner[]owner=new ControlOwner[1];final Fake connection=new Fake();final String scenario;String state;
  F(String scenario)throws Exception{this.scenario=scenario;files=new File(root,scenario);check(files.mkdir(),"exclusivecase");}
  class Fake implements ControlOwner.Connection {
   volatile boolean closed;int writes,reads;
   public InputStream input(){return new InputStream(){public int read(){return-1;}public int read(byte[]b)throws IOException{reads++;
    if(scenario.equals("read-close")){owner[0].close("EXPLICIT_OPERATOR_CLOSE");}
    if(scenario.equals("read-error")){owner[0].close("EXPLICIT_OPERATOR_CLOSE");throw new IOException("QA_CONNECTION_RESET");}
    byte[]p=new byte[Dialect95.D.get(0)[1]];ByteBuffer.wrap(p).order(ByteOrder.LITTLE_ENDIAN).putInt(0,0);p[4]=2;p[5]=3;p[7]=4;p[8]=3;byte[]w=Mavlink.packet(0,p,1);w[5]=42;w[6]=1;int n=w[1]&255,c=Mavlink.crc(w,10+n,Dialect95.D.get(0)[2]);w[10+n]=(byte)c;w[11+n]=(byte)(c>>8);System.arraycopy(w,0,b,0,w.length);return w.length;}};}
   public OutputStream output(){return new OutputStream(){public void write(int b){}public void write(byte[]b)throws IOException{writes++;
    if(scenario.equals("write-close")||scenario.equals("write-error")||scenario.equals("late-input")){owner[0].close("EXPLICIT_OPERATOR_CLOSE");
     if(scenario.equals("late-input"))owner[0].input(new ControlAuthority.Input(new ControlConfig(scenario,ProfileFixture.specs()).context,"touch-11111111-1111-1111-1111-111111111111","ANDROID_UPTIME_NS_SAMPLER","ROOT_INJECTED_ANDROID_TOUCH",1,900000000,1000000000,0,new double[4],0,-1,false));
     if(scenario.equals("write-error"))throw new IOException("QA_WRITE_FAILED");
    }
   }};}
   public boolean isClosed(){return closed;}public void close(){closed=true;}
  }
  void run()throws Exception{
   RunLifecycle.Clock clock=new RunLifecycle.Clock(){public long monotonicNs(){return 1000000000L;}public long wallUtcMs(){return 1700000001000L;}};
   NativeSegments.Sync sync=new NativeSegments.Sync(){public void file(FileDescriptor fd)throws IOException{fd.sync();if((scenario.equals("rx-fsync-close")||scenario.equals("background-rx"))&&!trigger.get())try{if(lines(files).contains("\"kind\":\"RX\"")){trigger.set(true);if(scenario.equals("background-rx")){fg.set(false);owner[0].close("ACTIVITY_PAUSED");}else owner[0].close("EXPLICIT_OPERATOR_CLOSE");}}catch(Exception e){throw new IOException(e);}}public void directory(File p)throws IOException{try(FileChannel c=FileChannel.open(p.toPath(),StandardOpenOption.READ)){c.force(true);}}};
   owner[0]=new ControlOwner(files,new ControlConfig(scenario,ProfileFixture.specs()),clock,sync,fg::get,(id,s)->state=s,"touch-11111111-1111-1111-1111-111111111111",()->connection);owner[0].start();Field field=ControlOwner.class.getDeclaredField("thread");field.setAccessible(true);Thread thread=(Thread)field.get(owner[0]);thread.join(5000);check(!thread.isAlive(),"ownedloopdidnotclose");check(connection.closed,"connectionnotclosed");check(state!=null&&state.contains("\"closed\":true"),"nosessionclosedstate");
   boolean failure=scenario.equals("read-error")||scenario.equals("write-error")||scenario.equals("background-rx");check(state.contains("\"firstFailure\":null")!=failure,"wrongfailureclassification:"+state);
   String raw=lines(files);check(raw.contains("\"kind\":\"OPERATOR_CLOSE_REQUEST\"")!=failure,"wrongintentionalcloseevent");
   if(scenario.equals("write-error"))check(raw.contains("\"kind\":\"TX_UNKNOWN\""),"unknownsendlost");
   if(scenario.equals("late-input"))check(!raw.contains("\"kind\":\"CONTROL_INPUT\""),"lateinputadmitted");
   if(!failure)check(state.contains("\"phase\":\"SEALED\"")&&state.contains("\"consent\":false"),"closureorleasewrong");
  }
 }
 public static void main(String[]args)throws Exception{root=new File(args[0]);check(root.mkdir(),"exclusivefixtures");for(String scenario:new String[]{"read-close","rx-fsync-close","write-close","late-input","read-error","write-error","background-rx"})test(scenario,()->new F(scenario).run());System.out.println(Values.json(Values.map("results",results,"scope","ACTUAL_OWNER03_IO_LOOP_REAL_FSYNC_FAKE_CONNECTION_NO_OS_SOCKET")));}
}
