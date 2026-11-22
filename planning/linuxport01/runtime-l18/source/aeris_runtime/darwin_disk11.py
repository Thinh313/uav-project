"""Bounded, non-authorizing host disk observations; persistence only at closure.

Disk-write counters are correlated IO, not allocated space or a causal verdict.
ABI: installed Apple SDK libproc.h and sys/resource.h, rusage_info_v2 (160B).
No process command lines, environment, file contents or recursive host scan.
"""
from pathlib import Path
from collections import deque
import ctypes,errno,hashlib,json,os,stat,struct,sys,threading,time,zlib

MAX_PIDS=1024; TOP=16; PATHS=24; RING=32; HEADER_MAX=4096; FILE_MAX=65536
INTERVAL_NS=1_000_000_000; SAMPLE_NS=500_000_000; UNKNOWN=2**64-1
MAGIC=b'AHDISK11'; FILE=struct.Struct('>8sI'); FRAME=struct.Struct('>II')
PROCESS=struct.Struct('>IIQ16sQQQ8s'); PHYSICAL=struct.Struct('>HHiQQQ')
SAMPLE=struct.Struct('>QQQQIIIIIIIIQQQIQHH')
WORST_BYTES=FILE.size+HEADER_MAX+RING*(FRAME.size+SAMPLE.size+TOP*PROCESS.size+PATHS*PHYSICAL.size)
assert PROCESS.size==64 and PHYSICAL.size==32 and SAMPLE.size==104 and WORST_BYTES<=FILE_MAX
P_UNKNOWN=1;P_RESET=2;P_REUSED=4;P_NAME_TRUNCATED=8;P_NAME_UNAVAILABLE=16;P_IDENTITY_UNAVAILABLE=32
F_PRESENT=1;F_MISSING=2;F_ERROR=3;F_SYMLINK=4;F_NOT_REGULAR=5
S_TRUNCATED=1;S_OVERRUN=2;S_PROBE_FAILURE=4

class RUsageV2(ctypes.Structure):
 _fields_=[('uuid',ctypes.c_ubyte*16)]+[(n,ctypes.c_uint64)for n in('user','system','pkg_idle','interrupt','pageins','wired','resident','footprint','start','exit','child_user','child_system','child_idle','child_interrupt','child_pageins','child_elapsed','read','written')]
assert ctypes.sizeof(RUsageV2)==160

class SwapUsage(ctypes.Structure):
 _fields_=[('total',ctypes.c_uint64),('avail',ctypes.c_uint64),('used',ctypes.c_uint64),('pagesize',ctypes.c_int),('encrypted',ctypes.c_int)]

def fixed_paths(spec):
 """Exact declared candidates, including absent paths, never a recursive scan."""
 avd=Path(spec['AVD']).absolute();home=Path.home()
 rows=[avd/n for n in('userdata-qemu.img.qcow2','userdata-qemu.img','cache.img.qcow2','cache.img','sdcard.img','encryptionkey.img','snapshots/default_boot/ram.img')]
 rows += [home/'Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw',home/'Library/Group Containers/group.com.docker/Data/vms/0/data/Docker.raw']
 rows += [Path('/private/var/vm')/('swapfile'+str(n))for n in range(8)]
 if len(rows)>PATHS or len(set(map(str,rows)))!=len(rows):raise ValueError('HOSTDISK11_PATH_SET')
 return rows

class DarwinProbe:
 """Read-only CDLL calls release the GIL. Missing data is an errno, not zero."""
 def __init__(self,volume,*,now=time.monotonic_ns):
  if sys.platform!='darwin':raise RuntimeError('HOSTDISK11_DARWIN_ONLY')
  self.volume=Path(volume);self.now=now;self.lib=ctypes.CDLL('/usr/lib/libproc.dylib',use_errno=True);self.system=ctypes.CDLL(None,use_errno=True)
  self.lib.proc_listallpids.argtypes=[ctypes.c_void_p,ctypes.c_int];self.lib.proc_listallpids.restype=ctypes.c_int
  self.lib.proc_pid_rusage.argtypes=[ctypes.c_int,ctypes.c_int,ctypes.c_void_p];self.lib.proc_pid_rusage.restype=ctypes.c_int
  self.lib.proc_name.argtypes=[ctypes.c_int,ctypes.c_void_p,ctypes.c_uint32];self.lib.proc_name.restype=ctypes.c_int
  self.system.sysctlbyname.argtypes=[ctypes.c_char_p,ctypes.c_void_p,ctypes.POINTER(ctypes.c_size_t),ctypes.c_void_p,ctypes.c_size_t];self.system.sysctlbyname.restype=ctypes.c_int
 def volume_free(self):
  value=os.statvfs(self.volume);return value.f_bavail*value.f_frsize
 def volume_device(self):return self.volume.stat().st_dev
 def volume_inode(self):return self.volume.stat().st_ino
 def swap_used(self):
  value=SwapUsage();n=ctypes.c_size_t(ctypes.sizeof(value));ctypes.set_errno(0)
  if self.system.sysctlbyname(b'vm.swapusage',ctypes.byref(value),ctypes.byref(n),None,0)!=0 or n.value!=ctypes.sizeof(value):return UNKNOWN
  return value.used
 def pids(self):
  values=(ctypes.c_int*MAX_PIDS)();ctypes.set_errno(0);n=self.lib.proc_listallpids(values,ctypes.sizeof(values))
  if n<=0:raise OSError(ctypes.get_errno()or errno.EIO,'proc_listallpids')
  return sorted(set(p for p in values[:min(n,MAX_PIDS)]if p>0)),n>=MAX_PIDS
 def process(self,pid):
  value=RUsageV2();ctypes.set_errno(0)
  if self.lib.proc_pid_rusage(pid,2,ctypes.byref(value))!=0:raise OSError(ctypes.get_errno(),'proc_pid_rusage')
  name=ctypes.create_string_buffer(64);n=self.lib.proc_name(pid,name,64);raw=name.value if n>0 else b''
  return {'pid':pid,'start':value.start,'uuid':bytes(value.uuid),'written':value.written,'footprint':value.footprint,'name':raw[:8],'nameTruncated':len(raw)>8,'nameUnavailable':n<=0}
 def physical(self,path):
  try:
   if any(p.is_symlink()for p in[path,*path.parents]):return(F_SYMLINK,0,0,0,0)
   s=path.lstat()
   if not stat.S_ISREG(s.st_mode):return(F_NOT_REGULAR,0,s.st_dev,s.st_ino,0)
   return(F_PRESENT,0,s.st_dev,s.st_ino,s.st_blocks*512)
  except FileNotFoundError:return(F_MISSING,errno.ENOENT,0,0,0)
  except OSError as e:return(F_ERROR,e.errno or errno.EIO,0,0,0)

def uint(v):return type(v)is int and 0<=v<UNKNOWN
def validate_process(value):
 if type(value)is not dict or any(not uint(value.get(k))for k in('pid','start','written','footprint'))or value['pid']>2**32-1 or not value['pid']or type(value.get('uuid'))is not bytes or len(value['uuid'])!=16 or type(value.get('name'))is not bytes or len(value['name'])>8:raise ValueError('HOSTDISK11_PROCESS_TYPES')
 return value

class HostDiskObserver:
 def __init__(self,volume,paths,*,candidate,source,probe=None,now=time.monotonic_ns,cpu=time.thread_time_ns,scope='CANDIDATE_RUNTIME_OBSERVER'):
  if len(paths)>PATHS or len(set(map(str,paths)))!=len(paths)or any(not Path(p).is_absolute()or '..'in Path(p).parts for p in paths):raise ValueError('HOSTDISK11_FIXED_PATHS24')
  if scope not in('CANDIDATE_RUNTIME_OBSERVER','PASSIVE_SOURCE_PROBE')or(scope=='CANDIDATE_RUNTIME_OBSERVER'and candidate=='0'*64):raise ValueError('HOSTDISK11_SCOPE')
  self.scope=scope;self.cpu=cpu;self.volume=Path(volume);self.paths=list(map(Path,paths));self.candidate=candidate;self.source=source;self.now=now;self.probe=probe if probe is not None else DarwinProbe(volume,now=now);self.rows=deque(maxlen=RING);self.previous={};self.total=0;self.overwritten=0;self.skipped=0;self.failure=None;self.done=threading.Event();self.thread=None;self.lock=threading.Lock();self.flushed=False;self.started=None;self.stopped=None;self.retired=False;self.retired_at=None;self.after_retirement=0
  try:self.volume_device=self.probe.volume_device()
  except BaseException:self.volume_device=UNKNOWN
  try:self.volume_inode=self.probe.volume_inode()
  except BaseException:self.volume_inode=UNKNOWN
 def sample(self):
  with self.lock:
   if self.retired:self.after_retirement+=1;return None
  begin=self.now();cpu_begin=self.cpu();deadline=begin+SAMPLE_NS;flags=0;errors=0;unreadable=0;first=0;resets=0;probed=0;ranked=[];all_delta=0;current={}
  try:free=self.probe.volume_free()
  except BaseException:free=UNKNOWN;flags|=S_PROBE_FAILURE;errors+=1
  try:swap=self.probe.swap_used()
  except BaseException:swap=UNKNOWN;flags|=S_PROBE_FAILURE;errors+=1
  try:pids,truncated=self.probe.pids()
  except BaseException:pids=[];truncated=True;flags|=S_PROBE_FAILURE;errors+=1
  if type(pids)is not list or len(pids)>MAX_PIDS or any(type(v)is not int or not 0<v<2**32 for v in pids)or len(set(pids))!=len(pids):raise ValueError('HOSTDISK11_ENUMERATION1024')
  if truncated:flags|=S_TRUNCATED
  for pid in pids:
   if self.now()>=deadline:flags|=S_OVERRUN;break
   try:v=validate_process(self.probe.process(pid));probed+=1
   except (OSError,ValueError):unreadable+=1;continue
   if v['pid']!=pid:raise ValueError('HOSTDISK11_PID_RETURN_BINDING')
   key=(pid,v['start'],v['uuid']);current[key]=v['written'];prev=self.previous.get(key,UNKNOWN);pf=P_NAME_TRUNCATED if v.get('nameTruncated')else 0
   if v.get('nameUnavailable'):pf|=P_NAME_UNAVAILABLE
   if not v['start']or v['uuid']==b'\0'*16:pf|=P_IDENTITY_UNAVAILABLE;prev=UNKNOWN
   if prev==UNKNOWN:
    pf|=P_UNKNOWN;first+=1
    if any(k[0]==pid for k in self.previous):pf|=P_REUSED
    delta=None
   elif v['written']<prev:pf|=P_RESET;resets+=1;delta=None
   else:delta=v['written']-prev;all_delta+=delta
   if all_delta>=UNKNOWN:raise ValueError('HOSTDISK11_AGGREGATE_OVERFLOW_UNKNOWN')
   ranked.append((0 if delta is None else delta,pid,pf,v['start'],v['uuid'],prev,v['written'],v['footprint'],v['name']))
  ranked.sort(key=lambda x:(-x[0],x[1]));selected=ranked[:TOP];other=sum(v[0]for v in ranked[TOP:]);physical=[]
  for index,path in enumerate(self.paths):
   if self.now()>=deadline:flags|=S_OVERRUN;physical.append((index,F_ERROR,errno.ETIMEDOUT,0,0,0));continue
   try:state,err,device,inode,allocated=self.probe.physical(path)
   except BaseException:state,err,device,inode,allocated=F_ERROR,errno.EIO,0,0,0
   if state not in(F_PRESENT,F_MISSING,F_ERROR,F_SYMLINK,F_NOT_REGULAR)or any(type(x)is not int or x<0 for x in(device,inode,allocated))or type(err)is not int:raise ValueError('HOSTDISK11_PHYSICAL_TYPES')
   physical.append((index,state,err,device,inode,allocated))
  end=self.now()
  if end-begin>SAMPLE_NS:flags|=S_OVERRUN
  with self.lock:
   if self.retired:self.after_retirement+=1;return None
   self.total+=1
   if self.total>2048:raise ValueError('HOSTDISK11_TOTAL2048')
   if len(self.rows)==RING:self.overwritten+=1
   self.rows.append({'begin':begin,'end':end,'free':free,'swap':swap,'enumerated':len(pids),'probed':probed,'errors':errors,'truncated':int(bool(truncated)),'unreadable':unreadable,'first':first,'resets':resets,'skipped':self.skipped,'allDelta':all_delta,'otherDelta':other,'sequence':self.total,'flags':flags,'threadCPU':max(0,self.cpu()-cpu_begin),'processes':selected,'physical':physical})
   self.previous=current
  return self.rows[-1]
 def _run(self):
  target=self.now()
  try:
   while not self.done.is_set():
    self.sample();target+=INTERVAL_NS;remaining=target-self.now()
    if remaining<0:self.skipped+=max(1,(-remaining)//INTERVAL_NS+1);target=self.now()+INTERVAL_NS;remaining=INTERVAL_NS
    self.done.wait(remaining/1e9)
  except BaseException as e:self.failure=type(e).__name__+':'+str(e)[:192];self.done.set()
 def start(self):
  if self.thread is not None:raise RuntimeError('HOSTDISK11_ONE_START')
  self.started=self.now();self.thread=threading.Thread(target=self._run,name='aeris-host-disk-diagnostic11',daemon=True);self.thread.start()
 def retire(self):
  """Nonblocking first-fault freeze; cleanup cannot evict the fault window."""
  with self.lock:
   if not self.retired:self.retired=True;self.retired_at=self.now();self.done.set()
 def stop(self):
  self.retire()
  if self.thread is not None:self.thread.join(timeout=1)
  if self.thread is not None and self.thread.is_alive():raise RuntimeError('HOSTDISK11_STOP_INCOMPLETE')
  self.stopped=self.now()
 def export(self):
  if self.thread is not None and self.thread.is_alive():raise RuntimeError('HOSTDISK11_EXPORT_ACTIVE')
  with self.lock:
   header={'format':'aeris-host-disk-attribution','version':1,'scope':self.scope,'candidateSHA256':self.candidate,'sourceSHA256':self.source,'PID':os.getpid(),'volume':str(self.volume),'volumeDevice':self.volume_device,'volumePathInode':self.volume_inode,'paths':list(map(str,self.paths)),'total':self.total,'overwritten':self.overwritten,'skipped':self.skipped,'failure':self.failure,'startedHostNs':self.started,'stoppedHostNs':self.stopped,'retiredAtHostNs':self.retired_at,'inflightDiscardedAfterRetirement':self.after_retirement,'rows':len(self.rows),'coverage':'FROZEN_FINAL32_SAMPLES_TOP16_NOT_ALL_HISTORY','attribution':'IO_CORRELATION_NOT_ALLOCATED_SPACE_OR_CAUSAL_PROOF','otherDelta':'PRODUCER_OBSERVED_AGGREGATE_INDIVIDUAL_RAW_ROWS_NOT_RETAINED','name':'PREFIX8_BYTES_NOT_FULL_PROCESS_NAME;UNAVAILABLE_FLAG16','swap':'GLOBAL_VM_SWAPUSED_METADATA_NOT_SAME_VOLUME_ALLOCATED_BLOCKS','cadenceNs':INTERVAL_NS,'sampleDeadlineNs':SAMPLE_NS,'recordLayouts':['SAMPLE104','PROCESS64','PHYSICAL32']};h=json.dumps(header,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
   if len(h)>HEADER_MAX:raise ValueError('HOSTDISK11_HEADER4096')
   chunks=[FILE.pack(MAGIC,len(h)),h]
   for row in self.rows:
    raw=SAMPLE.pack(*[row[k]for k in('begin','end','free','swap','enumerated','probed','errors','truncated','unreadable','first','resets','skipped','allDelta','otherDelta','sequence','flags','threadCPU')],len(row['processes']),len(row['physical']))
    for delta,pid,flags,start,uuid,prev,current,footprint,name in row['processes']:raw+=PROCESS.pack(pid,flags,start,uuid,prev,current,footprint,name.ljust(8,b'\0'))
    for value in row['physical']:raw+=PHYSICAL.pack(*value)
    chunks.extend((FRAME.pack(len(raw),zlib.crc32(raw)&0xffffffff),raw))
   result=b''.join(chunks)
   if len(result)>FILE_MAX:raise ValueError('HOSTDISK11_FILE64KiB')
   return result
 def flush(self,budget,path):
  if self.flushed:raise RuntimeError('HOSTDISK11_ONE_FLUSH')
  raw=self.export();result=budget.write('closure',path,raw,closing=True);self.flushed=True
  if self.failure is not None or not self.rows:raise RuntimeError('HOSTDISK11_CAPTURE_INCOMPLETE_PRESERVED')
  return result

def decode(raw,*,candidate=None,source=None):
 if type(raw)is not bytes or not FILE.size<=len(raw)<=FILE_MAX:raise ValueError('HOSTDISK11_FILE')
 magic,hn=FILE.unpack_from(raw);at=FILE.size
 if magic!=MAGIC or not 0<hn<=HEADER_MAX or at+hn>len(raw):raise ValueError('HOSTDISK11_HEADER')
 def pairs(xs):
  value={}
  for k,v in xs:
   if k in value:raise ValueError('HOSTDISK11_DUPLICATE')
   value[k]=v
  return value
 h=json.loads(raw[at:at+hn],object_pairs_hook=pairs,parse_constant=lambda v:(_ for _ in()).throw(ValueError('HOSTDISK11_NONFINITE')));at+=hn
 if type(h)is not dict or h.get('format')!='aeris-host-disk-attribution'or type(h.get('version'))is not int or h['version']!=1 or type(h.get('rows'))is not int or not 0<=h['rows']<=RING or type(h.get('paths'))is not list or len(h['paths'])>PATHS or any(type(p)is not str or not Path(p).is_absolute()or '..'in Path(p).parts for p in h['paths'])or len(set(h['paths']))!=len(h['paths'])or h.get('cadenceNs')!=INTERVAL_NS or h.get('sampleDeadlineNs')!=SAMPLE_NS or type(h.get('total'))is not int or type(h.get('overwritten'))is not int or not 0<=h['overwritten']<=h['total']<=2048 or type(h.get('volumeDevice'))is not int or not 0<=h['volumeDevice']<=UNKNOWN:raise ValueError('HOSTDISK11_SCHEMA')
 if h.get('scope')not in('CANDIDATE_RUNTIME_OBSERVER','PASSIVE_SOURCE_PROBE')or h['scope']=='CANDIDATE_RUNTIME_OBSERVER'and h.get('candidateSHA256')=='0'*64:raise ValueError('HOSTDISK11_SCOPE')
 for key in('candidateSHA256','sourceSHA256'):
  if type(h.get(key))is not str or len(h[key])!=64 or any(c not in'0123456789abcdef'for c in h[key]):raise ValueError('HOSTDISK11_IDENTITY_SHA')
 if candidate is not None and h.get('candidateSHA256')!=candidate or source is not None and h.get('sourceSHA256')!=source:raise ValueError('HOSTDISK11_SOURCE')
 rows=[];previous_sequence=0
 for _ in range(h['rows']):
  if at+FRAME.size>len(raw):raise ValueError('HOSTDISK11_PARTIAL')
  n,crc=FRAME.unpack_from(raw,at);at+=FRAME.size
  if not SAMPLE.size<=n<=SAMPLE.size+TOP*PROCESS.size+PATHS*PHYSICAL.size or at+n>len(raw):raise ValueError('HOSTDISK11_FRAME_BOUND')
  body=raw[at:at+n];at+=n
  if zlib.crc32(body)&0xffffffff!=crc:raise ValueError('HOSTDISK11_CRC')
  values=SAMPLE.unpack_from(body);names=('begin','end','free','swap','enumerated','probed','errors','truncated','unreadable','first','resets','skipped','allDelta','otherDelta','sequence','flags','threadCPU');row=dict(zip(names,values[:17]));pn,fn=values[-2:];offset=SAMPLE.size
  if row['sequence']<=previous_sequence or row['end']<row['begin']or pn>TOP or fn>PATHS or fn!=len(h['paths'])or len(body)!=SAMPLE.size+pn*PROCESS.size+fn*PHYSICAL.size or row['enumerated']>MAX_PIDS or row['probed']>row['enumerated']or row['otherDelta']>row['allDelta']:raise ValueError('HOSTDISK11_ROW_TYPES')
  previous_sequence=row['sequence'];processes=[];selected_delta=0;seen_pids=set()
  for _ in range(pn):
   pid,flags,start,uuid,before,current,footprint,name=PROCESS.unpack_from(body,offset);offset+=PROCESS.size
   if flags&~63 or not pid or pid in seen_pids or flags&P_REUSED and not flags&P_UNKNOWN or flags&P_UNKNOWN and flags&P_RESET or flags&P_NAME_UNAVAILABLE and name!=b'\0'*8:raise ValueError('HOSTDISK11_PROCESS_FLAGS')
   seen_pids.add(pid)
   delta=None if flags&(P_UNKNOWN|P_RESET)else current-before
   if flags&P_IDENTITY_UNAVAILABLE and not flags&P_UNKNOWN or flags&P_UNKNOWN and before!=UNKNOWN or flags&P_RESET and not current<before or delta is not None and delta<0:raise ValueError('HOSTDISK11_COUNTER_CAUSALITY')
   if delta is not None:selected_delta+=delta
   processes.append({'pid':pid,'start':start,'uuidHex':uuid.hex(),'previousWritten':None if before==UNKNOWN else before,'currentWritten':current,'writeDelta':delta,'flags':flags,'footprint':footprint,'namePrefix8Hex':name.hex()})
  if selected_delta+row['otherDelta']!=row['allDelta']:raise ValueError('HOSTDISK11_DELTA_CONSERVATION')
  physical=[]
  for expected in range(fn):
   index,state,err,dev,inode,allocated=PHYSICAL.unpack_from(body,offset);offset+=PHYSICAL.size
   if index!=expected or err<0 or state not in(F_PRESENT,F_MISSING,F_ERROR,F_SYMLINK,F_NOT_REGULAR)or state==F_PRESENT and err!=0 or state in(F_MISSING,F_ERROR,F_SYMLINK)and(dev or inode or allocated):raise ValueError('HOSTDISK11_PATH_STATE')
   physical.append({'index':index,'status':state,'errno':err,'device':dev,'inode':inode,'allocatedBytes':allocated})
  row['processes']=processes;row['physical']=physical;rows.append(row)
 if at!=len(raw)or rows and rows[-1]['sequence']!=h['total']or h['total']-len(rows)!=h['overwritten']:raise ValueError('HOSTDISK11_TRAILING_OR_RETENTION')
 changes=[]
 for before,current in zip(rows,rows[1:]):
  known_growth=0;paths=[];seen=set()
  for a,b in zip(before['physical'],current['physical']):
   same=a['status']==b['status']==F_PRESENT and(a['device'],a['inode'])==(b['device'],b['inode'])
   delta=b['allocatedBytes']-a['allocatedBytes']if same else None
   identity=(b['device'],b['inode']);same_volume=b['device']==h['volumeDevice']and h['volumeDevice']!=UNKNOWN;duplicate=identity in seen
   if same and same_volume and not duplicate:known_growth+=max(0,delta);seen.add(identity)
   paths.append({'index':b['index'],'sameInodeAllocatedDelta':delta,'sameObservedVolume':same_volume,'duplicateInodeNotDoubleCounted':duplicate,'replacementDeletionOrUnknown':not same})
  loss=None if UNKNOWN in(before['free'],current['free'])else before['free']-current['free']
  changes.append({'fromSequence':before['sequence'],'toSequence':current['sequence'],'globalFreeDeclineBytes':loss,'observedPositiveSameInodeGrowthBytes':known_growth,'unexplainedDifferenceBytes':None if loss is None else loss-known_growth,'physicalPathDeltas':paths,'processAttribution':'IO_CORRELATED_ONLY_CAUSAL_PROCESS_UNKNOWN','allocationCoverage':'DECLARED_PATHS_ONLY;COW_SNAPSHOTS_PURGEABLE_DELETED_OPEN_FILES_AND_UNOBSERVED_PROCESSES_UNKNOWN'})
 return {'header':h,'rows':rows,'changes':changes,'authority':False,'causalProcess':'UNKNOWN'}
