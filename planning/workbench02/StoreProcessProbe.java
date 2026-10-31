package vn.rtr.aeris.workbench02;
import java.io.*;
/** Two separate host JVM processes; not ART or device power-loss evidence. */
public final class StoreProcessProbe {
 public static void main(String[] args)throws Exception {
  File root=new File(args[1]);String body="Khảo sát Hera • host process persistence only";
  WorkspaceStore s=new WorkspaceStore(root,d->{},p->{});
  if(args[0].equals("write")){if(!s.load().status.equals("EMPTY"))throw new IOException("FRESH_STORE_REQUIRED");WorkspaceStore.Snapshot x=s.save("ROOT",body);System.out.println("WRITE "+x.head+" "+x.sha);}
  else if(args[0].equals("read")){WorkspaceStore.Snapshot x=s.load();if(!body.equals(x.body)||x.sequence!=1||!WorkspaceStore.sha(body.getBytes("UTF-8")).equals(x.sha))throw new IOException("PROCESS_RESTART_MISMATCH");System.out.println("READ "+x.head+" "+x.sha);}
  else throw new IOException("ACTION");
 }
}
