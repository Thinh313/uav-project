"""Real host observations, bounded pending audit and read-only local health.

Only the original DiskGuard supplies disk observations. Internal 100ms sampling
retains its original 192-sample window; durable diagnostic rows keep the original
2Hz cadence. This is separate from lossless, fsync-before-sensor flight evidence.
"""
from pathlib import Path
import hashlib,json,math,os,queue,re,secrets,socket,stat,struct,sys,threading,time
from .admission import DiskGuard,DISK_POLICY
from .cleanup import cleanup
from .metadata_budget import capture_command,MetadataBudget
from .stage_trace import StageTrace
from .paths import repository
FRESH_NS=2_000_000_000
QUEUE_ROWS=512
ROW_BYTES=1024
MAX_PENDING=QUEUE_ROWS+8+3
HEADER=struct.Struct('<IBH')
DISK_ROW=struct.Struct('<QQQddIQq')
INVENTORY_INTERVAL_NS=5_000_000_000
INVENTORY_DEADLINE_NS=2_000_000_000
INVENTORY_MAX_AGE_NS=7_000_000_000
INVENTORY_ROW_LIMIT={'guardian':421,'monitor':211}
POWER_ROW=struct.Struct('<QQBBHH')
AUDIT_LEASE={'guardian':2*2**20,'monitor':2**20}
ROW_LIMIT={'guardian':4200,'monitor':2100}

def source_sha():return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
def _json(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()+b'\n'
def _error(e):return type(e).__name__+':'+str(e)[:512]
def _strict(raw):
 def pairs(xs):
  d={}
  for k,v in xs:
   if k in d:raise ValueError('HOST_HEALTH_DUPLICATE_JSON_KEY')
   d[k]=v
  return d
 def bad(v):raise ValueError('HOST_HEALTH_NONFINITE_JSON')
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=bad)
def _int(v,minimum=0):return type(v)is int and minimum<=v<2**63
def _hex(v,n=64):return type(v)is str and re.fullmatch('[a-f0-9]{%d}'%n,v)is not None
def budget_binding(budget):
 if type(budget)is not MetadataBudget:raise ValueError('HOST_HEALTH_EXACT_BUDGET_BINDING')
 state=budget.snapshot()
 return {'budgetSourceIdentity':state['sourceIdentity'],'budgetRoot':state['budgetRoot'],'evidenceRoot':state['evidenceRoot']}
def _inventory_counters(c,owner):
 from .policy import campaign_budget
 limits={'metadataBytes':64*2**20,'exportBytes':192*2**20,'AVDPositiveGrowthBytes':512*2**20,'artifactBytes':8*2**20,'taskAllocatedBytes':campaign_budget()['taskHardPeakBytes']}
 if type(c)is not dict or not _int(c.get('metadataAccountingUpperBoundAtScan'))or not _int(c.get('metadataAccountingWriteSequenceAtScan'))or not _int(c.get('metadataBytes'))or c['metadataBytes']>c['metadataAccountingUpperBoundAtScan']:raise ValueError('HOST_INVENTORY_ORIGINAL_SCAN_ACCOUNTING')
 if type(c)is not dict or any(not _int(c.get(k))or c[k]>v for k,v in limits.items()):raise ValueError('HOST_REQUIRED_ORIGINAL_INVENTORY_CAPS')
 if owner=='monitor':
  for k,v in {'nativePhysicalBytes':160*2**20,'nativeLogicalBytes':512*2**20,'checkpointArchiveBytes':512*1024,'checkpointArchiveCount':8}.items():
   if k in c and(not _int(c[k])or c[k]>v):raise ValueError('HOST_REQUIRED_ORIGINAL_NATIVE_CAPS')
 return c
def _binding(b):
 if type(b)is not dict or set(b)!={'version','instance','pid','processStart','guardianSourceSHA256','healthSourceSHA256','budgetSourceIdentity','budgetRoot','evidenceRoot'}or type(b['version'])is not int or b['version']!=1 or not _int(b['pid'],1)or not _hex(b['instance'],32)or type(b['processStart'])is not str or not 1<=len(b['processStart'])<=128 or any(not _hex(b[k])for k in('guardianSourceSHA256','healthSourceSHA256','budgetSourceIdentity'))or any(type(b.get(k))is not str or not Path(b[k]).is_absolute()for k in('budgetRoot','evidenceRoot')):raise ValueError('HOST_HEALTH_TYPED_BINDING')
 return b
def _health_schema(r):
 if type(r)is not dict or any(r.get(k)is not v for k,v in [('samplerAlive',True),('primed',True),('closed',False),('failure',None)])or type(r.get('mockOnly'))is not bool or not _int(r.get('hostNs'))or not _int(r.get('responseHostNs')):raise ValueError('HOST_HEALTH_TYPED_RESPONSE')
 expected={'version','instance','pid','processStart','guardianSourceSHA256','healthSourceSHA256','hostNs','disk','power','failure','primed','audit','closed','samplerAlive','mockOnly','rowCredits','owner','challenge','responseHostNs','inventory','inventoryInFlightStartNs','inventoryAlive','budgetSourceIdentity','budgetRoot','evidenceRoot'}
 if set(r)!=expected or r['owner']!='guardian'or not _hex(r['challenge'],32):raise ValueError('HOST_HEALTH_EXACT_RESPONSE_SCHEMA')
 _binding({k:r[k]for k in('version','instance','pid','processStart','guardianSourceSHA256','healthSourceSHA256','budgetSourceIdentity','budgetRoot','evidenceRoot')})
 d=r.get('disk');p=r.get('power');a=r.get('audit')
 if type(d)is not dict or d.get('primed')is not True or any(not _int(d.get(k))for k in('hostNs','completedHostNs','freeBytes','checks','maximumActualGapNs'))or type(d.get('wallMonoDriftNs'))is not int or any(type(d.get(k))not in(int,float)or not math.isfinite(d[k])for k in('forecastFreeBytes','declineBytesPerSecond'))or d['hostNs']!=r['hostNs']or not 0<=d['completedHostNs']-d['hostNs']<=FRESH_NS or d['maximumActualGapNs']>FRESH_NS or abs(d['wallMonoDriftNs'])>FRESH_NS:raise ValueError('HOST_HEALTH_TYPED_DISK_OBSERVATION')
 if type(p)is not dict or type(p.get('AC'))is not bool or not _int(p.get('batteryPercent'))or p['batteryPercent']>100 or any(not _int(p.get(k))for k in('queryStartedHostNs','queryCompletedHostNs','auditSeq'))or not 0<=p['queryCompletedHostNs']-p['queryStartedHostNs']<=FRESH_NS or any(not _hex(p.get(k))for k in('stdoutSHA256','stderrSHA256')):raise ValueError('HOST_HEALTH_TYPED_POWER_OBSERVATION')
 if type(a)is not dict or a.get('failure')is not None or a.get('writerAlive')is not True or a.get('closed')is not False or any(not _int(a.get(k))for k in('producedSeq','committedSeq','pendingRows','committedBytes'))or not _hex(a.get('committedSHA256'))or a['producedSeq']-a['committedSeq']!=a['pendingRows']or not 0<=a['pendingRows']<=MAX_PENDING or p['auditSeq']>a['producedSeq']:raise ValueError('HOST_HEALTH_TYPED_AUDIT_CAUSALITY')
 if d['completedHostNs']>r['responseHostNs']or p['queryCompletedHostNs']>r['responseHostNs']or d['checks']<1 or d['freeBytes']<10*2**30+256*2**20 or d['forecastFreeBytes']<10*2**30+256*2**20 or d['declineBytesPerSecond']<0:raise ValueError('HOST_HEALTH_OBSERVATION_CAUSALITY_FLOOR')
 c=r['rowCredits']
 if type(c)is not dict or set(c)!={'reservation','guardRowsProduced','powerRowsProduced','inventoryRowsProduced','reservedNotProduced'}or c.get('reservedNotProduced')is not True or any(not _int(c.get(k),1)or c[k]>ROW_LIMIT['guardian']for k in('guardRowsProduced','powerRowsProduced'))or not _int(c.get('inventoryRowsProduced'),1)or c['inventoryRowsProduced']>INVENTORY_ROW_LIMIT['guardian']:raise ValueError('HOST_HEALTH_LOCAL_RESERVED_CREDITS')
 credit=c['reservation']
 if type(credit)is not dict or credit.get('kind')!='guardianRows'or type(credit.get('reservedCredits'))is not int or credit['reservedCredits']!=4200 or type(credit.get('globalCeiling'))is not int or credit['globalCeiling']!=4200 or credit.get('reservedNotProduced')is not True or credit.get('refunded')is not False:raise ValueError('HOST_HEALTH_TYPED_GLOBAL_CREDIT_RESERVATION')
 i=r.get('inventory');active=r.get('inventoryInFlightStartNs')
 if r.get('inventoryAlive')is not True or type(i)is not dict or any(not _int(i.get(k))for k in('startedHostNs','completedHostNs','auditSeq'))or not 0<=i['completedHostNs']-i['startedHostNs']<=INVENTORY_DEADLINE_NS or not 0<=r['responseHostNs']-i['startedHostNs']<=INVENTORY_MAX_AGE_NS or active is not None and(not _int(active)or not 0<=r['responseHostNs']-active<=INVENTORY_DEADLINE_NS)or i['auditSeq']>a['producedSeq']:raise ValueError('HOST_HEALTH_REQUIRED_CAP_OBSERVATION')
 if p['auditSeq']<1 or i['auditSeq']<1 or not p['AC']and(p['batteryPercent']<30 if c['powerRowsProduced']==1 else p['batteryPercent']<=20):raise ValueError('HOST_HEALTH_ORIGINAL_POWER_FLOOR_AND_SEQUENCE')
 _inventory_counters(i.get('counters'),'guardian')
 if i['completedHostNs']>r['responseHostNs']:raise ValueError('HOST_HEALTH_INVENTORY_CAUSALITY')
 return r

class AuditQueue:
 """A finite prefunded producer queue. Only its writer touches the ledger."""
 def __init__(self,budget,owner,root):
  if type(budget)is not MetadataBudget:raise ValueError('HOST_HEALTH_EXACT_METADATA_BUDGET')
  self.budget=budget;self.owner=owner;self.root=Path(root).absolute();self.path=self.root/'health-audit.bin';self.q=queue.Queue(QUEUE_ROWS);self.lock=threading.RLock();self.produced=0;self.committed=0;self.total_bytes=0;self.failure=None;self.rejected=[];self.committed_bytes=0;self.done=threading.Event();self.closed=None;self.close_failure=None;self.digest=hashlib.sha256();self.trace=StageTrace();self.lease=self._reserve();self.thread=threading.Thread(target=self._run,name='aeris-health-audit',daemon=True)
 def _reserve(self):
  with self.budget.trace_stages(self.trace):
   self.row_credits=self.budget.reserve_counter('guardianRows'if self.owner=='guardian'else'monitorRows',ROW_LIMIT[self.owner]);return self.budget.reserve_lease({self.owner:AUDIT_LEASE[self.owner]})
 def start(self):self.thread.start()
 def submit(self,kind,payload):
  payload=bytes(payload)
  with self.lock:
   if kind not in(1,2,3)or len(payload)>ROW_BYTES:raise ValueError('HOST_AUDIT_TYPED_ROW_BOUND')
   if self.done.is_set():raise RuntimeError('HOST_AUDIT_ALREADY_CLOSING')
   seq=self.produced+1;raw=HEADER.pack(seq,kind,len(payload))+payload
   if self.failure is not None:
    # There are exactly three single-threaded producers. Either can finish one
    # already-started acquisition after its peer has filled the queue.
    if not any(k==kind for k,_,_ in self.rejected):
     self.rejected.append((kind,seq,raw));self.produced=seq;self.total_bytes+=len(raw)
    raise self.failure
   if self.total_bytes+len(raw)>AUDIT_LEASE[self.owner]-16384:
    self.failure=ValueError('HOST_AUDIT_PREFIX_SOURCE_CAP');self.rejected.append((kind,seq,raw));self.produced=seq;self.total_bytes+=len(raw);raise self.failure
   try:self.q.put_nowait((seq,raw))
   except queue.Full as e:
    self.rejected.append((kind,seq,raw));self.produced=seq;self.total_bytes+=len(raw);self.failure=RuntimeError('HOST_AUDIT_QUEUE_FULL_LOSSLESS_REFUSAL');raise self.failure from e
   self.produced=seq;self.total_bytes+=len(raw);return seq
 def _run(self):
  try:
   with self.budget.trace_stages(self.trace),self.budget.use_lease(self.lease):
    self.budget.write(self.owner,self.path,b'')
    while not self.done.is_set() or not self.q.empty():
     try:seq,raw=self.q.get(timeout=.05)
     except queue.Empty:continue
     batch=[(seq,raw)]
     for _ in range(7):
      try:batch.append(self.q.get_nowait())
      except queue.Empty:break
     for _,frame in batch:
      if HEADER.unpack_from(frame)[1]==3:self.budget.observe_inventory(_strict(frame[HEADER.size:])['counters'])
     self.budget.write(self.owner,self.path,b''.join(r for _,r in batch),append=True);self.trace.check()
     with self.lock:
      for seq,raw in batch:self.digest.update(raw);self.committed=seq;self.committed_bytes+=len(raw)
     for _ in batch:self.q.task_done()
    for _,seq,raw in self.rejected:
     self.budget.write(self.owner,self.path,raw,append=True)
     with self.lock:self.digest.update(raw);self.committed=seq;self.committed_bytes+=len(raw)
  except BaseException as e:
   with self.lock:
    if self.failure is None:self.failure=e
    else:self.failure.add_note('AUDIT_WRITER_SECONDARY:'+_error(e))
 def snapshot(self):
  self.trace.check()
  with self.lock:
   return {'producedSeq':self.produced,'committedSeq':self.committed,'pendingRows':self.produced-self.committed,'failure':None if self.failure is None else _error(self.failure),'writerAlive':self.thread.is_alive(),'closed':self.closed is not None,'committedBytes':self.committed_bytes,'committedSHA256':self.digest.hexdigest()}
 def barrier(self,timeout=2):
  with self.lock:target=self.produced
  deadline=time.monotonic()+timeout
  while True:
   s=self.snapshot()
   if s['failure']:raise RuntimeError(s['failure'])
   if s['committedSeq']>=target:return {'path':str(self.path),'throughSeq':s['committedSeq'],'committedSeq':s['committedSeq'],'bytes':s['committedBytes'],'sha256':s['committedSHA256'],'pendingNewerRows':s['pendingRows'],'barrierHostNs':time.monotonic_ns(),'durable':True}
   if not self.thread.is_alive():raise RuntimeError('HOST_AUDIT_WRITER_DEAD')
   if time.monotonic()>=deadline:raise TimeoutError('HOST_AUDIT_DURABILITY_BARRIER')
   time.sleep(.005)
 def close(self):
  if self.closed is not None:return dict(self.closed)
  if self.close_failure is not None:raise self.close_failure
  try:return self._close()
  except BaseException as e:self.close_failure=e;raise
 def _close(self):
  self.done.set();self.thread.join(timeout=8)
  if self.thread.is_alive():raise RuntimeError('HOST_AUDIT_WRITER_CLOSE_TIMEOUT')
  if self.failure:raise self.failure
  if self.committed!=self.produced:raise RuntimeError('HOST_AUDIT_UNCOMMITTED_ROWS')
  self.trace.check()
  with self.budget.trace_stages(self.trace):self.budget.release_lease(self.lease)
  self.trace.check()
  terminal_trace=self.trace.snapshot();self.trace.check()
  self.closed={'path':str(self.path),'sha256':self.digest.hexdigest(),'bytes':self.total_bytes,'producedSeq':self.produced,'committedSeq':self.committed,'pendingRows':0,'durablyDrained':True,'mockOnly':self.budget.mock,'writerTrace':terminal_trace};return dict(self.closed)

class ObservedDiskGuard(DiskGuard):
 """Original actual IO/math, with a completion-time stale observation veto."""
 def __init__(self,path,observed):super().__init__(path);self.observed=observed;self.failure=None
 def _observe(self,requested_bytes=0,*,priming=False):
  if self.failure is not None:raise self.failure
  try:
   result=super()._observe(requested_bytes,priming=priming)
   diagnostic=self.diagnostic();completed=time.monotonic_ns()
   if not 0<=completed-diagnostic['currentObservationNs']<=FRESH_NS:raise RuntimeError('HOST_STATVFS_COMPLETION_STALE')
   self.observed(diagnostic,completed,time.time_ns());return result
  except BaseException as e:self.failure=e;raise

class ManagedClosing(RuntimeError):pass

class HostHealth:
 def __init__(self,root,budget,owner,*,inventory=None,check_inventory=None):
  if type(budget)is not MetadataBudget:raise ValueError('HOST_HEALTH_EXACT_METADATA_BUDGET')
  if owner not in ROW_LIMIT:raise ValueError('HOST_HEALTH_OWNER')
  self.root=Path(root).absolute();self.budget=budget;self.owner=owner;self.guard_lock=threading.RLock();self.state_lock=threading.RLock();self.disk=ObservedDiskGuard(repository(),self._observed);self.audit=AuditQueue(budget,owner,root);self.row_credits=self.audit.row_credits;self.stop_event=threading.Event();self.failure=None;self.latest=None;self.power=None;self.prime=None;self.max_gap=0;self.last_wall=None;self.last_ns=None;self.rows=0;self.power_rows=0;self.threads=[];self.closed=None;self.entry_barrier=None;self.power_trace=StageTrace();self.inventory=inventory;self.check_inventory=check_inventory;self.inventory_latest=None;self.inventory_inflight=None;self.inventory_rows=0;self.inventory_stop=threading.Event();self.managed_closing=False;self.managed_before=None;self.managed_after=None
 def latch(self,e):
  with self.state_lock:
   if self.failure is None:self.failure=e
  return self.failure
 def _observed(self,d,completed,wall):
  with self.state_lock:
   if self.stop_event.is_set()and self.prime is None:raise RuntimeError('HOST_HEALTH_PRIME_STOPPED_NOT_ACCEPTANCE')
   n=d['currentObservationNs'];gap=0 if self.last_ns is None else n-self.last_ns;drift=0 if self.last_wall is None else (wall-self.last_wall)-(completed-self.latest['completedHostNs'])
   if gap<0 or gap>FRESH_NS or abs(drift)>FRESH_NS:raise self.latch(RuntimeError('SUSPEND_OR_GENUINE_HOST_SAMPLE_GAP'))
   self.max_gap=max(self.max_gap,gap);self.last_ns=n;self.last_wall=wall;self.latest={'hostNs':n,'completedHostNs':completed,'freeBytes':d['currentFreeBytes'],'forecastFreeBytes':d['forecastFreeBytes'],'declineBytesPerSecond':d['declineBytesPerSecond'],'checks':d['checks'],'primed':d['primed'],'maximumActualGapNs':self.max_gap,'wallMonoDriftNs':drift}
 def start(self):
  if self.threads:raise RuntimeError('HOST_HEALTH_ONE_START')
  self.budget.require_real_actor()
  if self.inventory is None or not callable(self.check_inventory):raise ValueError('SOURCE_REQUIRED_CONTINUOUS_INVENTORY')
  from .inventory import Inventory
  if not self.budget.mock and type(self.inventory)is not Inventory:raise ValueError('SOURCE_EXACT_INVENTORY')
  self.audit.start()
  for name,fn in [('power',self._power_loop),('statvfs',self._sample_loop),('inventory',self._inventory_loop)]:
   t=threading.Thread(target=fn,name='aeris-host-'+name,daemon=True);self.threads.append(t);t.start()
  deadline=time.monotonic()+20
  while self.prime is None or self.power is None or self.rows<1 or self.inventory_latest is None:
   self._failure_check(priming=True)
   if time.monotonic()>=deadline:raise self.latch(TimeoutError('HOST_HEALTH_PRIME_READINESS'))
   time.sleep(.01)
  self.check();self.entry_barrier=self.audit.barrier();return {'actualPrime':self.prime,'power':dict(self.power),'auditBarrier':self.entry_barrier,'inventory':dict(self.inventory_latest)}
 def _sample_loop(self):
  try:
   with self.guard_lock:self.prime=self.disk.prime()
   next_audit=0
   while not self.stop_event.is_set():
    with self.guard_lock:self.disk.check()
    now=time.monotonic_ns()
    if now>=next_audit:
     if self.rows>=ROW_LIMIT[self.owner]:raise RuntimeError('HOST_GUARD_ORIGINAL_ROW_CAP')
     with self.state_lock:d=dict(self.latest)
     self.audit.submit(1,DISK_ROW.pack(d['hostNs'],d['completedHostNs'],d['freeBytes'],d['declineBytesPerSecond'],d['forecastFreeBytes'],d['checks'],d['maximumActualGapNs'],d['wallMonoDriftNs']));self.rows+=1;next_audit=now+500_000_000
    self.stop_event.wait(.1)
  except BaseException as e:self.latch(e)
 def _power_loop(self):
  try:
   while not self.stop_event.is_set():
    if self.power_rows>=ROW_LIMIT[self.owner]:raise RuntimeError('HOST_POWER_ORIGINAL_ROW_CAP')
    started=time.monotonic_ns();r=capture_command(None,self.owner,['pmset','-g','batt'],deadline_ns=started+FRESH_NS,stdout_limit=192,stderr_limit=128,trace=self.power_trace);ended=time.monotonic_ns();out=r['stdout'];err=r['stderr'];error=r['failure'];ac=False;batt=255
    if error is None and (not r['captureComplete'] or ended-started>FRESH_NS):error=TimeoutError('HOST_POWER_LATE_COMPLETION')
    if error is None and err:error=RuntimeError('POWER_STDERR_NOT_EMPTY')
    if error is None:
     try:
      text=out.decode();m=re.search(r'(\d+)%',text)
      if m is None or not 0<=int(m.group(1))<=100:raise RuntimeError('UNKNOWN_POWER')
      ac="'AC Power'"in text;batt=int(m.group(1))
      if not ac and (batt<30 if self.power is None else batt<=20):raise RuntimeError('POWER_ENTRY30_OR_STOP20')
     except BaseException as e:error=e
    seq=self.audit.submit(2,POWER_ROW.pack(started,ended,int(ac),batt,len(out),len(err))+out+err);self.power_rows+=1
    if error is not None:raise error
    with self.state_lock:self.power={'queryStartedHostNs':started,'queryCompletedHostNs':ended,'AC':ac,'batteryPercent':batt,'auditSeq':seq,'stdoutSHA256':hashlib.sha256(out).hexdigest(),'stderrSHA256':hashlib.sha256(err).hexdigest()}
    self.stop_event.wait(.5)
  except BaseException as e:self.latch(e)
 def _inventory_loop(self):
  try:
   while not self.stop_event.is_set()and not self.inventory_stop.is_set():
    if self.inventory_rows>=INVENTORY_ROW_LIMIT[self.owner]-1:raise RuntimeError('HOST_INVENTORY_ORIGINAL_COUNTER')
    started=time.monotonic_ns()
    with self.state_lock:self.inventory_inflight=started
    error=None
    with self.power_trace.span('inventory'):
     value=self.budget.snapshot_inventory(self.inventory)
     try:self.check_inventory(value)
     except BaseException as e:error=e
    ended=time.monotonic_ns();row={'startedHostNs':started,'completedHostNs':ended,'counters':{k:v for k,v in value.items()if type(v)is int},'failure':None if error is None else _error(error)[:128]}
    payload=_json(row)
    if len(payload)>ROW_BYTES:raise ValueError('HOST_INVENTORY_ORIGINAL_ROW1024')
    seq=self.audit.submit(3,payload);self.inventory_rows+=1
    if error is not None:raise error
    if not 0<=ended-started<=INVENTORY_DEADLINE_NS:raise TimeoutError('HOST_REQUIRED_INVENTORY_LATE_COMPLETION')
    with self.state_lock:self.inventory_latest={**row,'auditSeq':seq};self.inventory_inflight=None
    self.inventory_stop.wait(max(0,(started+INVENTORY_INTERVAL_NS-time.monotonic_ns())/1e9))
  except BaseException as e:
   self.inventory_fault=getattr(self.budget,'inventory_fault',None);self.latch(e)
 def _failure_check(self,priming=False,*,closing_validation=False):
  if self.managed_closing and not closing_validation:raise ManagedClosing('HOST_MANAGED_CLOSING_NO_NEW_ACCEPTANCE')
  if self.stop_event.is_set():raise RuntimeError('HOST_HEALTH_CLOSING_NO_NEW_ACCEPTANCE')
  try:self.power_trace.check();self.audit.trace.check()
  except BaseException as e:raise self.latch(e)
  if self.failure:raise self.failure
  a=self.audit.snapshot()
  if a['failure'] or not a['writerAlive']:raise self.latch(RuntimeError(a['failure']or'HOST_AUDIT_WRITER_DEAD'))
  checked_threads=self.threads[:2]if closing_validation else self.threads
  if checked_threads and any(not t.is_alive()for t in checked_threads) and not self.stop_event.is_set():raise self.latch(RuntimeError('HOST_OBSERVATION_WORKER_DEAD'))
  now=time.monotonic_ns()
  with self.state_lock:
   if self.latest is not None and not 0<=now-self.latest['hostNs']<=FRESH_NS:raise self.latch(RuntimeError('HOST_GENUINE_DISK_SAMPLE_STALE'))
   if self.power is not None and not 0<=now-self.power['queryStartedHostNs']<=FRESH_NS:raise self.latch(RuntimeError('HOST_ORIGINAL_POWER_STALE'))
   if not closing_validation and self.inventory_inflight is not None and not 0<=now-self.inventory_inflight<=INVENTORY_DEADLINE_NS:raise self.latch(TimeoutError('HOST_REQUIRED_INVENTORY_INFLIGHT_STALE'))
   if not closing_validation and self.inventory_latest is not None and not 0<=now-self.inventory_latest['startedHostNs']<=INVENTORY_MAX_AGE_NS:raise self.latch(TimeoutError('HOST_REQUIRED_INVENTORY_OBSERVATION_STALE'))
   if not priming and(self.latest is None or self.prime is None or self.power is None or self.inventory_latest is None):raise RuntimeError('HOST_REAL_PRIME_AND_POWER_REQUIRED')
 def check(self,n=None):
  self._failure_check()
  if n is not None:
   try:
    with self.guard_lock:self.disk.check(n)
   except BaseException as e:raise self.latch(e)
  self._failure_check();return self.snapshot()
 def snapshot(self):
  with self.state_lock:return {'hostNs':None if self.latest is None else self.latest['hostNs'],'disk':None if self.latest is None else dict(self.latest),'power':None if self.power is None else dict(self.power),'failure':None if self.failure is None else _error(self.failure),'primed':self.prime is not None,'audit':self.audit.snapshot(),'closed':self.closed is not None or self.managed_closing,'inventory':None if self.inventory_latest is None else dict(self.inventory_latest),'inventoryInFlightStartNs':self.inventory_inflight,'inventoryAlive':len(self.threads)==3 and self.threads[2].is_alive(),'samplerAlive':len(self.threads)==3 and self.threads[1].is_alive(),'mockOnly':self.budget.mock,'owner':self.owner,'rowCredits':{'reservation':self.row_credits,'guardRowsProduced':self.rows,'powerRowsProduced':self.power_rows,'inventoryRowsProduced':self.inventory_rows,'reservedNotProduced':True}}
 def barrier(self):
  self.check();self.power_trace.snapshot();self.audit.trace.snapshot();self.power_trace.check();self.audit.trace.check();deadline=time.monotonic_ns()+INVENTORY_DEADLINE_NS
  while self.inventory_inflight is not None:
   self.check()
   if time.monotonic_ns()>=deadline:raise TimeoutError('HOST_REQUIRED_INVENTORY_BARRIER')
   time.sleep(.005)
  return self.audit.barrier()
 def begin_managed_close(self):
  # Internal owner shutdown only. No IPC verb or operational readiness waiver.
  with self.state_lock:self.managed_closing=True
  self.inventory_stop.set()
  if len(self.threads)==3:self.threads[2].join(timeout=2)
  if len(self.threads)==3 and self.threads[2].is_alive():raise self.latch(TimeoutError('HOST_INVENTORY_QUIESCE2S'))
  if self.managed_before is None:
   self.managed_before={'inventory':None if self.inventory_latest is None else dict(self.inventory_latest),'auditRef':self.audit.barrier(),'hostNs':time.monotonic_ns(),'nonaccepting':True}
  return dict(self.managed_before)
 def closing_check(self):
  if not self.managed_closing:raise RuntimeError('INTERNAL_MANAGED_CLOSING_REQUIRED')
  # Inventory is intentionally quiesced. Genuine disk/power/death checks remain.
  self._failure_check(closing_validation=True)
 def final_managed_census(self):
  try:return self._final_managed_census()
  except BaseException as error:
   self.inventory_fault=getattr(self.budget,'inventory_fault',None);raise self.latch(error)
 def _final_managed_census(self):
  if not self.managed_closing or len(self.threads)==3 and self.threads[2].is_alive():raise RuntimeError('FINAL_CENSUS_REQUIRES_QUIESCED_INVENTORY')
  if self.managed_after is not None:return dict(self.managed_after)
  if self.inventory_rows>=INVENTORY_ROW_LIMIT[self.owner]:raise self.latch(RuntimeError('HOST_FINAL_INVENTORY_ROW_CAP'))
  started=time.monotonic_ns();value=self.budget.snapshot_inventory(self.inventory);self.check_inventory(value);ended=time.monotonic_ns()
  if not 0<=ended-started<=INVENTORY_DEADLINE_NS:raise self.latch(TimeoutError('HOST_FINAL_INVENTORY_DEADLINE'))
  row={'startedHostNs':started,'completedHostNs':ended,'counters':{k:v for k,v in value.items()if type(v)is int},'failure':None};seq=self.audit.submit(3,_json(row));self.inventory_rows+=1;barrier=self.audit.barrier()
  self.managed_after={'inventory':{**row,'auditSeq':seq},'auditRef':barrier,'hostNs':time.monotonic_ns(),'nonaccepting':True};return dict(self.managed_after)
 def close(self):
  if self.closed is not None:return dict(self.closed)
  self.inventory_stop.set();self.stop_event.set()
  for t in self.threads:t.join(timeout=8)
  if any(t.is_alive()for t in self.threads):raise self.latch(RuntimeError('HOST_HEALTH_WORKER_CLOSE_TIMEOUT'))
  audit=self.audit.close()
  if self.failure:raise self.failure
  proof=verify_audit_prefix({'path':audit['path'],'bytes':audit['bytes'],'sha256':audit['sha256'],'throughSeq':audit['committedSeq'],'durable':True},self.owner,expected_root=self.root)
  terminal_power_trace=self.power_trace.snapshot();self.power_trace.check();self.audit.trace.check()
  self.closed={'hostNs':time.monotonic_ns(),'failure':None,'audit':audit,'originalPrefixVerified':proof,'actualDiskDiagnostic':self.disk.diagnostic(),'durablyDrained':True,'mockOnly':self.budget.mock,'powerTrace':terminal_power_trace,'managedBefore':self.managed_before,'managedAfter':self.managed_after};return dict(self.closed)

# Darwin constants come from the selected SDK's sys/un.h: SOL_LOCAL=0,
# LOCAL_PEERPID=0x002. A missing kernel PID proof is a refusal, never a fallback.
def peer_pid(s):
 if sys.platform=='darwin':return struct.unpack('i',s.getsockopt(0,0x002,4))[0]
 if hasattr(socket,'SO_PEERCRED'):return struct.unpack('3i',s.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,12))[0]
 raise RuntimeError('HOST_HEALTH_KERNEL_PEER_PID_UNAVAILABLE')
def _receive(s,maximum):
 raw=bytearray()
 while b'\n'not in raw:
  b=s.recv(min(1024,maximum+1-len(raw)))
  if not b:raise ValueError('HOST_HEALTH_INCOMPLETE_IPC')
  raw.extend(b)
  if len(raw)>maximum:raise ValueError('HOST_HEALTH_IPC_BOUND')
 if raw.count(b'\n')!=1 or not raw.endswith(b'\n'):raise ValueError('HOST_HEALTH_IPC_FRAMING')
 return _strict(raw)

class HealthServer:
 def __init__(self,root,health,binding):
  self.root=Path(root);self.health=health;self.binding=_binding(dict(binding));self.path=self.root/'health.sock';self.socket=None;self.thread=None;self.done=threading.Event();self.failure=None
 def start(self):
  st=self.root.stat()
  if st.st_uid!=os.geteuid()or self.root.is_symlink():raise RuntimeError('HOST_HEALTH_ENDPOINT_OWNER')
  os.chmod(self.root,0o700)
  if len(os.fsencode(self.path))>103 or self.path.exists():raise RuntimeError('HOST_HEALTH_FRESH_BOUNDED_ENDPOINT')
  self.health.budget.charge_ephemeral_socket('guardian',self.path)
  self.socket=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
  with self.health.budget.publication():self.socket.bind(str(self.path));os.chmod(self.path,0o600);self.inode=self.path.stat().st_ino
  self.socket.listen(4);self.socket.settimeout(.1);self.thread=threading.Thread(target=self._run,name='aeris-health-readonly',daemon=True);self.thread.start()
 def _run(self):
  try:
   while not self.done.is_set():
    try:s,_=self.socket.accept()
    except socket.timeout:continue
    with s:
     s.settimeout(.1)
     try:
      request=_receive(s,256)
      if type(request)is not dict or set(request)!={'challenge','instance'}or not _hex(request['challenge'],32)or type(request['instance'])is not str or request['instance']!=self.binding['instance']:raise ValueError('HOST_HEALTH_CHALLENGE_BINDING')
      self.health.check();value={**self.binding,**self.health.snapshot(),'challenge':request['challenge'],'responseHostNs':time.monotonic_ns()};body=_json(value)
      if len(body)>4096:raise ValueError('HOST_HEALTH_RESPONSE_BOUND')
      s.sendall(body)
     except (ValueError,KeyError,json.JSONDecodeError,UnicodeError,socket.timeout,ConnectionResetError,BrokenPipeError):continue
     except ManagedClosing as e:
      try:s.sendall(_json({'failure':str(e)}))
      except OSError:pass
     except BaseException as e:
      self.health.latch(e)
      try:s.sendall(_json({'failure':_error(e)}))
      except OSError:pass
  except BaseException as e:
   if not self.done.is_set():self.failure=e;self.health.latch(e)
 def close(self):
  self.done.set()
  if self.thread:self.thread.join(timeout=2)
  error=None
  if self.thread and self.thread.is_alive():error=RuntimeError('HOST_HEALTH_ENDPOINT_THREAD_CLOSE')
  if self.socket:error=cleanup(error,[('health-socket-close',self.socket.close)])
  if self.path.exists():
   if self.path.stat().st_ino!=self.inode:error=error or RuntimeError('HOST_HEALTH_ENDPOINT_REPLACED')
   else:
    def unlink_owned():
     with self.health.budget.publication():self.path.unlink()
    error=cleanup(error,[('health-socket-unlink',unlink_owned)])
  if error:raise error

class GuardianClient:
 def __init__(self,root,source,*,budget=None,allow_mock=False):
  self.allow_mock=allow_mock;self.root=Path(root).absolute()
  if self.root.resolve()!=self.root or any(p.is_symlink()for p in[self.root,*self.root.parents])or not self.root.is_dir():raise RuntimeError('HOST_HEALTH_PRIVATE_ROOT_NO_ALIAS')
  p=self.root/'launch.json';st=p.lstat()
  if not stat.S_ISREG(st.st_mode)or st.st_size>16384 or p.is_symlink():raise RuntimeError('HOST_HEALTH_ORIGINAL_LAUNCH')
  launch=_strict(p.read_bytes());self.binding=_binding(launch['healthBinding']);self.source=source
  if self.binding['guardianSourceSHA256']!=source or self.binding['healthSourceSHA256']!=source_sha()or self.binding['pid']!=launch['guardianPID']or self.binding['processStart']!=launch['guardianProcessStart']:raise RuntimeError('HOST_HEALTH_ORIGINAL_SOURCE_START_BINDING')
  self.path=self.root/'health.sock'
  if budget is not None and any(self.binding.get(k)!=v for k,v in budget_binding(budget).items()):raise RuntimeError('HOST_HEALTH_EXACT_CAMPAIGN_FULL_SOURCE_BINDING')
  if budget is None and not allow_mock:raise ValueError('HOST_HEALTH_INITIAL_START_PROOF_BUDGET')
  if budget is not None:
   from .emulator import _query
   actual=_query(['ps','-p',str(self.binding['pid']),'-o','lstart='],budget,self.root,maximum=128).strip()
   if actual!=self.binding['processStart']:raise RuntimeError('HOST_HEALTH_INITIAL_ACTUAL_PROCESS_START')
  self.socket_identity=(self.path.lstat().st_dev,self.path.lstat().st_ino)
 def __call__(self):
  b=self.binding;os.kill(b['pid'],0)
  if self.root.resolve()!=self.root or any(p.is_symlink()for p in[self.root,*self.root.parents]):raise RuntimeError('HOST_HEALTH_PRIVATE_ROOT_NO_ALIAS')
  rootstat=self.root.lstat();st=self.path.lstat()
  if (st.st_dev,st.st_ino)!=self.socket_identity:raise RuntimeError('HOST_HEALTH_ENDPOINT_INODE_REPLACED')
  if not stat.S_ISDIR(rootstat.st_mode)or rootstat.st_uid!=os.geteuid()or stat.S_IMODE(rootstat.st_mode)!=0o700 or not stat.S_ISSOCK(st.st_mode)or st.st_uid!=os.geteuid()or stat.S_IMODE(st.st_mode)!=0o600:raise RuntimeError('HOST_HEALTH_PRIVATE_ENDPOINT')
  challenge=secrets.token_hex(16);started=time.monotonic_ns()
  with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)as s:
   s.settimeout(.1);s.connect(str(self.path))
   if peer_pid(s)!=b['pid']:raise RuntimeError('HOST_HEALTH_KERNEL_PID_BINDING')
   s.sendall(_json({'challenge':challenge,'instance':b['instance']}));r=_receive(s,4096)
  ended=time.monotonic_ns();_health_schema(r)
  if ended-started>100_000_000 or r.get('challenge')!=challenge or any(r.get(k)!=v for k,v in b.items()):raise RuntimeError('HOST_HEALTH_FRESH_RESPONSE_BINDING')
  if r.get('mockOnly')is True and not self.allow_mock:raise RuntimeError('HOST_HEALTH_MOCK_CANNOT_ADMIT_ACTORS')
  if r.get('failure')is not None or not r.get('samplerAlive')or r.get('closed')or not r.get('primed')or not 0<=ended-r.get('hostNs',-FRESH_NS)<=FRESH_NS or not started<=r.get('responseHostNs',-1)<=ended or not 0<=ended-r.get('power',{}).get('queryStartedHostNs',-FRESH_NS)<=FRESH_NS:raise RuntimeError('HOST_HEALTH_ORIGINAL_OBSERVATION_STALE_OR_FAILED')
  if r.get('audit',{}).get('failure')or not r.get('audit',{}).get('writerAlive'):raise RuntimeError('HOST_HEALTH_AUDIT_FAILURE')
  return {**r,'alive':True,'closed':False,'sourceVerified':True}

def verify_audit_prefix(ref,owner,*,expected_root=None):
 """Cold-check the exact committed byte prefix, without adopting a later append."""
 if owner not in ROW_LIMIT or type(ref)is not dict or ref.get('durable')is not True or not _int(ref.get('bytes'))or not _int(ref.get('throughSeq'))or not _hex(ref.get('sha256'))or ref['bytes']>AUDIT_LEASE[owner]-16384:raise ValueError('HOST_AUDIT_ORIGINAL_PREFIX_REF')
 path=Path(ref['path'])
 if not path.is_absolute()or path.name!='health-audit.bin'or path.resolve()!=path or any(p.is_symlink()for p in[path,*path.parents])or expected_root is not None and path!=Path(expected_root).absolute()/'health-audit.bin':raise ValueError('HOST_AUDIT_EXACT_OWNED_PATH')
 fd=os.open(path,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0))
 try:
  st=os.fstat(fd)
  if not stat.S_ISREG(st.st_mode)or st.st_nlink!=1 or st.st_size<ref['bytes']:raise ValueError('HOST_AUDIT_ORIGINAL_REGULAR_PREFIX')
  with os.fdopen(fd,'rb',closefd=False)as f:raw=f.read(ref['bytes'])
 finally:os.close(fd)
 if len(raw)!=ref['bytes']or hashlib.sha256(raw).hexdigest()!=ref['sha256']:raise ValueError('HOST_AUDIT_ORIGINAL_PREFIX_SHA')
 offset=0;seq=0;counts={1:0,2:0,3:0};lastdisk=None;lastpower=None;lastinventory=None
 while offset<len(raw):
  if len(raw)-offset<HEADER.size:raise ValueError('HOST_AUDIT_PARTIAL_HEADER')
  n,kind,size=HEADER.unpack_from(raw,offset);offset+=HEADER.size
  if n!=seq+1 or size>ROW_BYTES or len(raw)-offset<size or kind not in counts:raise ValueError('HOST_AUDIT_SEQUENCE_LENGTH_KIND')
  payload=raw[offset:offset+size];offset+=size;seq=n;counts[kind]+=1
  if counts[kind]>(INVENTORY_ROW_LIMIT[owner]if kind==3 else ROW_LIMIT[owner]):raise ValueError('HOST_AUDIT_ORIGINAL_ROW_COUNTER')
  if kind==1:
   if size!=DISK_ROW.size:raise ValueError('HOST_AUDIT_DISK_RECORD_SIZE')
   observed,completed,free,rate,forecast,checks,gap,drift=DISK_ROW.unpack(payload)
   if any(not _int(v)for v in(observed,completed,free,checks,gap))or not 0<=completed-observed<=FRESH_NS or free<10*2**30+256*2**20 or not math.isfinite(rate)or rate<0 or not math.isfinite(forecast)or forecast<10*2**30+256*2**20 or gap>FRESH_NS or abs(drift)>FRESH_NS or checks<1 or lastdisk is not None and(observed<=lastdisk[0]or checks<=lastdisk[1]):raise ValueError('HOST_AUDIT_ORIGINAL_DISK_OBSERVATION')
   lastdisk=(observed,checks)
  elif kind==2:
   if size<POWER_ROW.size:raise ValueError('HOST_AUDIT_POWER_RECORD_SIZE')
   started,ended,ac,batt,outn,errn=POWER_ROW.unpack_from(payload);out=payload[POWER_ROW.size:POWER_ROW.size+outn];err=payload[POWER_ROW.size+outn:]
   if any(not _int(v)for v in(started,ended))or size!=POWER_ROW.size+outn+errn or outn>192 or errn or ac not in(0,1)or not 0<=batt<=100 or not 0<=ended-started<=FRESH_NS or lastpower is not None and(started<=lastpower[0]or started<lastpower[1]):raise ValueError('HOST_AUDIT_ORIGINAL_POWER_CAPTURE')
   text=out.decode();m=re.search(r'(\d+)%',text)
   if m is None or int(m.group(1))!=batt or ("'AC Power'"in text)!=bool(ac)or not ac and(batt<30 if lastpower is None else batt<=20):raise ValueError('HOST_AUDIT_ORIGINAL_POWER_VALUES')
   lastpower=(started,ended)
  else:
   row=_strict(payload)
   if type(row)is not dict or any(not _int(row.get(k))for k in('startedHostNs','completedHostNs'))or not 0<=row['completedHostNs']-row['startedHostNs']<=INVENTORY_DEADLINE_NS or type(row.get('counters'))is not dict or row.get('failure')is not None:raise ValueError('HOST_AUDIT_REQUIRED_INVENTORY_ROW')
   if lastinventory is not None and(row['startedHostNs']<=lastinventory[0]or row['startedHostNs']<lastinventory[1]):raise ValueError('HOST_AUDIT_ORIGINAL_INVENTORY_CLOCK_ORDER')
   lastinventory=(row['startedHostNs'],row['completedHostNs']);_inventory_counters(row['counters'],owner)
 if seq!=ref['throughSeq']or not counts[1]or not counts[2]or not counts[3]:raise ValueError('HOST_AUDIT_PREFIX_EXACT_SEQUENCE_AND_DISK_POWER_REQUIRED')
 return {'status':'ORIGINAL_COMMITTED_PREFIX_VERIFIED','throughSeq':seq,'bytes':len(raw),'sha256':ref['sha256'],'diskDiagnosticRows':counts[1],'powerOriginalRows':counts[2],'inventoryOriginalRows':counts[3],'internalSamplePolicy':'ORIGINAL_192_WINDOW_100MS_NOT_A_NEW_PERSISTED_FULLRAW_LOG'}
