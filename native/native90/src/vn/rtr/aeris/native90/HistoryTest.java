package vn.rtr.aeris.native90;
import java.nio.file.*;import java.nio.charset.StandardCharsets;import java.io.*;import java.util.*;
public final class HistoryTest{
 static int n=0;static void ck(boolean x,String why){if(!x)throw new AssertionError(why);n++;}interface Op{void run()throws Exception;}static void refused(Op fn)throws Exception{try{fn.run();throw new AssertionError("Expected refusal");}catch(IOException e){n++;}}
 public static void main(String[] args)throws Exception{Path p=Paths.get(args[0]);DraftStore s=new DraftStore(p);ck(s.history(null).isEmpty(),"Empty list");DraftStore.Snapshot a=s.save("ROOT","one".getBytes(StandardCharsets.UTF_8)),b=s.save(a.token,"two".getBytes(StandardCharsets.UTF_8));ck(s.history(b.token).get(0).token.equals(b.token),"Newest first");ck(s.history(null).get(1).token.equals(a.token),"Old retained");ck(Arrays.equals(s.committed(b.token,a.token).bytes,a.bytes),"Exact old");refused(()->s.history(a.token));refused(()->s.committed(b.token,String.join("",Collections.nCopies(64,"a"))));DraftStore cold=new DraftStore(p);ck(cold.history(null).size()==2,"Restart");
  DraftStore fault=new DraftStore(p,x->{if(x.equals("RECORD_PUBLISHED"))throw new IOException("injected");});refused(()->fault.save(b.token,"orphan".getBytes(StandardCharsets.UTF_8)));ck(cold.history(null).size()==2,"Orphan not committed history");
  Files.write(p.resolve("HEAD.pending"),(b.token+"\n").getBytes(StandardCharsets.US_ASCII));refused(()->cold.history(null));Files.delete(p.resolve("HEAD.pending"));
  Path row=Files.list(p).filter(f->f.getFileName().toString().endsWith(a.token+".bin")).findFirst().get();byte[] raw=Files.readAllBytes(row);raw[raw.length-1]^=1;Files.write(row,raw);refused(()->cold.history(null));System.out.println("HISTORY_PASS "+n);
 }
}
