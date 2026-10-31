import java.io.*;import java.nio.file.*;import java.util.*;import vn.rtr.aeris.cockpit03.*;import vn.rtr.aeris.beta01runtime.*;
public class WorkspaceBuilderQA{
 static int pass;static void check(boolean b){if(!b)throw new AssertionError();pass++;}static void reject(RunnableE r)throws Exception{try{r.run();throw new AssertionError("accepted");}catch(IOException good){pass++;}}interface RunnableE{void run()throws Exception;}
 static class Sync implements NativeSegments.Sync{int dirs;int fail=-1;public void file(FileDescriptor f)throws IOException{f.sync();}public void directory(File d)throws IOException{if(++dirs==fail)throw new IOException("INJECT_DIR_SYNC");}}
 public static void main(String[]args)throws Exception{File parent=new File(args[0]);parent.mkdirs();Sync sync=new Sync();File dir=new File(parent,"workspace");WorkspaceStore s=new WorkspaceStore(dir,sync);byte[]d=Values.bytes(Values.map("revision",1,"name","Đường dây"));String sha=s.saveDraft(0,d);check(s.revision()==1&&s.latestDraft().getName().contains(sha));reject(()->s.saveDraft(0,d));check(new WorkspaceStore(dir,sync).revision()==1);s.saveReview("alpha-beta","{}".getBytes());s.saveReview("alpha","{\"a\":1}".getBytes());check(s.scan().size()==3);reject(()->s.saveReview("alpha","{\"a\":2}".getBytes()));
 File f=s.latestDraft();Files.write(f.toPath(),new byte[]{1});reject(()->new WorkspaceStore(dir,sync));
 Sync fail=new Sync();File fault=new File(parent,"fault");WorkspaceStore fs=new WorkspaceStore(fault,fail);fail.fail=fail.dirs+2;reject(()->fs.saveDraft(0,d));check(Arrays.stream(fault.list()).anyMatch(n->n.endsWith(".commit.pending")));reject(()->new WorkspaceStore(fault,new Sync()));
 File link=new File(parent,"symlink");Files.createSymbolicLink(link.toPath(),fault.toPath());reject(()->new WorkspaceStore(link,new Sync()));
 BridgeGate gate=new BridgeGate(7);gate.accept("ui-7-1",7,"LOAD",24);check(true);reject(()->gate.accept("ui-7-1",7,"LOAD",24));reject(()->gate.accept("ui-7-2",8,"STATE",24));reject(()->gate.accept("ui-7-3",7,"ARM",24));gate.accept("ui-7-999",7,"STATE",24);check(true);gate.close();reject(()->gate.accept("ui-7-1000",7,"LOAD",24));System.out.println("PASS "+pass);
 }
}
