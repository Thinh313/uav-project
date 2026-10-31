package vn.rtr.aeris.native90;
import java.io.*;import java.nio.file.*;import java.nio.charset.StandardCharsets;import java.util.*;
public final class JournalTest89 {
 static int count=0;static void yes(boolean b){if(!b)throw new AssertionError();}interface Work{void run()throws Exception;}static void rejects(Work r)throws Exception{try{r.run();}catch(IOException e){count++;return;}throw new AssertionError("Expected IOException");}
 public static void main(String[] args)throws Exception{Path root=Paths.get(args[0]);Files.createDirectory(root);String id=UUID.randomUUID().toString();File dir=root.resolve("normal").toFile();BenchJournal89 a=new BenchJournal89(dir,id);String head=a.append("{\"kind\":\"SESSION\"}",0);yes(head.matches("[a-f0-9]{64}")&&a.count()==1);count++;rejects(()->new BenchJournal89(dir,UUID.randomUUID().toString()));a.append("{\"kind\":\"NORMAL\"}",1);byte[] before=Files.readAllBytes(a.file.toPath());a.close();rejects(()->a.append("{}",2));yes(Arrays.equals(before,Files.readAllBytes(a.file.toPath())));count++;rejects(()->new BenchJournal89(dir,id));
 try(BenchJournal89 b=new BenchJournal89(root.resolve("clock").toFile(),UUID.randomUUID().toString())){b.append("{}",10);rejects(()->b.append("{}",9));rejects(()->b.append("{}",11));yes(b.count()==1);count++;}
 try(BenchJournal89 b=new BenchJournal89(root.resolve("count").toFile(),UUID.randomUUID().toString())){for(int i=0;i<512;i++)b.append("{}",i);rejects(()->b.append("{}",513));yes(b.count()==512);count++;}
 Path target=root.resolve("target");Files.createDirectory(target);Path link=root.resolve("link");Files.createSymbolicLink(link,target);rejects(()->new BenchJournal89(link.toFile(),UUID.randomUUID().toString()));
 try(BenchJournal89 b=new BenchJournal89(root.resolve("payload").toFile(),UUID.randomUUID().toString())){rejects(()->b.append(new String(new char[17000]).replace('\0','x'),0));yes(b.count()==0);count++;}
 File quota=root.resolve("quota").toFile();quota.mkdir();try(RandomAccessFile f=new RandomAccessFile(new File(quota,"retained.bin"),"rw")){f.setLength(BenchJournal89.MAX_TOTAL);}rejects(()->new BenchJournal89(quota,UUID.randomUUID().toString()));yes(new File(quota,"retained.bin").length()==BenchJournal89.MAX_TOTAL);count++;
 System.out.println("{\"status\":\"PASS\",\"checks\":"+count+",\"scope\":\"HOST_JVM_STORAGE_NOT_ANDROID_POWERLOSS\"}");}
}
