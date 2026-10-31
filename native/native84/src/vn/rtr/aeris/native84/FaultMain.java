package vn.rtr.aeris.native84;
import java.nio.file.*;import java.nio.charset.StandardCharsets;
/** Owned host-only death probe; not an Activity/Android acceptance. */
public final class FaultMain {public static void main(String[] a)throws Exception{DraftStore s=new DraftStore(Paths.get(a[0]),point->{if(point.equals(a[2])){Files.write(Paths.get(a[3]),point.getBytes(StandardCharsets.UTF_8),StandardOpenOption.CREATE_NEW);try{Thread.sleep(60000);}catch(InterruptedException e){throw new java.io.IOException(e);}}});DraftStore.Snapshot v=s.save(a[1],JournalMain.input());System.out.println(JournalMain.json(v,s.pending()));}}
