package vn.rtr.aeris.native95;
import java.io.*;import java.nio.channels.*;import java.nio.charset.StandardCharsets;import java.nio.file.*;import java.security.*;import java.util.*;
/** Exclusive per-Activity evidence stream. No resume, repair or deletion API. */
public final class BenchJournal89 implements Closeable {
 public static final long MAX_FILE=1024*1024,MAX_TOTAL=8*1024*1024;private FileOutputStream out;private FileChannel gate;private FileLock lock;private final File directory;private long last=-1,bytes=0;private int seq=0;private String previous="";private boolean blocked=false;public final File file;
 public BenchJournal89(File directory,String session)throws IOException{
  this.directory=directory;if(!session.matches("[a-f0-9-]{36}")||directory.exists()&&!directory.isDirectory())throw new IOException("LOG_ROOT");if(!directory.exists()&&!directory.mkdirs())throw new IOException("LOG_ROOT_CREATE");if(Files.isSymbolicLink(directory.toPath()))throw new IOException("LOG_SYMLINK");File lf=new File(directory,"bench.lock");if(Files.isSymbolicLink(lf.toPath()))throw new IOException("LOCK_SYMLINK");gate=FileChannel.open(lf.toPath(),StandardOpenOption.CREATE,StandardOpenOption.WRITE);try{lock=gate.tryLock();if(lock==null)throw new IOException("BENCH_ALREADY_OPEN");}catch(Exception e){gate.close();throw new IOException("BENCH_ALREADY_OPEN",e);}try{long total=0;File[] list=directory.listFiles();if(list==null||list.length>=24)throw new IOException("LOG_QUOTA_NO_DELETE");for(File f:list){if(Files.isSymbolicLink(f.toPath())||!f.isFile())throw new IOException("LOG_FOREIGN_ENTRY");total+=f.length();}if(total>=MAX_TOTAL||directory.getUsableSpace()<32*1024*1024)throw new IOException("LOG_RESERVE_NO_DELETE");file=new File(directory,session+".jsonl");Files.createFile(file.toPath());out=new FileOutputStream(file,true);}catch(IOException e){lock.release();gate.close();throw e;}
 }
 public static String sha(byte[] b){try{byte[] h=MessageDigest.getInstance("SHA-256").digest(b);StringBuilder s=new StringBuilder();for(byte x:h)s.append(String.format(Locale.ROOT,"%02x",x&255));return s.toString();}catch(Exception e){throw new IllegalStateException(e);}}
 public synchronized String append(String payload,long t)throws IOException{
  if(blocked||out==null)throw new IOException("LOG_BLOCKED");byte[] raw=payload==null?new byte[0]:payload.getBytes(StandardCharsets.UTF_8);
  if(t<0||t<last||raw.length==0||raw.length>16384||seq>=512){blocked=true;throw new IOException("LOG_CLOCK_PAYLOAD_OR_COUNT_BOUND");}
  long total=0;for(File f:directory.listFiles())total+=f.length();if(total>=MAX_TOTAL||directory.getUsableSpace()<32*1024*1024){blocked=true;throw new IOException("LOG_TOTAL_RESERVE_NO_DELETE");}
  String b="{\"n\":"+(seq+1)+",\"elapsedMs\":"+t+",\"previous\":"+Json.quote(previous)+",\"payloadBase64\":"+Json.quote(Base64.getEncoder().encodeToString(raw))+"}";String h=sha(b.getBytes(StandardCharsets.UTF_8));byte[] line=(b.substring(0,b.length()-1)+",\"sha256\":"+Json.quote(h)+"}\n").getBytes(StandardCharsets.UTF_8);if(bytes+line.length>MAX_FILE){blocked=true;throw new IOException("LOG_FILE_QUOTA_NO_DELETE");}
  try{out.write(line);out.getFD().sync();}catch(IOException e){blocked=true;throw e;}seq++;bytes+=line.length;previous=h;last=t;return h;
 }
 public synchronized void close()throws IOException{if(out!=null){out.close();out=null;}if(lock!=null){lock.release();lock=null;}if(gate!=null){gate.close();gate=null;}}public String head(){return previous;}public int count(){return seq;}
}
