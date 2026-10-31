package vn.rtr.aeris.operator01;
public final class PolicyTest {
 public static void main(String[] args){int n=0;for(String p:new String[]{"presentation-owner01.mjs","operator01.mjs","operator-model01.mjs","operator01.css","index.html","cockpit.mjs","runtime82.mjs","native82.css","fonts/Barlow-Bold.ttf","workflow/preflight/adapter.mjs","assets/camera-concept.png"}){if(!ResourcePolicy.allowed("https://operator01.aeris.invalid/"+p))throw new AssertionError(p);n++;}
 for(String raw:new String[]{"http://native87.aeris.invalid/index.html","https://evil.invalid/index.html","https://operator01.aeris.invalid.evil.invalid/index.html","https://user@native87.aeris.invalid/index.html","https://operator01.aeris.invalid:443/index.html","https://operator01.aeris.invalid/index.html?x=1","https://operator01.aeris.invalid/index.html#x","https://operator01.aeris.invalid/%69ndex.html","https://operator01.aeris.invalid/../index.html","https://operator01.aeris.invalid/workflow/../index.html","file:///index.html","javascript:alert(1)","https://operator01.aeris.invalid/unknown","https://operator01.aeris.invalid//index.html","https://operator01.aeris.invalid/index.html%00"}){if(ResourcePolicy.allowed(raw))throw new AssertionError(raw);n++;}
 System.out.println("PASS_RESOURCE_POLICY "+n+" allow/deny cases; no remote or file origin");
 }
}
