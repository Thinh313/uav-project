package vn.rtr.aeris.cockpit66;
import android.app.Activity;import android.os.Bundle;import android.webkit.*;import android.net.Uri;import java.io.*;import java.util.*;
/** Offline mock source only: no SDK, native command bridge or runtime qualification. */
public final class ShellActivity extends Activity {
 private static final String HOST="cockpit66.aeris.invalid",PAGE="https://"+HOST+"/index.html";
 private static final Set<String> ASSETS=new HashSet<>(Arrays.asList("index.html","cockpit.css","ui.mjs","model.mjs","store.mjs","reference-reviews.json","compatibility.mjs","assets/Barlow-Bold.ttf","assets/Barlow-Medium.ttf","assets/Barlow-SemiBold.ttf","portable/sha256.mjs","portable/cyber65/authority.mjs","portable/cyber65/contracts.mjs","portable/cyber65/corpus.json","portable/cyber65/replay.mjs","portable/cyber65/session.mjs","portable/protocol22/definitions.mjs","portable/protocol22/session.mjs","portable/protocol22/wire.mjs","portable/transport25/broker.mjs","portable/transport25/config.mjs","portable/transport25/fixtures.mjs","portable/transport25/mock.mjs"));
 private WebView web;private boolean dead=false;
 @Override public void onCreate(Bundle state){super.onCreate(state);web=new WebView(this);setContentView(web);WebSettings s=web.getSettings();s.setJavaScriptEnabled(true);s.setDomStorageEnabled(true);s.setAllowFileAccess(false);s.setAllowContentAccess(false);s.setBlockNetworkLoads(true);s.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);s.setJavaScriptCanOpenWindowsAutomatically(false);s.setCacheMode(WebSettings.LOAD_NO_CACHE);web.setWebViewClient(new WebViewClient(){
  @Override public boolean shouldOverrideUrlLoading(WebView v,WebResourceRequest q){return !PAGE.equals(q.getUrl().toString());}
  @Override public WebResourceResponse shouldInterceptRequest(WebView v,WebResourceRequest q){try{Uri u=q.getUrl();String p=u.getPath();if(!"GET".equals(q.getMethod())||!"https".equals(u.getScheme())||!HOST.equals(u.getHost())||u.getPort()!=-1||u.getQuery()!=null||u.getFragment()!=null||p==null||!p.startsWith("/")||!ASSETS.contains(p.substring(1)))return refused();String type=p.endsWith(".ttf")?"font/ttf":p.endsWith(".css")?"text/css":p.endsWith(".html")?"text/html":p.endsWith(".json")?"application/json":"text/javascript";Map<String,String> h=new HashMap<>();h.put("Content-Security-Policy","default-src 'self';connect-src 'self';object-src 'none';frame-src 'none';base-uri 'none'");h.put("X-Content-Type-Options","nosniff");return new WebResourceResponse(type,"UTF-8",200,"OK",h,getAssets().open("cockpit66"+p));}catch(Exception e){return refused();}}
 });web.loadUrl(PAGE);}
 private WebResourceResponse refused(){return new WebResourceResponse("text/plain","UTF-8",403,"Refused",Collections.emptyMap(),new ByteArrayInputStream(new byte[0]));}
 private void revoke(String reason){if(!dead&&web!=null&&PAGE.equals(web.getUrl()))web.evaluateJavascript("window.cockpit66Lifecycle && window.cockpit66Lifecycle('"+reason+"')",null);}
 @Override public void onWindowFocusChanged(boolean focused){super.onWindowFocusChanged(focused);if(!focused)revoke("focus");}
 @Override protected void onPause(){revoke("pause");if(web!=null)web.onPause();super.onPause();}
 @Override protected void onResume(){super.onResume();if(web!=null){web.onResume();revoke("focus");}}
 @Override protected void onDestroy(){revoke("pause");dead=true;if(web!=null){web.destroy();web=null;}super.onDestroy();}
}
