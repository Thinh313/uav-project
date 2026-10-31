package vn.rtr.aeris.cockpit81;
public final class PolicyTest {
 public static void main(String[] args){int n=0;for(String p:new String[]{"index.html","cockpit.mjs","runtime81.mjs","native81.css","fonts/Barlow-Bold.ttf","workflow/preflight/adapter.mjs","assets/camera-concept.png"}){if(!ResourcePolicy.allowed("https://native81.aeris.invalid/"+p))throw new AssertionError(p);n++;}
 for(String raw:new String[]{"http://native81.aeris.invalid/index.html","https://evil.invalid/index.html","https://native81.aeris.invalid.evil.invalid/index.html","https://user@native81.aeris.invalid/index.html","https://native81.aeris.invalid:443/index.html","https://native81.aeris.invalid/index.html?x=1","https://native81.aeris.invalid/index.html#x","https://native81.aeris.invalid/%69ndex.html","https://native81.aeris.invalid/../index.html","https://native81.aeris.invalid/workflow/../index.html","file:///index.html","javascript:alert(1)","https://native81.aeris.invalid/unknown","https://native81.aeris.invalid//index.html","https://native81.aeris.invalid/index.html%00"}){if(ResourcePolicy.allowed(raw))throw new AssertionError(raw);n++;}
 System.out.println("PASS_RESOURCE_POLICY "+n+" allow/deny cases; no remote or file origin");
 }
}
