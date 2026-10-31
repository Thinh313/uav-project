package vn.rtr.aeris.beta01runtime;
import java.io.*;
import java.nio.channels.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

/** Native wire/lifecycle journal; separate versioned format from Python model frames. */
public final class NativeSegments implements Closeable {
    public interface Clock {long nowNs();}
    public interface Sync {void file(FileDescriptor fd)throws IOException;void directory(File dir)throws IOException;}
    public interface Send {void write(byte[] bytes)throws Exception;}
    public static final long RESERVE=256L*1024*1024;
    private final File root;private final String run,epoch;private final Clock clock;private final Sync sync;
    private final long segmentLimit,totalLimit;private final int maxSegments;
    private final FileOutputStream lockStream;private final FileLock lock;
    private FileOutputStream out;private File active;private String head="",priorSeal="";private long sequence,bytes,segmentBytes,first,lastTime=-1;
    private int segment;private boolean failed,closed;private String failure,commitAnchor;
    public NativeSegments(File root,String run,String epoch,Clock clock,Sync sync,long segmentLimit,long totalLimit,int maxSegments)throws IOException {
        if(run==null||epoch==null||!run.matches("[A-Za-z0-9_.:-]{1,128}")||!epoch.matches("[A-Za-z0-9_.:-]{1,128}")||clock==null||sync==null||segmentLimit<32768||segmentLimit>8L*1024*1024||totalLimit<segmentLimit*2||totalLimit>512L*1024*1024||maxSegments<2||maxSegments>4096)throw new IOException("SEGMENT_POLICY");
        this.root=root;this.run=run;this.epoch=epoch;this.clock=clock;this.sync=sync;this.segmentLimit=segmentLimit;this.totalLimit=totalLimit;this.maxSegments=maxSegments;
        if(Files.exists(root.toPath(),LinkOption.NOFOLLOW_LINKS)||!root.mkdir())throw new IOException("EXCLUSIVE_RUN_DIRECTORY");
        sync.directory(root.getParentFile());
        lockStream=new FileOutputStream(new File(root,"writer.lock"));lock=lockStream.getChannel().tryLock();if(lock==null)throw new IOException("SINGLE_WRITER");
        try {open();}catch(IOException e){lock.release();lockStream.close();throw e;}
    }
    private void capacity(long n)throws IOException {
        if(n<0||bytes+n>totalLimit-16384||root.getUsableSpace()<RESERVE+n+16384)throw new IOException("NATIVE_QUOTA_OR_RESERVE");
    }
    private void exclusive(File p,byte[] data)throws IOException {
        capacity(data.length);Files.createFile(p.toPath());try(FileOutputStream f=new FileOutputStream(p)){IoTiming.Token timing=IoTiming.beginCurrent("journal.write");try{f.write(data);}finally{IoTiming.endCurrent(timing);}sync.file(f.getFD());}sync.directory(root);bytes+=data.length;
    }
    private void open()throws IOException {
        if(segment>=maxSegments)throw new IOException("SEGMENT_COUNT_BOUND");
        active=new File(root,String.format(Locale.ROOT,"segment-%06d.jsonl",segment));Files.createFile(active.toPath());out=new FileOutputStream(active);segmentBytes=0;first=sequence+1;
        raw("HEADER",Values.bytes(Values.map("format","aeris-native-segments","version",1,"segment",segment,"previousSeal",priorSeal)));
        sync.directory(root);
    }
    private void raw(String kind,byte[] data)throws IOException {
        long n=clock.nowNs();if(n<0||n<lastTime)throw new IOException("NATIVE_CLOCK_REGRESSION");
        String body=Values.json(Values.map("format","aeris-native-record","version",1,"run",run,"epoch",epoch,"segment",segment,"n",sequence+1,"previous",head,"monotonicNs",n,"kind",kind,"base64",Base64.getEncoder().encodeToString(data)));
        String sha=Values.hash(body.getBytes(StandardCharsets.UTF_8));byte[] line=(body.substring(0,body.length()-1)+",\"sha256\":\""+sha+"\"}\n").getBytes(StandardCharsets.UTF_8);
        capacity(line.length);IoTiming.Token timing=IoTiming.beginCurrent("journal.write");try{out.write(line);}finally{IoTiming.endCurrent(timing);}sync.file(out.getFD());sequence++;lastTime=n;head=sha;bytes+=line.length;segmentBytes+=line.length;
    }
    public synchronized long append(String kind,byte[] data)throws IOException {
        if(closed||failed)throw new IOException("NATIVE_JOURNAL_CLOSED_OR_FAILED");
        if(!kind.matches("[A-Z][A-Z0-9_]{0,47}")||Arrays.asList("HEADER","SESSION_CLOSE").contains(kind)||data==null||data.length>8192)throw new IOException("NATIVE_RECORD_BOUND");
        try {long bound=512L+((data.length+2L)/3)*4+run.length()+epoch.length();if(segmentBytes+bound+16384>segmentLimit){seal();segment++;open();}raw(kind,data);return sequence;}
        catch(IOException e){poison(e);throw e;}
    }
    /** One bounded versioned logical candidate record, one existing append barrier. Completion clock is sampled AFTER that barrier. */
    public static final class Barrier {public final long recordN,durableNs;public final String payloadSHA256;Barrier(long n,long d,String h){recordN=n;durableNs=d;payloadSHA256=h;}}
    public synchronized Barrier transaction(String kind,byte[] payload)throws IOException{
        if(!Arrays.asList("CONTROL_INPUT_TX","CONTROL_CONSENT_TX").contains(kind))throw new IOException("AUTHORITY_TRANSACTION_KIND");
        long n=append(kind,payload);long completed=clock.nowNs();if(completed<0||completed<lastTime){IOException e=new IOException("TRANSACTION_COMPLETION_CLOCK_REGRESSION");poison(e);throw e;}return new Barrier(n,completed,Values.hash(payload));
    }
    public synchronized void intentSend(byte[] wire,Send sender)throws Exception {
        append("TX_INTENT",wire);
        try {sender.write(wire);append("TX_WRITTEN",wire);}
        catch(Exception e){try{append("TX_UNKNOWN",Values.bytes(Values.map("wireSHA256",Values.hash(wire),"reason",e.getClass().getSimpleName())));}catch(Exception ignored){}poison(e);throw e;}
    }
    public interface Approval {void check()throws Exception;}
    /** New explicit pre-socket phase; legacy overload above remains byte/behavior compatible. */
    public synchronized void intentSend(byte[]wire,Approval approval,Send sender)throws Exception{
        long intentRecordN=append("TX_INTENT",wire);
        try{approval.check();}catch(Exception refused){
            String reason=String.valueOf(refused.getMessage());if(reason.length()>512)reason=reason.substring(0,512);
            try{append("TX_REFUSED",Values.bytes(Values.map("wireSHA256",Values.hash(wire),"intentRecordN",intentRecordN,"reasonClass",refused.getClass().getSimpleName(),"reason",reason,"disposition","PRE_SOCKET_REFUSED","socketCallbackEntered",false,"run",run,"epoch",epoch)));}
            catch(Exception outcomeFailure){poison(outcomeFailure);refused.addSuppressed(outcomeFailure);}
            throw refused;
        }
        try{sender.write(wire);append("TX_WRITTEN",wire);}
        catch(Exception unknown){try{append("TX_UNKNOWN",Values.bytes(Values.map("wireSHA256",Values.hash(wire),"reason",unknown.getClass().getSimpleName())));}catch(Exception outcomeFailure){unknown.addSuppressed(outcomeFailure);}poison(unknown);throw unknown;}
    }
    private String seal()throws IOException {
        sync.file(out.getFD());out.close();out=null;
        byte[] raw=Files.readAllBytes(active.toPath());
        byte[] data=Values.bytes(Values.map("format","aeris-native-seal","version",1,"run",run,"epoch",epoch,"segment",segment,"file",active.getName(),"bytes",raw.length,"sha256",Values.hash(raw),"first",first,"last",sequence,"head",head,"previousSeal",priorSeal));
        File p=new File(root,String.format(Locale.ROOT,"seal-%06d.json",segment));exclusive(p,data);priorSeal=Values.hash(data);return priorSeal;
    }
    private void poison(Exception e) {failed=true;if(failure==null)failure=e.getClass().getSimpleName()+":"+String.valueOf(e.getMessage());}
    public synchronized String finish(String reason)throws IOException {
        if(reason==null||!reason.matches("[A-Z0-9_:-]{1,128}"))throw new IOException("CLOSE_REASON_BOUND");
        if(closed){if(commitAnchor==null)throw new IOException("CLOSE_UNCOMMITTED");return commitAnchor;}
        if(failed)throw new IOException("JOURNAL_FAILED_PREFIX_ONLY:"+failure);
        try {
            raw("SESSION_CLOSE",Values.bytes(Values.map("reason",reason,"authorityRestorable",false,"aircraftExecutionAccepted",false)));
            seal();byte[] session=Values.bytes(Values.map("format","aeris-native-session","version",1,"run",run,"epoch",epoch,"segments",segment+1,"records",sequence,"head",head,"lastSeal",priorSeal,"authorityRestorable",false,"publicationAllowed",false));
            exclusive(new File(root,"session.json"),session);
            commitAnchor=Values.hash(session);closed=true;return commitAnchor;
        }catch(IOException e){poison(e);throw e;}
        finally {if(out!=null)try{out.close();}catch(Exception ignored){}if(lock.isValid())lock.release();lockStream.close();}
    }
    public synchronized void close()throws IOException {
        if(!closed&&!failed){finish("EXPLICIT_CLOSE");return;}
        if(out!=null){out.close();out=null;}if(lock.isValid())lock.release();lockStream.close();
    }
    public synchronized Map<String,Object> snapshot() {return Values.map("run",run,"epoch",epoch,"records",sequence,"bytes",bytes,"segments",segment+1,"head",head,"failed",failed,"failure",failure,"closed",closed,"commitAnchor",commitAnchor,"publicationAllowed",false);}
}
