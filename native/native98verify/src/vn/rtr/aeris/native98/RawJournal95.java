package vn.rtr.aeris.native98;
import java.io.*;import java.nio.charset.StandardCharsets;import java.util.Base64;
/** Fixed-order SHA chain; durable raw bytes precede all TX and all JS RX delivery. */
public final class RawJournal95 implements Closeable{
 public interface Clock{long now();}private final FileOutputStream out;private final File file;private final Clock clock;private long count=0,bytes=0,last=-1;private String head="";private boolean failed=false,closed=false;
 public RawJournal95(File file,Clock clock)throws IOException{this.file=file;this.clock=clock;if(file.exists()||!file.getParentFile().isDirectory())throw new IOException("JOURNAL_CREATE_NEW");out=new FileOutputStream(file);}
 public synchronized long append(String kind,byte[] data)throws IOException{if(closed||failed)throw new IOException("JOURNAL_NOT_WRITABLE");if(!kind.matches("[A-Z0-9_]{1,60}")||data.length>131072)throw new IOException("JOURNAL_BOUND");long t=clock.now();if(t<last)throw new IOException("JOURNAL_CLOCK_REGRESSION");last=t;String body="{\"n\":"+(count+1)+",\"previous\":"+Json.quote(head)+",\"elapsedMs\":"+t+",\"kind\":"+Json.quote(kind)+",\"dataBase64\":"+Json.quote(Base64.getEncoder().encodeToString(data))+"}";String digest=DraftStore.hash(body.getBytes(StandardCharsets.UTF_8));byte[] line=(body.substring(0,body.length()-1)+",\"sha256\":"+Json.quote(digest)+"}\n").getBytes(StandardCharsets.UTF_8);if(bytes+line.length>32L*1024*1024||file.getUsableSpace()<DraftStore.RESERVE+line.length)throw new IOException("RAW_STORAGE_RESERVE_OR_QUOTA");try{out.write(line);out.getFD().sync();count++;bytes+=line.length;head=digest;return count;}catch(IOException e){failed=true;throw e;}}
 public synchronized String summary(){return "{\"records\":"+count+",\"bytes\":"+bytes+",\"head\":"+Json.quote(head)+",\"failed\":"+failed+",\"closed\":"+closed+"}";}
 public synchronized void close()throws IOException{if(!closed){closed=true;out.getFD().sync();out.close();}}
}
