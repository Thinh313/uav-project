package vn.rtr.aeris.beta01runtime;
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
import vn.rtr.aeris.betaintegrated01.RunLifecycle;

/** Diagnostic runtime shell only. This is not the final cockpit or a physical provider. */
public final class RuntimeActivity extends Activity {
    private volatile boolean foreground;private SocketOwner owner;private TextView status;private boolean pendingUI;
    private String last="{\"phase\":\"NO_SESSION\",\"authorityRestorable\":false}";
    private final NativeSegments.Sync sync=new NativeSegments.Sync(){
        public void file(FileDescriptor fd)throws IOException{fd.sync();}
        public void directory(File dir)throws IOException{FileDescriptor fd=null;try{fd=Os.open(dir.getAbsolutePath(),OsConstants.O_RDONLY,0);if(!OsConstants.S_ISDIR(Os.fstat(fd).st_mode))throw new IOException("DIRECTORY_FSYNC_TYPE");Os.fsync(fd);}catch(ErrnoException e){throw new IOException("DIRECTORY_FSYNC",e);}finally{if(fd!=null)try{Os.close(fd);}catch(ErrnoException e){throw new IOException("DIRECTORY_CLOSE",e);}}}
    };
    private final RunLifecycle.Clock clock=new RunLifecycle.Clock(){public long monotonicNs(){return SystemClock.elapsedRealtimeNanos();}public long wallUtcMs(){return System.currentTimeMillis();}};
    @Override public void onCreate(Bundle b){super.onCreate(b);getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setPadding(24,16,24,16);root.setBackgroundColor(Color.rgb(15,19,23));TextView title=new TextView(this);title.setText("RtR  /  AERIS M1 · Runtime chẩn đoán");title.setTextColor(Color.WHITE);title.setTextSize(22);root.addView(title);TextView subtitle=new TextView(this);subtitle.setText("Emulator · External SITL · Không phải cockpit cuối / không kết nối drone thật");subtitle.setTextColor(Color.LTGRAY);root.addView(subtitle);LinearLayout controls=new LinearLayout(this);for(String action:new String[]{"CONNECT","CLOSE","CONSENT","GUIDED","ARM","TAKEOFF","LAND"}){Button button=new Button(this);button.setText(action);button.setContentDescription("m1-"+action.toLowerCase(Locale.ROOT));button.setOnClickListener(v->action(action,getIntent()));controls.addView(button,new LinearLayout.LayoutParams(0,56,1));}root.addView(controls);ScrollView scroll=new ScrollView(this);status=new TextView(this);status.setTextColor(Color.WHITE);status.setTextSize(15);status.setTypeface(Typeface.MONOSPACE);status.setText(last);scroll.addView(status);root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));setContentView(root);root.post(()->{try{writeProbe();}catch(Exception e){error(e);}String a=getIntent().getStringExtra("m1Action");if(a!=null)action(a,getIntent());});}
    @Override protected void onResume(){super.onResume();foreground=true;}
    @Override protected void onPause(){foreground=false;if(owner!=null)owner.close("ACTIVITY_PAUSED");super.onPause();}
    @Override protected void onDestroy(){if(owner!=null)owner.close("ACTIVITY_DESTROYED");super.onDestroy();}
    @Override protected void onNewIntent(Intent intent){super.onNewIntent(intent);setIntent(intent);String a=intent.getStringExtra("m1Action");if(a!=null)action(a,intent);}
    private void error(Exception e){last=Values.json(Values.map("error",e.getClass().getSimpleName()+":"+e.getMessage(),"authorityRestorable",false));status.setText(last);try{writeCheckpoint(last);}catch(Exception ignored){}}
    private void action(String action,Intent intent){
        try {
            if("STATUS".equals(action)){status.setText(owner==null?last:owner.state());return;}
            if("CLOSE".equals(action)){if(owner!=null)owner.close("EXPLICIT_ROOT_OR_UI_CLOSE");return;}
            if(!"CONNECT".equals(action)){if(owner==null)throw new IOException("NO_NATIVE_OWNER");owner.action(action);return;}
            if(!foreground||owner!=null&&owner.isRunning()||!"ranchu".equals(Build.HARDWARE))throw new IOException("OWNED_EMULATOR_FOREGROUND_NO_ACTIVE_OWNER_REQUIRED");
            File binding=new File(getFilesDir(),"launch-binding.json");byte[] observed=readBounded(binding,65536);
            String expected;try(InputStream in=getAssets().open("expected-provider.json")){expected=new String(readBounded(in,65536),StandardCharsets.UTF_8);}
            RuntimeConfig config=new RuntimeConfig(expected,observed,intent.getStringExtra("launchBindingSHA256"));
            if(!writeProbe()&&config.manualCapability)throw new IOException("ACTUAL_M1_PROBE_REQUIRED_BEFORE_GRANT");owner=new SocketOwner(getFilesDir(),config,clock,sync,()->foreground,this::update);owner.start();
        }catch(Exception e){error(e);}
    }
    private synchronized void update(String value){last=value;try{writeCheckpoint(value);}catch(Exception e){if(owner!=null)owner.close("STATE_CHECKPOINT_FAILURE");}if(pendingUI)return;pendingUI=true;runOnUiThread(()->{synchronized(RuntimeActivity.this){pendingUI=false;status.setText(last);}});}
    private synchronized void writeCheckpoint(String value)throws Exception {
        byte[] b=value.getBytes(StandardCharsets.UTF_8);if(b.length>65536)throw new IOException("CHECKPOINT_BOUND");File next=new File(getFilesDir(),"latest-state.pending"),dest=new File(getFilesDir(),"latest-state.json");try(FileOutputStream out=new FileOutputStream(next)){out.write(b);sync.file(out.getFD());}if(!next.renameTo(dest))throw new IOException("CHECKPOINT_RENAME");sync.directory(getFilesDir());
    }
    private static byte[] readBounded(File file,int max)throws IOException{try(InputStream in=new FileInputStream(file)){return readBounded(in,max);}}
    private static byte[] readBounded(InputStream in,int max)throws IOException{ByteArrayOutputStream out=new ByteArrayOutputStream();byte[]b=new byte[4096];for(int n;(n=in.read(b))>=0;){if(out.size()+n>max)throw new IOException("INPUT_BYTES_BOUND");out.write(b,0,n);}return out.toByteArray();}
    private boolean writeProbe()throws Exception {
        PackageInfo own=getPackageManager().getPackageInfo(getPackageName(),0),web=WebView.getCurrentWebViewPackage();
        Map<String,Object> p=Values.map("format","aeris-m1-android-probe","version",1,"atUTCms",System.currentTimeMillis(),"API",Build.VERSION.SDK_INT,"ABI",Arrays.asList(Build.SUPPORTED_ABIS),"fingerprint",Build.FINGERPRINT,"hardware",Build.HARDWARE,"package",getPackageName(),"versionName",own.versionName,"versionCode",own.versionCode,"webViewPackage",web==null?null:web.packageName,"webViewVersion",web==null?null:web.versionName,"widthPx",getWindow().getDecorView().getWidth(),"heightPx",getWindow().getDecorView().getHeight(),"densityDpi",getResources().getDisplayMetrics().densityDpi,"fontScale",getResources().getConfiguration().fontScale,"capabilityProfile","NO_MEDIA_M1_RUNTIME","decoderBackend","NOT_STARTED_NOT_OBSERVED","fullBetaProfileAccepted",false);
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
