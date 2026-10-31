package vn.rtr.aeris.diagnostic;
import java.util.*;
/** Explicit synthetic replay for cross-language contract tests. Never Android observations. */
public final class CaptureSessionFixture {
 public static void main(String[] args){CaptureSession s=new CaptureSession();s.lifecycle("create",10);s.lifecycle("resume",20);s.capture(true,30);s.raw("axis",40,CaptureSession.map("deviceId",1,"source",0x1000010,"axes",Arrays.asList(CaptureSession.map("axis",0,"value",.25))));s.lifecycle("focus-lost",50);
 List<Map<String,Object>> obs=Arrays.asList(CaptureSession.map("id","build","source","android.os.Build","status","observed","atElapsedMs",60,"value",CaptureSession.map("manufacturer","HOST FIXTURE","model","REPLAY / NOT DEVICE","hardware","fixture","osRelease","13","api",33,"buildFingerprint","REPLAY","abis",Arrays.asList("arm64-v8a"))),CaptureSession.map("id","window","source","android.view.Window","status","observed","atElapsedMs",60,"value",CaptureSession.map("widthPx",1280,"heightPx",800,"densityDpi",160,"density",1,"rotation",0,"insetsPx",CaptureSession.map("left",0,"top",24,"right",0,"bottom",24))),CaptureSession.map("id","inputs","source","android.view.InputDevice","status","unknown","atElapsedMs",60,"value",null),CaptureSession.map("id","codecs","source","android.media.MediaCodecList","status","unknown","atElapsedMs",60,"value",null));
 Map<String,Object> r=s.report("2026-10-12T06:00:00.000Z","emulator","HOST REPLAY ONLY","fixture",args[0],obs);r.put("context","replay");r.put("elapsedAtExport",1000);System.out.println(CaptureSession.json(r));}
}
