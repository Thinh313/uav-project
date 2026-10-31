package vn.rtr.aeris.shell29;
import java.nio.charset.StandardCharsets;import java.security.MessageDigest;
import vn.rtr.aeris.shell24.Json;
public final class Plan {
 public final String id,label,sha,compiledRaw;public final double altitudeM,areaM2,seconds,homeX,homeY;public final int lines,photos;private final double[][] polygon,route;
 public Plan(String id,String label,String sha,String raw,double altitude,double area,int lines,int photos,double seconds,double homeX,double homeY,double[][] polygon,double[][] route){
  if(id==null||!id.matches("[a-z]+-(60|80)")||label==null||label.length()>80||raw==null||raw.length()>131072||sha==null||!sha.equals(hash(raw))||!Double.isFinite(altitude)||altitude<5||altitude>120||!Double.isFinite(area)||area<100||lines<1||photos<1||!Double.isFinite(seconds)||seconds<=0||!Double.isFinite(homeX)||!Double.isFinite(homeY)||Math.hypot(homeX,homeY)>1000)throw new IllegalArgumentException("Compiled contract integrity");
  this.id=id;this.label=label;this.sha=sha;this.compiledRaw=raw;this.altitudeM=altitude;this.areaM2=area;this.lines=lines;this.photos=photos;this.seconds=seconds;this.homeX=homeX;this.homeY=homeY;this.polygon=copy(polygon,3,64);this.route=copy(route,2,512);
 }
 private static double[][] copy(double[][] p,int min,int max){if(p==null||p.length<min||p.length>max)throw new IllegalArgumentException("Bounded route");double[][] r=new double[p.length][2];for(int i=0;i<p.length;i++){if(p[i]==null||p[i].length!=2||!Double.isFinite(p[i][0])||!Double.isFinite(p[i][1])||Math.hypot(p[i][0],p[i][1])>1000)throw new IllegalArgumentException("Local projection");r[i]=p[i].clone();}return r;}
 public double[][] polygon(){return copy(polygon,3,64);}public double[][] route(){return copy(route,2,512);}public int points(){return route.length;}
 public static String hash(String s){return hash(s.getBytes(StandardCharsets.UTF_8));}public static String hash(byte[] s){try{StringBuilder b=new StringBuilder();for(byte x:MessageDigest.getInstance("SHA-256").digest(s))b.append(String.format(java.util.Locale.ROOT,"%02x",x&255));return b.toString();}catch(Exception e){throw new IllegalStateException(e);}}
 public String json(){return "{\"id\":"+Json.quote(id)+",\"label\":"+Json.quote(label)+",\"missionSha256\":"+Json.quote(sha)+",\"altitudeM\":"+altitudeM+",\"altitudeFrame\":\"flat-reference\",\"world\":\"aeris-flat-world-v1\",\"coordinateSystem\":\"WGS84\",\"home\":{\"lat\":10.854,\"lon\":106.807,\"amslM\":10},\"areaM2\":"+areaM2+",\"lines\":"+lines+",\"estimatedPhotos\":"+photos+",\"points\":"+points()+",\"nominalSeconds\":"+seconds+",\"origin\":\"FROZEN_CORE_COMPILED_SYNTHETIC_SURVEY\",\"operational\":false}";}
}
