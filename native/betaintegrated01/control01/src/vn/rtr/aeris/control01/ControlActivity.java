package vn.rtr.aeris.control01;
import android.app.*;
import android.os.*;
import android.content.*;
import android.content.pm.*;
import android.graphics.*;
import android.view.*;
import android.widget.*;
import android.webkit.WebView;
import android.media.*;
import android.opengl.*;
import android.system.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import org.json.*;
import vn.rtr.aeris.betaintegrated01.RunLifecycle;
import vn.rtr.aeris.beta01runtime.NativeSegments;
import vn.rtr.aeris.beta01runtime.Values;
import vn.rtr.aeris.beta01runtime.PendingExplicitAction;

/** Explicit emulator training controls. Not final cockpit, HID calibration or real aircraft. */
public final class ControlActivity extends Activity {
    private volatile boolean foreground;private boolean everFocused,sampling,pendingUI;
    private final Handler handler=new Handler(Looper.getMainLooper());
    private final PendingExplicitAction<Intent> pendingActions=new PendingExplicitAction<>(2000000000L,16);
    private ControlOwner owner;private ControlConfig config;private TouchControls controls;
    private TextView status,home;private final Map<String,Button>buttons=new LinkedHashMap<>();
    private String last="{\"phase\":\"NO_SESSION\",\"authorityRestorable\":false}",displayedHomeHash,displayedRun;
    private final NativeSegments.Sync sync=new NativeSegments.Sync(){public void file(FileDescriptor fd)throws IOException{fd.sync();}public void directory(File dir)throws IOException{FileDescriptor fd=null;try{fd=Os.open(dir.getAbsolutePath(),OsConstants.O_RDONLY,0);if(!OsConstants.S_ISDIR(Os.fstat(fd).st_mode))throw new IOException("DIRECTORY_TYPE");Os.fsync(fd);}catch(ErrnoException e){throw new IOException("DIRECTORY_FSYNC",e);}finally{if(fd!=null)try{Os.close(fd);}catch(ErrnoException e){throw new IOException("DIRECTORY_CLOSE",e);}}}};
    private final RunLifecycle.Clock clock=new RunLifecycle.Clock(){public long monotonicNs(){return SystemClock.elapsedRealtimeNanos();}public long wallUtcMs(){return System.currentTimeMillis();}};
    private final Runnable producer=new Runnable(){public void run(){if(!sampling)return;if(!foreground||!getWindow().getDecorView().hasWindowFocus()||owner==null||!owner.running()){stopProducer();return;}sampleNow();handler.postDelayed(this,50);}};
    @Override public void onCreate(Bundle saved){super.onCreate(saved);getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setPadding(16,12,16,12);root.setBackgroundColor(0xff10171d);
        TextView title=text("RtR  /  AERIS CONTROL01 · Native sticks + assisted flight",22,Color.WHITE);root.addView(title);
        root.addView(text("Owned emulator / external SITL · LOITER is AP-assisted pilot control · No physical controller or real aircraft",13,Color.LTGRAY));
        String[][]rows={{"CONNECT","CONSENT","GUIDED","ARM","CONFIRM_HOME"},{"TAKEOFF","LOITER","HOLD","LAND","CLOSE"}};
        for(String[]row:rows){LinearLayout bar=new LinearLayout(this);for(String action:row){Button button=new Button(this);button.setText(label(action));button.setTextSize(14);button.setContentDescription("control01-"+action.toLowerCase(Locale.ROOT).replace('_','-'));button.setOnClickListener(v->operator(action));bar.addView(button,new LinearLayout.LayoutParams(0,52,1));buttons.put(action,button);}root.addView(bar);}
        home=text("Home: chưa có quan sát. Duyệt lại Home sau ARM trước TAKEOFF.",13,Color.LTGRAY);home.setContentDescription("control01-displayed-home");root.addView(home,new LinearLayout.LayoutParams(-1,68));
        controls=new TouchControls(this,new TouchControls.Sink(){public void motion(Map<String,Object>raw){if(owner!=null&&owner.running())owner.motion(raw);}public void released(){stopProducer();sampleNow();}public void invalid(String reason){stopProducer();if(owner!=null)owner.close("INVALID_TOUCH_EVENT");error(new IOException(reason));}});
        LinearLayout pads=new LinearLayout(this);pads.addView(controls.left,new LinearLayout.LayoutParams(0,-1,1));pads.addView(controls.right,new LinearLayout.LayoutParams(0,-1,1));root.addView(pads,new LinearLayout.LayoutParams(-1,0,1));
        ScrollView scroll=new ScrollView(this);status=text(last,13,Color.WHITE);status.setTypeface(Typeface.MONOSPACE);status.setContentDescription("control01-status");scroll.addView(status);root.addView(scroll,new LinearLayout.LayoutParams(-1,150));setContentView(root);disableFlightButtons();
        if(saved==null)queueExplicit(getIntent());root.post(()->{try{writeProbe();}catch(Exception e){error(e);}});
    }
    private TextView text(String value,int size,int color){TextView t=new TextView(this);t.setText(value);t.setTextSize(size);t.setTextColor(color);return t;}
    private String label(String action){switch(action){case"CONNECT":return"Kết nối";case"CONSENT":return"Nhận quyền";case"CONFIRM_HOME":return"Duyệt Home";case"TAKEOFF":return"Cất cánh 3 m";case"HOLD":return"HOLD / Release";case"LAND":return"Hạ cánh";case"CLOSE":return"Đóng phiên";default:return action;}}
    private void disableFlightButtons(){for(Map.Entry<String,Button>e:buttons.entrySet())e.getValue().setEnabled(e.getKey().equals("CONNECT")||e.getKey().equals("CLOSE"));}
    @Override protected void onResume(){super.onResume();foreground=true;}
    @Override protected void onPostResume(){super.onPostResume();getWindow().getDecorView().post(this::drainExplicit);}
    @Override protected void onPause(){foreground=false;stopProducer();pendingActions.cancel("ACTIVITY_PAUSED");if(owner!=null)owner.close("ACTIVITY_PAUSED");super.onPause();}
    @Override protected void onDestroy(){stopProducer();pendingActions.cancel("ACTIVITY_DESTROYED");if(owner!=null)owner.close("ACTIVITY_DESTROYED");super.onDestroy();}
    @Override public void onWindowFocusChanged(boolean focused){super.onWindowFocusChanged(focused);if(focused)everFocused=true;else if(everFocused){stopProducer();if(owner!=null)owner.close("WINDOW_FOCUS_LOST");}}
    @Override protected void onNewIntent(Intent intent){super.onNewIntent(intent);setIntent(intent);queueExplicit(intent);}
    private void queueExplicit(Intent intent){String action=intent.getStringExtra("m1Action");if(action==null)return;if(!Arrays.asList("CONNECT","CLOSE","STATUS").contains(action)){error(new IOException("ACTIVE_FLIGHT_REQUIRES_OBSERVED_UI_TOUCH"));return;}if((intent.getFlags()&Intent.FLAG_ACTIVITY_LAUNCHED_FROM_HISTORY)!=0){pendingActions.cancel("HISTORY");return;}try{long n=SystemClock.elapsedRealtimeNanos();pendingActions.enqueue(intent.getStringExtra("m1ActionId"),action,new Intent(intent),n);android.util.Log.i("AERIS_CONTROL_INTENT","QUEUED "+action+" foreground="+foreground+" atNs="+n);}catch(Exception e){error(e);}}
    private void drainExplicit(){try{PendingExplicitAction.Ticket<Intent> ticket=pendingActions.consume(SystemClock.elapsedRealtimeNanos(),foreground);if(ticket==null)return;android.util.Log.i("AERIS_CONTROL_INTENT","CONSUMED "+ticket.action+" foreground="+foreground+" atNs="+SystemClock.elapsedRealtimeNanos());if("CONNECT".equals(ticket.action))connect(ticket.payload);else operator(ticket.action);}catch(Exception e){error(e);}}
    private void connect(Intent intent)throws Exception{
        if(!foreground||owner!=null&&owner.running()||!"ranchu".equals(Build.HARDWARE))throw new IOException("OWNED_RESUMED_EMULATOR_NO_ACTIVE_OWNER_REQUIRED");
        byte[] expected;try(InputStream in=getAssets().open("expected-providers.json")){expected=readBounded(in,65536);}byte[] observed=readBounded(new File(getFilesDir(),"launch-binding.json"),65536);
        config=new ControlConfig(expected,observed,intent.getStringExtra("launchBindingSHA256"),name->{try(InputStream in=getAssets().open(name)){return readBounded(in,65536);}});
        if(!writeProbe())throw new IOException("ACTUAL_MINIMAL_ANDROID_PROFILE_NOT_OBSERVED");
        ControlOwner next=new ControlOwner(getFilesDir(),config,clock,sync,()->foreground,this::update,controls.source);owner=next;next.start();
    }
    private void sampleNow(){if(config!=null&&owner!=null&&owner.running()&&foreground&&getWindow().getDecorView().hasWindowFocus())owner.input(controls.sample(config.context,config.provenance));}
    private void startProducer(){if(sampling)return;sampling=true;handler.post(producer);}
    private void stopProducer(){sampling=false;handler.removeCallbacks(producer);}
    private void operator(String action){try{
        if("STATUS".equals(action)){status.setText(last);return;}
        if("CONNECT".equals(action)){connect(getIntent());return;}
        if("CLOSE".equals(action)){stopProducer();if(owner!=null)owner.close("EXPLICIT_OPERATOR_CLOSE");return;}
        if(!foreground||!getWindow().getDecorView().hasWindowFocus()||owner==null||!owner.running())throw new IOException("FOCUSED_ACTIVE_NATIVE_OWNER_REQUIRED");
        if("CONFIRM_HOME".equals(action)&&(!Objects.equals(displayedRun,config.context.run)||displayedHomeHash==null))throw new IOException("DISPLAYED_CURRENT_RUN_HOME_REQUIRED");
        sampleNow();long at=SystemClock.elapsedRealtimeNanos();owner.action(action,"touch-action-"+UUID.randomUUID(),displayedHomeHash,at);if("CONSENT".equals(action))startProducer();
    }catch(Exception e){error(e);}}
    private void error(Exception e){status.setText("REFUSED: "+e.getMessage()+"\nNo implicit permission or retry.");}
    private synchronized void update(String identity,String value){if(!ControlOwner.latest(identity))return;last=value;try{writeCheckpoint(value);}catch(Exception e){if(owner!=null)owner.close("CHECKPOINT_FAILURE");}if(pendingUI)return;pendingUI=true;runOnUiThread(()->{synchronized(ControlActivity.this){pendingUI=false;render(last);}});}
    private void render(String value){try{JSONObject s=new JSONObject(value),f=s.optJSONObject("flight"),a=s.optJSONObject("input");if(f==null){status.setText(value);disableFlightButtons();return;}displayedHomeHash=f.optString("homeHash",null);displayedRun=s.optString("run",null);home.setText("Trước ARM: "+f.opt("preArmHome")+"\nHome hiện tại: "+f.opt("home")+"\nSHA đã hiển thị: "+displayedHomeHash+"  |  "+(f.optBoolean("homeConfirmed")?"CONFIRMED":"CONFIRM REQUIRED AFTER ARM"));
        boolean opened=!s.optBoolean("closed")&&!s.has("firstFailure")||!s.optBoolean("closed")&&s.isNull("firstFailure");boolean ready=s.optBoolean("preflightReady"),consent=a!=null&&a.optBoolean("consent"),armed=f.optBoolean("armed"),confirmed=f.optBoolean("homeConfirmed");int mode=f.optInt("mode",-1),landed=f.optInt("landedState",-1);
        buttons.get("CONSENT").setEnabled(opened&&ready&&!consent&&!"WAIT_HOLD".equals(s.optString("releaseState")));buttons.get("GUIDED").setEnabled(opened&&consent&&!armed);buttons.get("ARM").setEnabled(opened&&consent&&!armed&&mode==4&&ready);buttons.get("CONFIRM_HOME").setEnabled(opened&&consent&&armed&&f.optBoolean("postArmHomePending")&&f.optLong("homeObservedAtMs")>f.optLong("armObservedAtMs"));buttons.get("TAKEOFF").setEnabled(opened&&consent&&armed&&landed==1&&confirmed);buttons.get("LOITER").setEnabled(opened&&consent&&armed&&mode==4&&landed==2&&f.optLong("hoverObservedMs")>=1000);buttons.get("HOLD").setEnabled(opened&&consent&&armed&&landed==2);buttons.get("LAND").setEnabled(opened&&consent&&armed&&!s.optBoolean("rcOverrideActiveLocally"));
        status.setText("Preflight: "+(ready?"READY":s.optString("preflightReason"))+"\nMode="+mode+" armed="+armed+" landed="+landed+" altitude="+f.optDouble("relativeAltitudeM")+"m horizontal="+f.optDouble("horizontalSpeedMps")+"m/s battery="+f.optInt("batteryWireMillivolts")+"mV\nHomeconfirmed="+confirmed+" hoverObserved="+f.optLong("hoverObservedMs")+"ms | Input="+a+"\nRelease="+s.optString("releaseState")+" | Failure="+s.opt("firstFailure"));
        if(s.optBoolean("closed")||!opened)stopProducer();
    }catch(Exception e){status.setText(value);}}
    private synchronized void writeCheckpoint(String value)throws Exception{byte[]b=value.getBytes(StandardCharsets.UTF_8);if(b.length>65536)throw new IOException("CHECKPOINT_BOUND");File next=new File(getFilesDir(),"latest-state.pending"),dest=new File(getFilesDir(),"latest-state.json");try(FileOutputStream out=new FileOutputStream(next)){out.write(b);sync.file(out.getFD());}if(!next.renameTo(dest))throw new IOException("CHECKPOINT_RENAME");sync.directory(getFilesDir());}
    private static byte[]readBounded(File file,int max)throws Exception{try(InputStream in=new FileInputStream(file)){return readBounded(in,max);}}
    private static byte[]readBounded(InputStream in,int max)throws Exception{ByteArrayOutputStream out=new ByteArrayOutputStream();byte[]b=new byte[4096];for(int n;(n=in.read(b))>=0;){if(out.size()+n>max)throw new IOException("INPUT_BOUND");out.write(b,0,n);}return out.toByteArray();}
    private boolean writeProbe()throws Exception {
        PackageInfo own=getPackageManager().getPackageInfo(getPackageName(),0),web=WebView.getCurrentWebViewPackage();
        Map<String,Object> p=Values.map("format","aeris-control01-android-probe","version",1,"atUTCms",System.currentTimeMillis(),"API",Build.VERSION.SDK_INT,"ABI",Arrays.asList(Build.SUPPORTED_ABIS),"fingerprint",Build.FINGERPRINT,"hardware",Build.HARDWARE,"package",getPackageName(),"versionName",own.versionName,"versionCode",own.versionCode,"webViewPackage",web==null?null:web.packageName,"webViewVersion",web==null?null:web.versionName,"widthPx",getWindow().getDecorView().getWidth(),"heightPx",getWindow().getDecorView().getHeight(),"densityDpi",getResources().getDisplayMetrics().densityDpi,"fontScale",getResources().getConfiguration().fontScale,"capabilityProfile","M1_CONTROL01_NO_MEDIA","decoderBackend","NOT_STARTED_NOT_OBSERVED","fullBetaProfileAccepted",false);
        WindowInsets insets=getWindow().getDecorView().getRootWindowInsets();p.put("insets",insets==null?null:Values.map("left",insets.getSystemWindowInsetLeft(),"top",insets.getSystemWindowInsetTop(),"right",insets.getSystemWindowInsetRight(),"bottom",insets.getSystemWindowInsetBottom()));
        ArrayList<String> codecs=new ArrayList<>();for(MediaCodecInfo info:new MediaCodecList(MediaCodecList.ALL_CODECS).getCodecInfos())if(!info.isEncoder()&&codecs.size()<128)codecs.add(info.getName());p.put("availableDecodersNotActualBackend",codecs);Map<String,Object> gpu=gpu();p.put("GPU",gpu);
        byte[] data=Values.bytes(p);File f=new File(getFilesDir(),"probe-"+System.currentTimeMillis()+".json");if(!f.createNewFile())throw new IOException("EXCLUSIVE_PROBE");try(FileOutputStream out=new FileOutputStream(f)){out.write(data);sync.file(out.getFD());}sync.directory(getFilesDir());return Build.VERSION.SDK_INT==33&&Arrays.asList(Build.SUPPORTED_ABIS).contains("arm64-v8a")&&web!=null&&"ranchu".equals(Build.HARDWARE)&&"OBSERVED_GLES_PBUFFER".equals(gpu.get("status"))&&getWindow().getDecorView().getWidth()>=1000&&getWindow().getDecorView().getHeight()>=600;
    }
    private Map<String,Object> gpu(){
        EGLDisplay d=EGL14.eglGetDisplay(EGL14.EGL_DEFAULT_DISPLAY);EGLContext c=EGL14.EGL_NO_CONTEXT;EGLSurface s=EGL14.EGL_NO_SURFACE;
        try{int[]v=new int[2];if(!EGL14.eglInitialize(d,v,0,v,1))throw new IOException("EGL_INIT");EGLConfig[]configs=new EGLConfig[1];int[]n=new int[1];int[]attrs={EGL14.EGL_RENDERABLE_TYPE,EGL14.EGL_OPENGL_ES2_BIT,EGL14.EGL_SURFACE_TYPE,EGL14.EGL_PBUFFER_BIT,EGL14.EGL_NONE};if(!EGL14.eglChooseConfig(d,attrs,0,configs,0,1,n,0)||n[0]<1)throw new IOException("EGL_CONFIG");c=EGL14.eglCreateContext(d,configs[0],EGL14.EGL_NO_CONTEXT,new int[]{EGL14.EGL_CONTEXT_CLIENT_VERSION,2,EGL14.EGL_NONE},0);s=EGL14.eglCreatePbufferSurface(d,configs[0],new int[]{EGL14.EGL_WIDTH,1,EGL14.EGL_HEIGHT,1,EGL14.EGL_NONE},0);if(!EGL14.eglMakeCurrent(d,s,s,c))throw new IOException("EGL_MAKE_CURRENT");return Values.map("status","OBSERVED_GLES_PBUFFER","renderer",GLES20.glGetString(GLES20.GL_RENDERER),"vendor",GLES20.glGetString(GLES20.GL_VENDOR),"version",GLES20.glGetString(GLES20.GL_VERSION));}
        catch(Exception e){return Values.map("status","NOT_OBSERVED","reason",String.valueOf(e.getMessage()));}
        finally{EGL14.eglMakeCurrent(d,EGL14.EGL_NO_SURFACE,EGL14.EGL_NO_SURFACE,EGL14.EGL_NO_CONTEXT);if(s!=EGL14.EGL_NO_SURFACE)EGL14.eglDestroySurface(d,s);if(c!=EGL14.EGL_NO_CONTEXT)EGL14.eglDestroyContext(d,c);EGL14.eglTerminate(d);}
    }
}
