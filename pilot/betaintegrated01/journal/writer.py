"""Versioned host-only recording foundation. Not wired to AP or native flight."""
from pathlib import Path
from dataclasses import dataclass
from collections import deque
import os,json,hashlib,zlib,base64,stat,time,threading,math
from .admission import DiskGuard,integer,checked_sum

VERSION=1
ZERO='0'*64
def encode(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def digest(b):return hashlib.sha256(b).hexdigest()
def ident(v):
    import re
    if type(v)is not str or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,63}',v):raise ValueError('CONTEXT_ID')
    return v
def safe_parent(p):
    p=Path(os.path.abspath(p))
    for a in [p,*p.parents]:
        if a.is_symlink():raise ValueError('SYMLINK_PATH')
    if not p.is_dir():raise ValueError('PARENT_DIRECTORY_REQUIRED')
    return p

@dataclass(frozen=True)
class Policy:
    segment_bytes:int=65536
    quota_bytes:int=8*2**20
    max_record_bytes:int=4096
    max_segments:int=128
    termination_reserve_bytes:int=16384
    def validate(self):
        for n,v in self.__dict__.items():integer(v,n,1)
        if not 1024<=self.max_record_bytes<=65536:raise ValueError('RECORD_BOUND')
        if self.segment_bytes<4*self.max_record_bytes+4096:raise ValueError('SEGMENT_GROUP_RESERVE')
        if self.quota_bytes<self.segment_bytes+self.termination_reserve_bytes:raise ValueError('QUOTA_RESERVE')
        if self.max_segments>4096 or self.termination_reserve_bytes<8192:raise ValueError('POLICY_BOUND')
        return self

class FileIO:
    """Fault seam; the journal additionally performs a non-injectable real disk check."""
    def __init__(self,hook=None):self.hook=hook or(lambda *a:None)
    def open_exclusive(self,path):
        self.hook('open',str(path),0)
        return os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,'O_NOFOLLOW',0),0o600)
    def write(self,fd,data):self.hook('write',None,len(data));return os.write(fd,data)
    def fsync(self,fd):self.hook('fsync',None,0);os.fsync(fd)
    def dirsync(self,path):
        self.hook('dirsync',str(path),0);fd=os.open(path,os.O_RDONLY|getattr(os,'O_DIRECTORY',0)|getattr(os,'O_NOFOLLOW',0))
        try:os.fsync(fd)
        finally:os.close(fd)
    def close(self,fd):os.close(fd)

class JournalError(RuntimeError):pass

def bounded_value(value,budget):
    """Bound caller-owned trees before JSON encoding; no recursive encoder first.

    The callback creating intent bytes is caller code and has its own resource
    obligation. Its returned bytes are checked before base64 publication.
    """
    remaining=budget;nodes=0;active=set()
    def visit(v,depth):
        nonlocal remaining,nodes
        nodes+=1
        if nodes>256 or depth>8:raise JournalError('PAYLOAD_TREE_BOUND')
        t=type(v)
        if v is None or t is bool:remaining-=5
        elif t is int:
            if not -(2**63)<=v<2**63:raise JournalError('PAYLOAD_INTEGER_BOUND')
            remaining-=20
        elif t is float:
            if not math.isfinite(v):raise JournalError('PAYLOAD_NONFINITE')
            remaining-=32
        elif t is str:
            if len(v)>budget:raise JournalError('PAYLOAD_STRING_BOUND')
            remaining-=len(v.encode('utf-8'))+2
        elif t in (dict,list):
            if len(v)>64 or id(v)in active:raise JournalError('PAYLOAD_CONTAINER_BOUND')
            active.add(id(v));remaining-=2+len(v)
            if t is dict:
                for k,x in v.items():
                    if type(k)is not str:raise JournalError('PAYLOAD_KEY_TYPE')
                    visit(k,depth+1);visit(x,depth+1)
            else:
                for x in v:visit(x,depth+1)
            active.remove(id(v))
        else:raise JournalError('PAYLOAD_TYPE')
        if remaining<0:raise JournalError('PAYLOAD_BYTE_BOUND')
    visit(value,0)

class SegmentedJournal:
    """Single-writer frame state machine; local send return is not AP execution.

    root must not exist. Parent must exist and contain no symlink. The caller
    supplies bytes or a compute(rx)->bytes function; no sockets are created here.
    """
    def __init__(self,root,run,epoch,policy=None,io=None):
        self.root=Path(os.path.abspath(root));safe_parent(self.root.parent)
        self.run,self.epoch=ident(run),ident(epoch);self.policy=(policy or Policy()).validate();self.io=io or FileIO()
        self.guard=DiskGuard(self.root.parent);self.guard.check(self.policy.termination_reserve_bytes)
        self.root.mkdir(mode=0o700);self.guard=DiskGuard(self.root)
        self.lock=threading.Lock();self.seq=0;self.head=ZERO;self.previous_segment=ZERO;self.segment=-1;self.fd=None;self.segment_used=0;self.used=0
        self.first_seq=None;self.segment_hash=None;self.next_frame=0;self.frames=0;self.phase='BETWEEN';self.failed=None;self.closed=False;self.send_called=False;self.stage_summary={}
        self.seal_shas=[]
        try:
            self.manifest_sha=self._meta('manifest.json',{'format':'aeris-beta-journal','version':VERSION,'run':run,'epoch':epoch,'policy':self.policy.__dict__,'scope':'HOST_RECORDING_FOUNDATION_NOT_AP_STAGE_OR_FLIGHT_ACCEPTANCE'})
            self._new_segment()
        except BaseException as e:self._fail(e);raise

    def _check(self):
        if self.failed or self.closed:raise JournalError('JOURNAL_NOT_WRITABLE')
        self.guard.check()

    def _write_all(self,fd,b):
        self.guard.check(len(b));view=memoryview(b)
        while view:
            n=self.io.write(fd,view)
            if type(n)is not int or n<=0 or n>len(view):raise OSError('SHORT_OR_INVALID_WRITE')
            view=view[n:]

    def _meta(self,name,value):
        b=encode(value)+b'\n'
        if len(b)>4096 or self.used+len(b)>self.policy.quota_bytes:raise JournalError('METADATA_QUOTA')
        p=self.root/name;fd=self.io.open_exclusive(p)
        try:self._write_all(fd,b);self.io.fsync(fd)
        finally:self.io.close(fd)
        self.io.dirsync(self.root);self.used+=len(b)
        return digest(b)

    def _record(self,kind,frame,payload,sync=False):
        if self.seq>=2**63-1:raise JournalError('SEQUENCE_BOUND')
        bounded_value(payload,self.policy.max_record_bytes)
        body={'v':VERSION,'run':self.run,'epoch':self.epoch,'segment':self.segment,'seq':self.seq,'previous':self.head,'kind':kind,'frame':frame,'payload':payload}
        raw=encode(body);head=digest(bytes.fromhex(self.head)+raw);b=encode({'body':body,'crc32':format(zlib.crc32(raw),'08x'),'sha256':head})+b'\n'
        if len(b)>self.policy.max_record_bytes:raise JournalError('RECORD_SIZE_BOUND')
        if self.segment_used+len(b)>self.policy.segment_bytes or self.used+len(b)>self.policy.quota_bytes:raise JournalError('RECORD_CAPACITY')
        self._write_all(self.fd,b)
        if sync:self.io.fsync(self.fd)
        self.segment_hash.update(b);self.segment_used+=len(b);self.used+=len(b);self.head=head;self.seq+=1
        return self.seq-1

    def _new_segment(self):
        if self.segment+1>=self.policy.max_segments:raise JournalError('SEGMENT_COUNT_BOUND')
        self.segment+=1;self.segment_used=0;self.first_seq=self.seq;self.segment_hash=hashlib.sha256()
        self.fd=self.io.open_exclusive(self.root/('segment-%06d.jsonl'%self.segment));self.io.dirsync(self.root)
        self._record('SEGMENT',None,{'ordinal':self.segment,'startSequence':self.seq,'previousSegmentSHA256':self.previous_segment},True)

    def _seal(self,state):
        self.io.fsync(self.fd)
        seal={'version':VERSION,'run':self.run,'epoch':self.epoch,'segment':self.segment,'startSequence':self.first_seq,'endSequence':self.seq-1,'fileBytes':self.segment_used,'fileSHA256':self.segment_hash.hexdigest(),'head':self.head,'previousSegmentSHA256':self.previous_segment,'state':state}
        self.seal_shas.append(self._meta('segment-%06d.seal.json'%self.segment,seal))
        self.io.close(self.fd);self.fd=None;self.previous_segment=seal['fileSHA256'];return seal

    def _reserve_group(self):
        reserve=3*self.policy.max_record_bytes
        # Account a successor header and both segment metadata plus termination.
        if self.used+reserve+self.policy.termination_reserve_bytes+8192>self.policy.quota_bytes:raise JournalError('FRAME_ADMISSION_QUOTA')
        self.guard.check(reserve+self.policy.termination_reserve_bytes+8192)
        if self.segment_used+reserve+self.policy.max_record_bytes>self.policy.segment_bytes:
            self._seal('ROTATED');self._new_segment()

    def record_frame(self,frame,rx_bytes,intent_or_compute,send):
        if not self.lock.acquire(blocking=False):raise JournalError('SINGLE_WRITER_BUSY')
        try:
            self._check();integer(frame,'frame');self.send_called=False
            if self.phase!='BETWEEN'or frame!=self.next_frame or type(rx_bytes)is not bytes:raise JournalError('FRAME_ORDER_OR_TYPE')
            if len(rx_bytes)>self.policy.max_record_bytes*3//4:raise JournalError('RX_INPUT_BOUND')
            if not callable(intent_or_compute)and(type(intent_or_compute)is not bytes or len(intent_or_compute)>self.policy.max_record_bytes*3//4):raise JournalError('INTENT_INPUT_BOUND')
            self._reserve_group();self.phase='RX'
            self._record('RX',frame,{'base64':base64.b64encode(rx_bytes).decode()})
            intent=intent_or_compute(rx_bytes)if callable(intent_or_compute)else intent_or_compute
            if type(intent)is not bytes:raise JournalError('INTENT_BYTES_REQUIRED')
            if len(intent)>self.policy.max_record_bytes*3//4:raise JournalError('INTENT_INPUT_BOUND')
            self._record('INTENT',frame,{'base64':base64.b64encode(intent).decode()},True);self.phase='INTENT_DURABLE'
            # A fresh actual-host guard after durable INTENT and immediately before send.
            self.guard.check(self.policy.termination_reserve_bytes);self.send_called=True
            try:returned=send(intent)
            except BaseException as e:
                self._record('UNKNOWN',frame,{'reason':'SEND_RAISED','errorType':type(e).__name__,'sendCalled':True},True);raise JournalError('SEND_OUTCOME_UNKNOWN')from e
            if type(returned)is not int or returned!=len(intent):
                self._record('UNKNOWN',frame,{'reason':'LOCAL_SEND_LENGTH_MISMATCH','sendCalled':True,'returned':returned if type(returned)is int and -(2**63)<=returned<2**63 else None,'expected':len(intent)},True);raise JournalError('SEND_OUTCOME_UNKNOWN')
            self._record('SENT',frame,{'returnedBytes':returned,'expectedBytes':len(intent),'scope':'LOCAL_CALLBACK_RETURN_NOT_AP_EXECUTION'},True)
            self.frames+=1;self.next_frame+=1;self.phase='BETWEEN'
            return {'frame':frame,'localSendReturned':True,'APExecutionAccepted':False,'intentBytes':len(intent)}
        except BaseException as e:self._fail(e);raise
        finally:self.lock.release()

    def append_event(self,kind,payload):
        if not self.lock.acquire(blocking=False):raise JournalError('SINGLE_WRITER_BUSY')
        try:
            return self._append_event_locked(kind,payload)
        except BaseException as e:self._fail(e);raise
        finally:self.lock.release()

    def _append_event_locked(self,kind,payload):
        self._check()
        if self.phase!='BETWEEN'or type(kind)is not str or not kind or len(kind)>48:raise JournalError('EVENT_CONTEXT')
        bounded_value(payload,self.policy.max_record_bytes)
        self._reserve_group();return self._record('EVENT',None,{'eventKind':kind,'data':payload},True)

    def append_stage(self,frame,fields):
        if not self.lock.acquire(blocking=False):raise JournalError('SINGLE_WRITER_BUSY')
        try:
            self._check();integer(frame,'stage_frame')
            if frame>=self.next_frame or type(fields)is not dict or len(fields)>32:raise JournalError('STAGE_CONTEXT')
            if len(set(self.stage_summary)|set(fields))>32:raise JournalError('STAGE_SUMMARY_FIELD_BOUND')
            for k,v in fields.items():
                if type(k)is not str or not k or len(k)>48:raise JournalError('STAGE_KEY')
                integer(v,'stage_value')
                prior=self.stage_summary.get(k,{});checked_sum(prior.get('sum',0),v);checked_sum(prior.get('count',0),1)
            result=self._append_event_locked('STAGE',{'frame':frame,'fields':fields})
            for k,v in fields.items():
                s=self.stage_summary.setdefault(k,{'count':0,'sum':0,'max':0});s['count']+=1;s['sum']+=v;s['max']=max(s['max'],v)
            return result
        except BaseException as e:self._fail(e);raise
        finally:self.lock.release()

    def close(self):
        if not self.lock.acquire(blocking=False):raise JournalError('SINGLE_WRITER_BUSY')
        try:
            self._check()
            if self.phase!='BETWEEN':raise JournalError('INCOMPLETE_GROUP_NO_CLOSE')
            self._record('CLOSE',None,{'completedFrames':self.frames,'scope':'RECORDING_ONLY_NOT_FLIGHT'},True)
            seal=self._seal('SESSION_CLOSED')
            result={'version':VERSION,'run':self.run,'epoch':self.epoch,'segments':self.segment+1,'records':self.seq,'head':self.head,'lastSegmentSHA256':seal['fileSHA256'],'frames':self.frames,'state':'COMPLETE_RECORDING','APExecutionAccepted':False}
            session_sha=self._meta('session.json',result);self.closed=True
            # Returned only after every file/directory sync has acknowledged. Keep
            # this anchor outside the journal; never infer it from imported bytes.
            anchor={'version':1,'run':self.run,'epoch':self.epoch,'manifestSHA256':self.manifest_sha,'sessionSHA256':session_sha,'sealSHA256':list(self.seal_shas),'head':self.head}
            return {**result,'commitAnchor':anchor,'publicationAllowed':False,'scope':'LOCAL_FSYNC_ACK_NOT_SOURCE_AUTH_OR_POWERLOSS_PROOF'}
        except BaseException as e:self._fail(e);raise
        finally:self.lock.release()

    def _fail(self,error):
        if self.failed or self.closed:return
        self.failed=type(error).__name__+':'+str(error)[:200]
        # Failure recording is best effort and cannot convert its own I/O error to success.
        try:self._meta('failure.json',{'version':VERSION,'run':self.run,'epoch':self.epoch,'reason':self.failed,'phase':self.phase,'nextFrame':self.next_frame,'sendCalled':self.send_called,'complete':False})
        except BaseException:pass
        if self.fd is not None:
            try:self.io.close(self.fd)
            except BaseException:pass
            self.fd=None

    def abort(self,reason):
        if self.closed:raise JournalError('SEALED_SESSION')
        self._fail(JournalError(str(reason)));return {'state':'INCOMPLETE_RECORDING','reason':self.failed,'APExecutionAccepted':False}
