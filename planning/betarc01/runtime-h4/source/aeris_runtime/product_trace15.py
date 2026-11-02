"""Fixed4KiB per-operation diagnostic tail; never flight or retry authority.

Only the first failed/late operation plus one predecessor is retained. Healthy
runs retain their final two operations, not full latency history. Stage timings
are inclusive/nested: their sums must not be added as end-to-end latency.
"""
from collections import deque
from contextlib import contextmanager
from pathlib import Path
import hashlib,json,os,struct,threading,time,re,zlib
MAGIC=b'PWST15\0\0';FILE=struct.Struct('<8sHB');RECORD=struct.Struct('<HH');STAGE=struct.Struct('<BIQQQQ')
MAX_FILE=4096;MAX_HEADER=768;MAX_META=768;MAX_RECORD=1568;MAX_ROWS=2;MAX_EVENTS=200000
CODES=('rpc_receive','rpc_parse','data_lock','rpc_validate','lock_thread','lock_file','quota_charge','ledger_serial','ledger_write','ledger_file_fsync','ledger_publish','ledger_dir_fsync','payload_data_write','payload_fsync','payload_dir_fsync','payload_write','lock_hold','ledger_save','reply_encode','reply_send','payload_file_fsync')
def encoded(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def error_text(e):return (type(e).__name__+':'+str(e)).encode('unicode_escape').decode('ascii')[:64]
class Operation:
 def __init__(self,owner,started,scope):
  self.owner=owner;self.meta={'s':0,'o':'UNKNOWN','p':'','q':None,'r':None,'b':started,'e':None,'d':None,'c':False,'f':None,'x':None,'v':scope,'u':0 if scope=='DIRECT_CALL'else 1,'k':False};self.stats={};self.events=0;self.error=None;self.finished=False
 @contextmanager
 def span(self,code):
  # Other existing StageTrace hooks are valid but not part of this fixed record.
  if code not in CODES:yield;return
  b=time.monotonic_ns();cpu=time.thread_time_ns();primary=None
  try:yield
  except BaseException as e:primary=e;raise
  finally:
   try:
    end=time.monotonic_ns();cost=time.thread_time_ns()-cpu;wall=end-b
    if not 0<=wall<2**63 or not 0<=cost<2**63 or self.events>=MAX_EVENTS:raise RuntimeError('PRODUCT_TRACE_TYPED_CLOCK_OR_EVENT_BOUND')
    self.events+=1;k=CODES.index(code);v=self.stats.setdefault(k,[0,0,0,0,0]);v[0]+=1;v[1]+=wall;v[2]=max(v[2],wall);v[3]+=cost;v[4]=max(v[4],cost)
   except BaseException as e:
    if self.error is None:self.error=e
    if primary is not None:primary.add_note('PRODUCT_TRACE_SECONDARY:'+error_text(e))
 def bind(self,request,raw=None):
  if type(request)is dict:
   self.meta['s']=request.get('sequence')if type(request.get('sequence'))is int and 0<=request['sequence']<=32769 else 0
   op=request.get('op');path=request.get('path');self.meta['o']=op[:24]if type(op)is str and bool(op)and op.isascii()else'INVALID_OP';self.meta['p']=path[:160]if type(path)is str and path.isascii()else'INVALID_PATH'
  self.meta['q']=hashlib.sha256(raw if raw is not None else encoded(request)).hexdigest();self.meta['k']=True
 def commit(self,value,ref=None):
  self.meta['c']=value
  if ref is not None:self.meta['f']=[ref['offset'],ref['bytes'],ref['sha256'],ref['writeSequence']]
 def check(self):
  if self.error is not None:raise self.error
 def finish(self,response=None,error=None,raw=None):
  if self.finished:raise RuntimeError('PRODUCT_TRACE_ONE_FINISH')
  self.finished=True;self.meta['e']=time.monotonic_ns()
  if response is not None:
   self.meta['r']=hashlib.sha256(raw if raw is not None else encoded(response)).hexdigest()
   if type(response)is dict:
    self.meta['c']=response.get('committed',self.meta['c'])
    if response.get('ref')is not None:self.commit(response.get('committed'),response['ref'])
    if response.get('ok')is False and error is None:self.meta['x']=str(response.get('error','FAILED_RESPONSE')).encode('unicode_escape').decode('ascii')[:64]
  if error is not None:self.meta['x']=error_text(error)
  if self.error is not None and self.meta['x']is None:self.meta['x']=error_text(self.error)
  self.owner.finish(self)
 def binary(self):
  raw=encoded(self.meta);stats=b''.join(STAGE.pack(code,*row)for code,row in sorted(self.stats.items()))
  if len(raw)>MAX_META or RECORD.size+len(raw)+len(stats)>MAX_RECORD:raise ValueError('PRODUCT_TRACE_RECORD_BOUND')
  return RECORD.pack(len(raw),len(self.stats))+raw+stats
class WriterTrace:
 def __init__(self,context):
  self.context=dict(context);self.pid=os.getpid();self.candidate=os.environ.get('AERIS_CANDIDATE_SHA256');self.rows=deque(maxlen=MAX_ROWS);self.total=0;self.after_frozen=0;self.frozen=False;self.failure=None;self.flushed=False;self.lock=threading.RLock()
 def begin(self,started=None,scope='SOCKET_BODY'):
  return Operation(self,time.monotonic_ns()if started is None else started,scope)
 def finish(self,op):
  with self.lock:
   if self.frozen:self.after_frozen+=1;return
   try:
    raw=op.binary();self.total+=1
    if op.meta['x']is not None:
     if self.rows:self.rows=deque([self.rows[-1]],maxlen=MAX_ROWS)
     self.rows.append(raw);self.frozen=True
    else:self.rows.append(raw)
   except BaseException as e:
    if self.failure is None:self.failure=e
 def check(self):
  if self.failure is not None:raise self.failure
 def snapshot(self):
  with self.lock:
   self.check();header={'format':'aeris-product-writer-stage15','version':1,'pid':self.pid,'candidate':self.candidate,'context':self.context,'total':self.total,'overwritten':max(0,self.total-len(self.rows)),'afterFrozen':self.after_frozen,'frozen':self.frozen,'coverage':'FIRST_FAILED_PLUS_ONE_PRIOR_OR_FINAL_TWO','fullHistory':False,'nestedInclusiveStages':True,'requestResponseDigestScope':'EXACT_SOCKET_JSON_BODY_OR_ENCODED_DIRECT_CALL','authority':False};raw=encoded(header)
   if len(raw)>MAX_HEADER:raise ValueError('PRODUCT_TRACE_HEADER_BOUND')
   out=FILE.pack(MAGIC,len(raw),len(self.rows))+raw+b''.join(self.rows);out+=struct.pack('<I',zlib.crc32(out)&0xffffffff)
   if len(out)>MAX_FILE:raise ValueError('PRODUCT_TRACE_FILE4KiB')
   return out
 def flush(self,budget):
  if self.flushed:raise RuntimeError('PRODUCT_TRACE_NO_SECOND_FLUSH')
  raw=self.snapshot();path=budget.evidence/'reports/product-writer-stage15.bin'
  if not path.parent.is_dir()or path.parent.is_symlink():raise RuntimeError('PRODUCT_TRACE_PREFUNDED_REPORT_DIRECTORY_REQUIRED')
  ref=budget.write('closure',path,raw,closing=True);self.flushed=True
  return {'path':'reports/product-writer-stage15.bin','offset':0,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'writeSequence':ref['writeSequence'],'coverage':'BOUNDED_NOT_FULL_HISTORY','authority':False}
def strict(raw):
 def pairs(xs):
  d={}
  for k,v in xs:
   if k in d:raise ValueError('PRODUCT_TRACE_DUPLICATE_JSON_KEY')
   d[k]=v
  return d
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in()).throw(ValueError('PRODUCT_TRACE_NONFINITE')))
def _integer(v,minimum=0):return type(v)is int and minimum<=v<2**63
def _hex(v):return type(v)is str and re.fullmatch('[a-f0-9]{64}',v)is not None
def decode(raw,*,candidate=None,context=None,pid=None,expected_sha256=None):
 if type(raw)is not bytes or not FILE.size+4<=len(raw)<=MAX_FILE:raise ValueError('PRODUCT_TRACE_FILE_BOUND')
 if expected_sha256 is not None and hashlib.sha256(raw).hexdigest()!=expected_sha256:raise ValueError('PRODUCT_TRACE_FILE_SHA')
 if zlib.crc32(raw[:-4])&0xffffffff!=struct.unpack('<I',raw[-4:])[0]:raise ValueError('PRODUCT_TRACE_CRC')
 end=len(raw)-4;magic,hn,n=FILE.unpack_from(raw);at=FILE.size
 if magic!=MAGIC or not 0<hn<=MAX_HEADER or not 0<=n<=MAX_ROWS or at+hn>end:raise ValueError('PRODUCT_TRACE_HEADER')
 header=strict(raw[at:at+hn]);at+=hn
 fields={'format','version','pid','candidate','context','total','overwritten','afterFrozen','frozen','coverage','fullHistory','nestedInclusiveStages','requestResponseDigestScope','authority'}
 if type(header)is not dict or set(header)!=fields or header['format']!='aeris-product-writer-stage15'or type(header['version'])is not int or header['version']!=1 or not _integer(header['pid'],1)or header['candidate']is not None and not _hex(header['candidate']):raise ValueError('PRODUCT_TRACE_HEADER_SCHEMA')
 ctx=header['context']
 if type(ctx)is not dict or set(ctx)!={'run','epoch','boot','operator','generation','profileId'}or any(type(v)is not str or not 0<len(v)<=64 for v in ctx.values())or len(encoded(ctx))>256:raise ValueError('PRODUCT_TRACE_CONTEXT_SCHEMA')
 if any(not _integer(header[k])or header[k]>32769 for k in('total','overwritten','afterFrozen'))or n!=min(header['total'],MAX_ROWS)or header['overwritten']!=header['total']-n or type(header['frozen'])is not bool or header['coverage']!='FIRST_FAILED_PLUS_ONE_PRIOR_OR_FINAL_TWO'or header['fullHistory']is not False or header['nestedInclusiveStages']is not True or header['authority']is not False or header['requestResponseDigestScope']!='EXACT_SOCKET_JSON_BODY_OR_ENCODED_DIRECT_CALL':raise ValueError('PRODUCT_TRACE_COVERAGE_SCHEMA')
 if candidate is not None and header['candidate']!=candidate or context is not None and ctx!=context or pid is not None and header['pid']!=pid:raise ValueError('PRODUCT_TRACE_CONTEXT')
 rows=[];previous_end=0
 for _ in range(n):
  record_start=at
  if at+RECORD.size>end:raise ValueError('PRODUCT_TRACE_PARTIAL_RECORD')
  mn,count=RECORD.unpack_from(raw,at);at+=RECORD.size
  if not 0<mn<=MAX_META or count>len(CODES)or at+mn+count*STAGE.size>end or RECORD.size+mn+count*STAGE.size>MAX_RECORD:raise ValueError('PRODUCT_TRACE_RECORD_BOUND')
  meta=strict(raw[at:at+mn]);at+=mn;stats={}
  if type(meta)is not dict or set(meta)!={'s','o','p','q','r','b','e','d','c','f','x','v','u','k'}or not _integer(meta['s'])or meta['s']>32769 or type(meta['o'])is not str or not meta['o'].isascii()or not 0<len(meta['o'])<=24 or type(meta['p'])is not str or not meta['p'].isascii()or len(meta['p'])>160:raise ValueError('PRODUCT_TRACE_META_SCHEMA')
  if any(meta[k]is not None and not _hex(meta[k])for k in('q','r'))or type(meta['k'])is not bool or meta['k']and meta['q']is None or type(meta['u'])is not int or meta['u']not in(0,1,2,3)or meta['u']in(2,3)and meta['r']is None or meta['v']not in('DIRECT_CALL','SOCKET_BODY')or meta['v']=='DIRECT_CALL'and meta['u']!=0:raise ValueError('PRODUCT_TRACE_CAPTURE_DISPOSITION')
  if not _integer(meta['b'])or not _integer(meta['e'])or not previous_end<=meta['e']or meta['b']>meta['e']or meta['d']is not None and(not _integer(meta['d'])or not meta['b']<=meta['d']<=meta['e'])or meta['c']is not None and type(meta['c'])is not bool or meta['x']is not None and(type(meta['x'])is not str or not meta['x'].isascii()or len(meta['x'])>96):raise ValueError('PRODUCT_TRACE_OPERATION_CLOCK_OR_OUTCOME')
  previous_end=meta['e'];ref=meta['f']
  if ref is not None and(type(ref)is not list or len(ref)!=4 or not _integer(ref[0])or not _integer(ref[1],1)or ref[1]>65536 or not _hex(ref[2])or not _integer(ref[3],1)or meta['c']is not True):raise ValueError('PRODUCT_TRACE_COMMIT_REF')
  prior_code=-1
  for _ in range(count):
   code,*v=STAGE.unpack_from(raw,at);at+=STAGE.size
   if not prior_code<code<len(CODES)or not 1<=v[0]<=MAX_EVENTS or any(x>=2**63 for x in v[1:])or v[2]>v[1]or v[4]>v[3]:raise ValueError('PRODUCT_TRACE_STAGE_SCHEMA')
   prior_code=code;stats[CODES[code]]=dict(zip(('count','sumWallNs','maxWallNs','sumThreadCPUNs','maxThreadCPUNs'),v))
  rows.append({'operation':meta,'stages':stats})
 if at!=end:raise ValueError('PRODUCT_TRACE_TRAILING_BYTES')
 if header['frozen']and(not rows or rows[-1]['operation']['x']is None)or not header['frozen']and any(v['operation']['x']is not None for v in rows):raise ValueError('PRODUCT_TRACE_FAILURE_FREEZE_SCHEMA')
 return {'header':header,'rows':rows,'fullHistory':False,'authority':False,'replyDispositionCodes':{'0':'DIRECT_NO_SOCKET','1':'SEND_NOT_ATTEMPTED','2':'SENDALL_RETURNED_NOT_DELIVERY_PROOF','3':'SEND_ERROR_PARTIAL_OR_UNKNOWN'}}
