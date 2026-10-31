package vn.rtr.aeris.shell30;
import java.nio.file.*;import java.nio.charset.StandardCharsets;
/** Test-only controlled crash point; parent owns/kills this JVM, never another process. */
public final class CrashMain {public static void main(String[] a)throws Exception{DraftStore s=new DraftStore(Paths.get(a[0]),phase->{if(phase.equals(a[2])){Files.write(Paths.get(a[3]),phase.getBytes(StandardCharsets.UTF_8),StandardOpenOption.CREATE_NEW);try{Thread.sleep(120000);}catch(InterruptedException e){throw new java.io.IOException(e);}}});s.save(a[1],JournalMain.input());}}
