"""Optional pose observer: post-STAGE latest-only memory -> anonymous pipe.
It cannot send flight commands, change physics, block it on IO or alter rawframes.
"""
from collections import deque
from pathlib import Path
import errno,json,math,os,select,stat,struct,threading,time,zlib,hashlib
MAX_FRAME=2048
NO_RESERVATION=object()

def need(v,name):
 if not v:raise ValueError('SCENE_'+name)
def unique(items):
 out={}
 for k,v in items:need(k not in out,'DUPLICATE_FIELD');out[k]=v
 return out
class ScenePublisher:
 def __init__(self,fd,context,ap_snapshot,source_binding):
  need(type(fd)is int and fd>2 and stat.S_ISFIFO(os.fstat(fd).st_mode),'ORIGINAL_INHERITED_ANONYMOUS_PIPE')
  self.source_binding=dict(source_binding);need(set(self.source_binding)=={'backendSourceSHA256','modelSourceSHA256','profileSHA256','journalPolicySHA256'}and all(__import__('re').fullmatch('[a-f0-9]{64}',v)for v in self.source_binding.values()),'EXACT_SOURCE_BINDING');self.fd=fd;os.set_blocking(fd,False);self.context={k:context[k]for k in('run','epoch','boot','profileId')};self.ap_snapshot=ap_snapshot;self.pending=deque(maxlen=1);self.stop=threading.Event();self.thread=None;self.failure=None;self.selected=0;self.sent=0;self.no_fresh_AP=0;self.next_due=0;self.last_frame=-1;self.inflight=False;self.reserved=None
 def start(self):
  need(self.thread is None,'ONE_START');self.thread=threading.Thread(target=self._run,name='aeris-scene-pipe',daemon=False);self.thread.start()
 def reserve(self,frame,row,origin):
  # Main physics thread only. Reserve BEFORE stage encoding/fsync, so the
  # later offer cannot drift onto a DELTA row when crossing the20Hz boundary.
  if self.failure is not None or self.stop.is_set():return None
  sampled=origin+row['computeEndSinceOriginNs']
  if sampled<self.next_due:return None
  if self.reserved is not None:self.failure='SCENE_ONE_OUTSTANDING_STAGE_RESERVATION';return None
  self.next_due=sampled+50_000_000;self.reserved={'frame':frame,'sampled':sampled};return self.reserved
 def offer(self,adapter,frame,row,*,reservation=NO_RESERVATION):
  # The flight thread performs only a short model clone and deque append. The
  # serializer never holds any lock that the flight thread must acquire.
  if self.failure is not None or self.stop.is_set():return
  sampled=adapter.origin_ns+row['computeEndSinceOriginNs']
  if reservation is NO_RESERVATION:reservation=self.reserve(frame,row,adapter.origin_ns)
  if reservation is None:return
  try:
   need(reservation is self.reserved and reservation['frame']==frame and reservation['sampled']==sampled,'SOURCE_STAGE_RESERVATION');self.reserved=None
   need(getattr(adapter.journal,'last_stage_encoding_absolute',True)is True,'SELECTED_STAGE_MUST_BE_ABSOLUTE')
   need(adapter.current['phase']=='FRAME_AND_STAGE_COMPLETE'and adapter.current['SENTGroupAcknowledged']is True,'AFTER_DURABLE_SENT_AND_STAGE')
   heartbeat=self.ap_snapshot().get('latest',{}).get('HEARTBEAT')
   if type(heartbeat)is not dict or type(heartbeat.get('armed'))is not bool or type(heartbeat.get('observedHostNs'))is not int or not 0<=sampled-heartbeat['observedHostNs']<=1_500_000_000:self.no_fresh_AP+=1;return
   model=adapter.model.snapshot();journal=adapter.journal
   value={'format':'aeris-sim-scene-frame','version':1,'mode':'LIVE','poseSource':'ROOT_DURABLE_FDM_STATE','sourceBinding':dict(self.source_binding),'context':dict(self.context),'frame':frame,'simulationTimeS':model['timestamp'],'sampleHostNs':str(sampled),'committedHostNs':str(time.monotonic_ns()),'positionNedM':list(model['position']),'quaternionWxyz':list(model['quaternion']),'rpmEstimated':list(model['rpmEstimated']),'ap':{'armed':heartbeat['armed'],'heartbeatHostNs':str(heartbeat['observedHostNs'])},'rawRef':{'relativePath':'journal/segment-%06d.jsonl'%journal.segment,'throughSequence':journal.seq-1,'headSHA256':journal.head,'prefixBytes':journal.segment_used,'frame':frame}}
   value['rawRef']['previousLogicalHeadSHA256']=journal.last_record_previous_head
   value['rawRef']['privatePhysicalStageSHA256']=journal.last_stage_physical_sha;value['rawRef']['physicalStageBytes']=journal.last_stage_physical_bytes
   self.selected+=1;self.pending.append(value)
  except BaseException as error:self.failure=type(error).__name__+':'+str(error)[:256]
 def _run(self):
  try:
   while not self.stop.is_set()or self.pending:
    try:value=self.pending.pop()
    except IndexError:self.stop.wait(.005);continue
    body=json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode();need(len(body)<=MAX_FRAME,'FRAME_BOUND');wire=struct.pack('!I',len(body))+body;offset=0;self.inflight=True
    # Once a framed message starts, finish it before any newer frame. A full
    # pipe never blocks the physics thread; only its oldest pending visual view
    # may be overwritten. A shutdown timeout retains an unavailable partial.
    end=None
    while offset<len(wire):
     if self.stop.is_set()and end is None:end=time.monotonic()+.2
     if end is not None and time.monotonic()>=end:raise TimeoutError('SCENE_PARTIAL_AT_BOUNDED_SHUTDOWN')
     try:n=os.write(self.fd,wire[offset:]);need(type(n)is int and n>0,'WRITE_COUNT');offset+=n
     except BlockingIOError:select.select([],[self.fd],[],.01)
    self.sent+=1;self.last_frame=value['frame'];self.inflight=False
  except BaseException as error:self.failure=type(error).__name__+':'+str(error)[:256]
  finally:
   try:os.close(self.fd)
   except OSError:pass
 def close(self):
  self.stop.set()
  if self.thread:self.thread.join(timeout=.5)
  if self.thread and self.thread.is_alive():self.failure=self.failure or'SCENE_WRITER_CLOSE_UNKNOWN'
  return {'selectedVisualFrames':self.selected,'completeVisualFrames':self.sent,'visualFramesSkipped':max(0,self.selected-self.sent-len(self.pending)-int(self.inflight)),'noFreshAPVisualFrames':self.no_fresh_AP,'failure':self.failure,'physicsFramesDropped':0,'flightAcceptance':False}
class ScenePipeReader:
 def __init__(self,fd,context,raw_root,source_binding):
  need(type(fd)is int and stat.S_ISFIFO(os.fstat(fd).st_mode),'OWNED_READ_PIPE');self.source_binding=dict(source_binding);self.fd=fd;os.set_blocking(fd,False);self.context={k:context[k]for k in('run','epoch','boot','profileId')};self.raw_root=Path(raw_root);self.pending=bytearray();self.latest=None;self.failure=None;self.eof=False;self.stop=threading.Event();self.thread=None;self.received=0;self.closure=None
 def start(self):
  need(self.thread is None,'READER_ONE_START');self.thread=threading.Thread(target=self._run,name='aeris-scene-reader',daemon=False);self.thread.start()
 def _accept(self,body):
  value=json.loads(body,object_pairs_hook=unique,parse_constant=lambda v:(_ for _ in()).throw(ValueError('SCENE_NONFINITE')))
  need(value.get('poseSource')=='ROOT_DURABLE_FDM_STATE'and value.get('sourceBinding')==self.source_binding,'EXACT_PINNED_POSE_SOURCE');need(value.get('format')=='aeris-sim-scene-frame'and value.get('version')==1 and value.get('mode')=='LIVE'and value.get('context')==self.context,'EXACT_CONTEXT')
  need(type(value.get('frame'))is int and value['frame']>=0 and(self.latest is None or value['frame']>self.latest['frame']),'MONOTONIC_VISUAL_FRAME')
  for key,n in(('positionNedM',3),('quaternionWxyz',4),('rpmEstimated',4)):
   need(type(value.get(key))is list and len(value[key])==n and all(type(x)in(int,float)and math.isfinite(x)for x in value[key]),'FINITE_'+key)
  ref=value['rawRef'];need(ref.get('frame')==value['frame']and type(ref.get('relativePath'))is str and __import__('re').fullmatch(r'journal/segment-[0-9]{6}\.jsonl',ref['relativePath'])is not None and type(ref.get('prefixBytes'))is int and ref['prefixBytes']>0,'RAW_PREFIX_REF')
  need(type(ref.get('throughSequence'))is int and(self.latest is None or ref['throughSequence']>self.latest['rawRef']['throughSequence'])and(self.latest is None or ref['relativePath']!=self.latest['rawRef']['relativePath']or ref['prefixBytes']>self.latest['rawRef']['prefixBytes']),'MONOTONIC_RAW_PREFIX');path=self.raw_root/ref['relativePath'];need(not any(p.is_symlink()for p in(path,*path.parents))and path.stat().st_size>=ref['prefixBytes'],'DURABLE_RAW_FILE_PREFIX')
  with path.open('rb')as file:
   start=max(0,ref['prefixBytes']-4096);file.seek(start);tail=file.read(ref['prefixBytes']-start)
  from .foundation.fdm09 import decode_line
  previous=ref.get('previousLogicalHeadSHA256');need(type(previous)is str and __import__('re').fullmatch('[a-f0-9]{64}',previous)is not None,'SOURCE_PREVIOUS_LOGICAL_HEAD')
  need(tail.endswith(b'\n'),'DURABLE_STAGE_TAIL');stored=tail.splitlines()[-1]+b'\n';physical_sha=ref.get('privatePhysicalStageSHA256');need(type(physical_sha)is str and __import__('re').fullmatch('[a-f0-9]{64}',physical_sha)is not None and type(ref.get('physicalStageBytes'))is int and 0<ref['physicalStageBytes']==len(stored)<=2048 and ref['prefixBytes']>=len(stored)and hashlib.sha256(stored).hexdigest()==physical_sha,'SOURCE_PHYSICAL_STAGE_BYTES_SHA')
  need(set(json.loads(stored,object_pairs_hook=unique))=={'fdm09'},'EXPECTED_MAIN_FDM09_STAGE_WRAPPER');record=json.loads(decode_line(stored,self.context['run'],self.context['epoch'],previous),object_pairs_hook=unique);b=record['body'];raw=json.dumps(b,sort_keys=True,separators=(',',':'),allow_nan=False).encode();actual=hashlib.sha256(bytes.fromhex(b['previous'])+raw).hexdigest()
  need(record['sha256']==actual==ref['headSHA256']and record['crc32']==format(zlib.crc32(raw),'08x')and b['seq']==ref['throughSequence']and b['kind']=='EVENT'and b['payload']['eventKind']=='STAGE'and b['payload']['data']['frame']==value['frame'],'ORIGINAL_STAGE_CRC_HEAD_FRAME')
  sample=int(value['sampleHostNs']);commit=int(value['committedHostNs']);need(0<=sample<=commit<=time.monotonic_ns(),'SAME_HOST_TIME_ORDER')
  # Private decode hints do not become browser/media-proof entropy. Public
  # byte-span + logical head remain cold-joinable to the complete stored stream.
  ref['physicalByteStart']=ref['prefixBytes']-ref['physicalStageBytes'];ref.pop('previousLogicalHeadSHA256');ref.pop('privatePhysicalStageSHA256');value['proofStatus']='LIVE_ROOT_VALIDATED_COLD_FULL_PREFIX_REQUIRED'
  self.latest=value;self.received+=1
 def _run(self):
  try:
   while not self.stop.is_set():
    readable,_,_=select.select([self.fd],[],[],.05)
    if not readable:continue
    raw=os.read(self.fd,min(4096,MAX_FRAME*2+8-len(self.pending)))
    if not raw:self.eof=True;need(not self.pending,'PARTIAL_FRAME_EOF');return
    self.pending.extend(raw);need(len(self.pending)<=MAX_FRAME*2+8,'READ_BUFFER_BOUND')
    while len(self.pending)>=4:
     length=struct.unpack('!I',self.pending[:4])[0];need(0<length<=MAX_FRAME,'READ_FRAME_BOUND')
     if len(self.pending)<length+4:break
     body=bytes(self.pending[4:4+length]);del self.pending[:4+length];self._accept(body)
  except BaseException as error:self.failure=type(error).__name__+':'+str(error)[:256];self.latest=None
 def snapshot(self):
  now=time.monotonic_ns()
  if self.failure or self.latest is None or self.eof:return {'available':False,'failure':self.failure or('SCENE_EOF'if self.eof else'SCENE_NOT_READY'),'rootNowNs':str(now),'flightAuthority':False}
  value=dict(self.latest);value['rootNowNs']=str(now);return {'available':True,'frame':value,'flightAuthority':False}
 def close(self):
  if self.closure is not None:return dict(self.closure)
  self.stop.set()
  if self.thread:self.thread.join(timeout=.1)
  need(self.thread is None or not self.thread.is_alive(),'READER_CLOSE_UNKNOWN');os.close(self.fd)
  self.closure={'receivedVisualFrames':self.received,'failure':self.failure,'EOF':self.eof,'physicsFramesDropped':0,'flightAcceptance':False};return dict(self.closure)
