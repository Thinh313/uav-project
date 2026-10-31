package vn.rtr.aeris.beta01runtime;
import java.util.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import vn.rtr.aeris.native98.Json;
public final class Values {
    private Values() {}
    public static String hash(byte[] bytes) {
        try { byte[] h=MessageDigest.getInstance("SHA-256").digest(bytes); return hex(h); }
        catch(Exception e) { throw new IllegalStateException(e); }
    }
    public static String hex(byte[] b) { StringBuilder s=new StringBuilder();for(byte v:b)s.append(String.format(Locale.ROOT,"%02x",v&255));return s.toString(); }
    public static String json(Object value) {
        if(value==null)return "null";
        if(value instanceof String)return Json.quote((String)value);
        if(value instanceof Boolean)return value.toString();
        if(value instanceof Number) { if(value instanceof Double&&!Double.isFinite((Double)value))throw new IllegalArgumentException("NONFINITE");return value.toString(); }
        if(value instanceof Map) {StringJoiner s=new StringJoiner(",","{","}");for(Object k:((Map<?,?>)value).keySet())s.add(Json.quote(k.toString())+":"+json(((Map<?,?>)value).get(k)));return s.toString();}
        if(value instanceof Iterable) {StringJoiner s=new StringJoiner(",","[","]");for(Object v:(Iterable<?>)value)s.add(json(v));return s.toString();}
        throw new IllegalArgumentException("JSON_TYPE");
    }
    public static Map<String,Object> map(Object... a) { LinkedHashMap<String,Object> m=new LinkedHashMap<>();for(int i=0;i<a.length;i+=2)m.put((String)a[i],a[i+1]);return m; }
    public static byte[] bytes(Object value) {return json(value).getBytes(StandardCharsets.UTF_8);}
}
