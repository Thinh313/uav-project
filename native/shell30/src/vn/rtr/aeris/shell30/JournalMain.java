package vn.rtr.aeris.shell30;
import java.nio.file.*;import java.io.*;import java.util.Base64;
public final class JournalMain {
 public static String json(DraftStore.Snapshot s,boolean pending){return "{\"ok\":true,\"token\":\""+(s==null?"ROOT":s.token)+"\",\"revision\":"+(s==null?0:s.revision)+",\"pending\":"+pending+",\"bodyBase64\":\""+(s==null?"":Base64.getEncoder().encodeToString(s.bytes))+"\",\"authorityRestorable\":false}";}
 public static byte[] input()throws IOException{ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] b=new byte[4096];int n;while((n=System.in.read(b))!=-1){out.write(b,0,n);if(out.size()>DraftStore.MAX_BODY)throw new IOException("Input bound");}return out.toByteArray();}
 public static void main(String[] args)throws Exception{DraftStore s=new DraftStore(Paths.get(args[1]));DraftStore.Snapshot v;if(args[0].equals("load"))v=s.load();else if(args[0].equals("save"))v=s.save(args[2],input());else throw new IOException("Command whitelist");System.out.println(json(v,s.pending()));}
}
