package vn.rtr.aeris.native79qa3;
import android.app.Instrumentation;import android.os.Bundle;import android.os.Process;import java.io.*;import java.nio.file.*;import java.nio.charset.StandardCharsets;
/** Development-only actual app sandbox journal probe, no UI/flight authority. */
public final class JournalInstrumentation extends Instrumentation {
 @Override public void onCreate(Bundle args){super.onCreate(args);start();}
 @Override public void onStart(){Bundle result=new Bundle();try{File original=getTargetContext().getFilesDir();File dir=original.getCanonicalFile();result.putString("originalFilesDir",original.toString());result.putString("filesDir",dir.toString());result.putString("uid",String.valueOf(Process.myUid()));DraftStore s=new DraftStore(new File(dir,"instrumentation79").toPath());DraftStore.Snapshot a=s.save("ROOT","app-domain".getBytes(StandardCharsets.UTF_8));DraftStore.Snapshot b=new DraftStore(new File(dir,"instrumentation79").toPath()).load();if(!a.token.equals(b.token))throw new IOException("Committed token mismatch");result.putString("status","PASS_APP_DOMAIN_SAVE_LOAD");finish(-1,result);}catch(Exception e){result.putString("status","FAIL");result.putString("error",e.toString());android.util.Log.e("NATIVE79","APP_DOMAIN_PROBE",e);finish(0,result);}}
}
