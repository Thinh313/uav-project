package vn.rtr.aeris.field02;
import java.io.*;import java.nio.file.*;import java.security.*;import java.net.*;import java.util.*;
/** Deterministic byte/path policy, shared by ART and host adversarial tests. */
public final class Integrity02 {
 public static final String ORIGIN="http://127.0.0.1:8872";public static final int WORKSPACE_MAX=1200000,ARTIFACT_MAX=32*1024*1024;public static final long QUOTA=128L*1024*1024,RESERVE=128L*1024*1024;
 public static String sha(byte[] b){try{StringBuilder s=new StringBuilder();for(byte x:MessageDigest.getInstance("SHA-256").digest(b))s.append(String.format(Locale.ROOT,"%02x",x&255));return s.toString();}catch(Exception e){throw new IllegalStateException(e);}}
 public static boolean digest(String s){return s!=null&&s.matches("[a-f0-9]{64}");}
 public static byte[] read(InputStream in,int max)throws IOException{ByteArrayOutputStream o=new ByteArrayOutputStream();byte[]b=new byte[16384];int n;while((n=in.read(b))!=-1){if(n==0)continue;if(o.size()+n>max)throw new IOException("BYTE_BOUND");o.write(b,0,n);}return o.toByteArray();}
 public static boolean control(String url){try{URI u=new URI(url);return u.getScheme().equals("http")&&u.getHost().equals("127.0.0.1")&&u.getPort()==8872&&u.getUserInfo()==null;}catch(Exception e){return false;}}
 public static boolean subresource(String url){try{URI u=new URI(url);return u.getScheme().equals("http")&&u.getHost().equals("127.0.0.1")&&(u.getPort()==8872||u.getPort()==8873)&&u.getUserInfo()==null;}catch(Exception e){return false;}}
 public static String artifact(String url)throws IOException{if(!control(url))throw new IOException("ARTIFACT_ORIGIN");URI u=URI.create(url);if(u.getRawQuery()!=null||u.getRawFragment()!=null||!u.getRawPath().matches("(/delivery/[a-f0-9-]{36}/(index\\.json|flight\\.tar|capture-[0-9]{2}\\.tar)|/artifact/[a-f0-9-]{36}\\.tar)"))throw new IOException("ARTIFACT_PATH");return u.toString();}
 public static String filename(String s)throws IOException{if(s==null||!s.matches("[A-Za-z0-9][A-Za-z0-9._-]{0,95}")||s.contains(".."))throw new IOException("ARTIFACT_FILENAME");return s;}
 public static void verified(byte[]b,String expected)throws IOException{if(!digest(expected)||!sha(b).equals(expected))throw new IOException("SHA256_MISMATCH");}
 public static void publish(File f,byte[]b)throws IOException{Path p=f.toPath();if(Files.exists(p,LinkOption.NOFOLLOW_LINKS))throw new IOException("IMMUTABLE_EXISTS");Path temp=p.resolveSibling(p.getFileName()+".pending");try(OutputStream out=Files.newOutputStream(temp,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE)){out.write(b);}try(FileOutputStream out=new FileOutputStream(temp.toFile(),true)){out.getFD().sync();}Files.move(temp,p,StandardCopyOption.ATOMIC_MOVE);}
 public static long usage(File root)throws IOException{long total=0;File[]fs=root.listFiles();if(fs==null)return 0;for(File f:fs){if(Files.isSymbolicLink(f.toPath())||!f.isFile())throw new IOException("STORE_FOREIGN_ENTRY");total+=f.length();}return total;}
 private Integrity02(){}
}
