package vn.rtr.aeris.native79;
import java.nio.file.*;import java.nio.charset.StandardCharsets;import android.os.Build;import android.os.Process;
/** Actual ART shell execution, not installed Activity/application sandbox acceptance. */
public final class AndroidProbe {
 public static void main(String[] a)throws Exception{System.out.println("ANDROID_RUNTIME API="+Build.VERSION.SDK_INT+" ABI="+Build.SUPPORTED_ABIS[0]+" PID="+Process.myPid()+" UID="+Process.myUid());
 if(a[0].equals("test")){DraftStoreTest.main(new String[]{a[1]});return;}
 if(a[0].equals("crash")){DraftStore s=new DraftStore(Paths.get(a[1]),phase->{if(phase.equals(a[3])){Files.write(Paths.get(a[4]),(Process.myPid()+"\n"+phase).getBytes(StandardCharsets.UTF_8),StandardOpenOption.CREATE_NEW);System.out.println("WAITING_FOR_OWNED_SIGKILL "+phase+" PID="+Process.myPid());System.out.flush();try{Thread.sleep(120000);}catch(InterruptedException e){throw new java.io.IOException(e);}}});s.save(a[2],JournalMain.input());return;}
 throw new IllegalArgumentException("Probe command whitelist");}
}
