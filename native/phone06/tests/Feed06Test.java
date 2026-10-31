package vn.rtr.aeris.phone06;
import java.io.*;import java.nio.file.*;import java.util.*;
public final class Feed06Test{
 static final String C=String.join("",Collections.nCopies(64,"a"));
 static class S implements PhoneObserver06.Source{File f;boolean live=true;int calls=0,expireAt=999;S(Path p)throws Exception{f=p.toFile();Files.write(p,"COMMITTEDuncommitted".getBytes());}public PhoneObserver06.Prefix prefix()throws Exception{if(!live||++calls>=expireAt)throw new IOException("REVOKED");return new PhoneObserver06.Prefix(f,"run","gen","source",9,1,"head");}public String capability()throws Exception{if(!live)throw new IOException("REVOKED");return C;}public long now(){return 1;}}
 static void check(boolean b)throws Exception{if(!b)throw new IOException("ASSERT");}interface W{void run()throws Exception;}static void reject(W w)throws Exception{try{w.run();}catch(IOException e){return;}throw new IOException("EXPECTED_REJECTION");}
 public static void main(String[]a)throws Exception{Path root=Paths.get(a[0]);Files.createDirectory(root);
 S s=new S(root.resolve("wal"));PhoneObserver06 f=new PhoneObserver06(s);f.fixtureOpen06();try{Map<String,Object>r=f.readFixture06("Bearer "+C,"run","gen","source",0);check(new String(Base64.getDecoder().decode((String)r.get("dataBase64"))).equals("COMMITTED"));check(((Number)r.get("nextOffset")).longValue()==9);System.out.println("PASS F30_EXACT_COMMITTED_PREFIX_NO_NETWORK");
 reject(()->f.readFixture06("Bearer bad","run","gen","source",0));reject(()->f.readFixture06("Bearer "+C,"run","gen","source",10));reject(()->f.readFixture06("Bearer "+C,"other","gen","source",0));System.out.println("PASS F31_CAPABILITY_CONTEXT_OFFSET_NO_NETWORK");
 s.expireAt=s.calls+2;reject(()->f.readFixture06("Bearer "+C,"run","gen","source",0));s.expireAt=999;f.close();reject(()->f.readFixture06("Bearer "+C,"run","gen","source",0));System.out.println("PASS F32_REVOKED_DURING_READ_AND_EXPLICIT_STOP_NO_NETWORK");}finally{f.destroy();}}
}
