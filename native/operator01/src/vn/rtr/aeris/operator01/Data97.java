package vn.rtr.aeris.operator01;
import java.util.*;
public final class Data97{
 public static Map<String,Object> m(Object...a){Map<String,Object>m=new LinkedHashMap<>();for(int i=0;i<a.length;i+=2)m.put((String)a[i],a[i+1]);return m;}
 public static String json(Object x){if(x==null)return"null";if(x instanceof String)return Json.quote((String)x);if(x instanceof Boolean)return x.toString();if(x instanceof Number){if(!Double.isFinite(((Number)x).doubleValue()))throw new IllegalArgumentException("NONFINITE_JSON");return x.toString();}if(x instanceof Map){StringJoiner s=new StringJoiner(",","{","}");for(Object e0:((Map<?,?>)x).entrySet()){Map.Entry<?,?>e=(Map.Entry<?,?>)e0;s.add(Json.quote((String)e.getKey())+":"+json(e.getValue()));}return s.toString();}if(x instanceof Iterable){StringJoiner s=new StringJoiner(",","[","]");for(Object v:(Iterable<?>)x)s.add(json(v));return s.toString();}throw new IllegalArgumentException("JSON_TYPE");}
}
