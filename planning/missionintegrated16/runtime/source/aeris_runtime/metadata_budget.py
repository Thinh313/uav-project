"""Campaign-wide explicit metadata ownership, durable reservations and bounded IO.

All reservations are source constants. Raw/AP-state/native/export/artifact domains
keep their original Inventory classification and their existing quota writers.
"""
from pathlib import Path
from .cleanup import cleanup,finish_cleanup,close_fd
from .stage_trace import span as trace_span
from contextlib import contextmanager
import errno,fcntl,hashlib,json,os,re,selectors,shutil,stat,subprocess,threading,time,secrets,traceback
MIB=2**20;CAP=64*MIB;CLOSURE=MIB;LEDGER=128*1024;BLOCK=4096
CLOSING_OWNERS={'lifecycle':192*1024,'guardian':136*1024,'monitor':128*1024,'stream':256*1024,'commands':32*1024,'command_receipts':32*1024,'closure':224*1024}
LIMITS={'requests':900,'commands':3700,'dtoSnapshots':900,'preparationCommands':24,'bootstraps':2,'observerEpochs':4,'cases':2,'children':4,'diagnosticChildren':4,'queries':32,'monitorRows':4200,'guardianRows':4200,'campaignRecords':32,'auditRecords':4}
OWNERS={'dto':15*MIB,'stream':4*MIB,'commands':9*MIB,'command_receipts':5*MIB,'requests':2*MIB,'barriers':512*1024,'lifecycle':8*MIB,'host_queries':MIB,'child_output':4*MIB,'monitor':3*MIB,'guardian':3*MIB,'campaign':MIB,'audit':256*1024,'external_task':MIB}

def observer_envelope():
 return {'format':'aeris-campaign-io-envelope','version':3,'maximumRequests':900,'maximumCommands':3700,'snapshotAcceptedBytes':16384,'ackLineBytes':2048,'streamBytes':4*MIB,'owners':dict(OWNERS),'shutdownReserveBytes':CLOSURE,'ledgerReserveBytes':LEDGER,'closureSubEnvelopes':dict(CLOSING_OWNERS),'closureUnassignedBytes':CLOSURE-sum(CLOSING_OWNERS.values()),'totalFutureBytes':sum(OWNERS.values())+CLOSURE+LEDGER,'globalWritersIntegrated':True,'sourceEnforcedCounts':dict(LIMITS)}
def encoded(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()+b'\n'
def _sync_dir(path):
 fd=os.open(path,os.O_RDONLY)
 try:os.fsync(fd)
 finally:close_fd(fd)
def _bound(path,n,append):
 old=path.stat().st_size if append and path.exists()else 0
 return max(0,((old+n+BLOCK-1)//BLOCK)*BLOCK-((old+BLOCK-1)//BLOCK)*BLOCK)+sum(BLOCK for p in path.parents if not p.exists())
def _product_dto_domain(path,evidence,owner):
 if owner!='dto':return None
 relative=str(Path(path).relative_to(evidence))
 m=re.fullmatch(r'sessions/[^/]+/product/media/([^/]+)',relative)
 if m is None:return None
 name=m[1]
 if re.fullmatch(r'video-[a-f0-9-]{36}-proof-s[0-9]{2}\.ajz01',name):return('sourceProof',11*MIB//2)
 if re.fullmatch(r'video-[a-f0-9-]{36}-report-0[1-8]\.json',name):return('reports',4*MIB)
 if re.fullmatch(r'capture-[a-f0-9-]{36}-original\.jpg',name):return('originalJPEG',MIB)
 if re.fullmatch(r'replay-[a-f0-9]{64}\.json\.gz',name):return('replayGZIP',256*1024)
 return('auxiliaryMediaMetadata',512*1024)

def _product_lifecycle_domain(path,evidence,owner):
 if owner!='lifecycle':return None
 relative=str(Path(path).relative_to(evidence))
 if re.fullmatch(r'sessions/[^/]+/product/journal/media-clock-[a-f0-9-]{36}-s[0-9]{2}\.ajz01',relative):return('mediaClock',768*1024)
 return None

class _Publication:
 def __init__(self,owner,deadline):self.owner=owner;self.pid=os.getpid();self.thread=threading.get_ident();self.active=True;self.deadline=deadline;self.evidence=owner.evidence.resolve()
 def check(self,inventory,deadline):
  if not self.active or self.owner.local.publication is not self or self.pid!=os.getpid()or self.thread!=threading.get_ident()or inventory.evidence!=self.evidence or self.owner.evidence!=self.evidence:raise RuntimeError('INVENTORY_PUBLICATION_CAPABILITY')
  if self.owner.root.name!='metadata-budget'or self.deadline is not None and deadline>self.deadline or deadline>time.monotonic_ns()+2_000_000_000:raise RuntimeError('INVENTORY_PUBLICATION_ROOT_DEADLINE')
  self.owner._deadline(deadline)
 def fast_check(self,deadline):
  # Full exact root/capability validation surrounds the scan. This per-entry
  # check retains live ownership/thread and the original monotonic deadline.
  if not self.active or self.owner.local.publication is not self or self.pid!=os.getpid()or self.thread!=threading.get_ident():raise RuntimeError('INVENTORY_PUBLICATION_CAPABILITY')
  self.owner._deadline(deadline)
class MetadataBudget:
 def __init__(self,root,inventory=None,*,free=None,mock=False):
  self.root=Path(root).absolute();self.evidence=self.root.parent;self.inventory=inventory;self.free=free if mock and free is not None else(lambda:shutil.disk_usage(self.evidence).free);self.mock=mock;self.thread_lock=threading.RLock();self.local=threading.local();self._verified_identity=None;self.state_path=self.root/'metadata-ledger.json';self.lock_path=self.root/'metadata-ledger.lock'
  if '..'in self.root.parts or any(p.is_symlink()for p in[self.root,*self.root.parents]):raise ValueError('METADATA_OWNED_ROOT')
  if not self.evidence.is_dir():raise ValueError('METADATA_EXISTING_OWNER_REQUIRED')
  self.root.mkdir(exist_ok=True);_sync_dir(self.root);_sync_dir(self.evidence)
 @classmethod
 def attach(cls,root,*,allow_mock=False):
  value=cls(root,mock=allow_mock)
  with value._locked():
   state=value._state()
   if not state['admitted']or state.get('closed')or state['mockOnly']and not allow_mock:raise ValueError('METADATA_ATTACH_REFUSED')
   if state.get('evidenceRoot')!=str(value.evidence.resolve())or state.get('budgetRoot')!=str(value.root.resolve())or state.get('sourceIdentity')!=value.source_identity():raise ValueError('METADATA_OWNER_OR_SOURCE_IDENTITY')
   value._verified_identity=state['sourceIdentity']
   if not state['mockOnly']:
    from .pipeline_contract import require_closed_contract
    require_closed_contract()
  return value
 @contextmanager
 def _ledger_directory(self):
  owner=os.open(self.evidence,os.O_RDONLY|os.O_DIRECTORY|getattr(os,'O_NOFOLLOW',0))
  try:
   directory=os.open(self.root.name,os.O_RDONLY|os.O_DIRECTORY|getattr(os,'O_NOFOLLOW',0),dir_fd=owner)
   try:yield directory
   finally:close_fd(directory)
  finally:close_fd(owner)
 @contextmanager
 def trace_stages(self,trace):
  previous=getattr(self.local,'stage_trace',None);self.local.stage_trace=trace
  try:yield
  finally:self.local.stage_trace=previous
 def _span(self,code):return trace_span(getattr(self.local,'stage_trace',None),code)
 def _deadline(self,deadline_ns):
  if deadline_ns is not None and time.monotonic_ns()>=deadline_ns:raise TimeoutError('PUBLICATION_TOTAL_DEADLINE')
 @contextmanager
 def _locked(self,deadline_ns=None):
  held=getattr(self.local,'publication',None)
  if held is not None:
   if held.owner is not self or held.pid!=os.getpid()or held.thread!=threading.get_ident()or not held.active:raise RuntimeError('PUBLICATION_CAPABILITY_IDENTITY')
   self._deadline(deadline_ns);yield held;return
  acquired=False
  try:
   with self._span('lock_thread'):
    if deadline_ns is None:self.thread_lock.acquire();acquired=True
    else:
     self._deadline(deadline_ns);acquired=self.thread_lock.acquire(timeout=max(0,(deadline_ns-time.monotonic_ns())/1e9))
     if not acquired:raise TimeoutError('PUBLICATION_THREAD_LOCK_DEADLINE')
   with self._span('lock_hold'):
    with self._ledger_directory()as directory:
     fd=os.open('metadata-ledger.lock',os.O_RDWR|os.O_CREAT|getattr(os,'O_NOFOLLOW',0),0o600,dir_fd=directory)
     try:
      if not stat.S_ISREG(os.fstat(fd).st_mode)or os.fstat(fd).st_nlink!=1:raise ValueError('METADATA_LOCK_REGULAR_SINGLE_LINK')
      with self._span('lock_file'):
       if deadline_ns is None:fcntl.flock(fd,fcntl.LOCK_EX)
       else:
        while True:
         self._deadline(deadline_ns)
         try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);break
         except OSError as error:
          if error.errno not in(errno.EACCES,errno.EAGAIN):raise
          time.sleep(min(.005,max(0,(deadline_ns-time.monotonic_ns())/1e9)))
      token=_Publication(self,deadline_ns);self.local.publication=token
      try:self._deadline(deadline_ns);yield token
      finally:token.active=False;self.local.publication=None
     finally:finish_cleanup([('ledger-unlock',lambda:fcntl.flock(fd,fcntl.LOCK_UN)),('ledger-close',lambda:os.close(fd))])
  finally:
   if acquired:self.thread_lock.release()
 @contextmanager
 def publication(self,*,deadline_ns=None):
  started=time.monotonic_ns();end=started+2_000_000_000
  if deadline_ns is not None:
   if type(deadline_ns)is not int:raise ValueError('TYPED_PUBLICATION_DEADLINE')
   end=min(end,deadline_ns)
  with self._locked(end)as token:
   yield token;self._deadline(end)
 def _inventory_fault(self,error,started):
  if getattr(self,'_inventory_fault_error',None)is error:return
  def short(value,maximum):return str(value).encode('unicode_escape').decode('ascii')[:maximum]
  self._inventory_fault_error=error;self.inventory_fault={'type':short(type(error).__name__,48),'reason':short(error,192),'path':short(str(getattr(error,'filename',''))[-160:],160),'frames':[{'file':short(f.filename[-160:],160),'line':f.lineno,'function':short(f.name,48)}for f in traceback.extract_tb(error.__traceback__)[-6:]],'startedHostNs':started,'failedHostNs':time.monotonic_ns(),'noMissingFileSkipped':True}
  error.add_note('ORIGINAL_INVENTORY_FAULT:'+json.dumps(self.inventory_fault,separators=(',',':')))
 def _scan_inventory(self,inventory,started,token):
  from .inventory import Inventory
  if type(inventory)is not Inventory or inventory.evidence!=self.evidence.resolve():raise ValueError('EXACT_ORIGINAL_INVENTORY_SCAN_ROOT')
  deadline=min(started+2_000_000_000,token.deadline)if token.deadline is not None else started+2_000_000_000
  try:
   self._deadline(deadline)
   with inventory.publication_snapshot(token,deadline):value=inventory()
   self._deadline(deadline);return value
  except BaseException as error:self._inventory_fault(error,started);raise
 def snapshot_inventory(self,inventory=None,*,closing=False):
  if type(closing)is not bool:raise TypeError('INVENTORY_CLOSING_MODE_BOOL')
  started=time.monotonic_ns();inventory=self.inventory if inventory is None else inventory
  if self.root.name!='metadata-budget':raise ValueError('EXACT_CAMPAIGN_PUBLICATION_ROOT')
  try:
   with self._locked(started+2_000_000_000)as token:
    value=self._scan_inventory(inventory,started,token)
    if self.state_path.exists():
     state=self._state();self._ready(state,closing=closing)
     if value['metadataBytes']>state['usedUpperBound']+LEDGER:raise ValueError('UNACCOUNTED_OUT_OF_DOMAIN_METADATA_WRITER')
     value={**value,'metadataAccountingUpperBoundAtScan':state['usedUpperBound']+LEDGER,'metadataAccountingWriteSequenceAtScan':state['writes']}
    self._deadline(started+2_000_000_000);return value
  except BaseException as error:self._inventory_fault(error,started);raise
 def _state(self):
  with self._ledger_directory()as directory:
   fd=os.open('metadata-ledger.json',os.O_RDONLY|getattr(os,'O_NOFOLLOW',0),dir_fd=directory)
   try:
    st=os.fstat(fd)
    if not stat.S_ISREG(st.st_mode)or st.st_nlink!=1 or st.st_size>LEDGER//2:raise ValueError('METADATA_LEDGER_REGULAR_BOUND')
    with os.fdopen(fd,'rb',closefd=False)as f:return json.loads(f.read(LEDGER//2+1))
   finally:close_fd(fd)
 def _save(self,v):
  with self._span('ledger_save'):
   with self._span('ledger_serial'):raw=encoded(v)
   if len(raw)>LEDGER//2:raise ValueError('METADATA_LEDGER_BOUND')
   with self._ledger_directory()as directory:
    fd=os.open('metadata-ledger.pending',os.O_WRONLY|os.O_CREAT|getattr(os,'O_NOFOLLOW',0),0o600,dir_fd=directory)
    try:
     if not stat.S_ISREG(os.fstat(fd).st_mode)or os.fstat(fd).st_nlink!=1:raise ValueError('METADATA_LEDGER_HARDLINK')
     with self._span('ledger_write'):
      os.ftruncate(fd,len(raw));os.lseek(fd,0,os.SEEK_SET);view=memoryview(raw)
      while view:
       n=os.write(fd,view)
       if not 0<n<=len(view):raise OSError('METADATA_LEDGER_SHORT_WRITE')
       view=view[n:]
     with self._span('ledger_fsync'),self._span('ledger_file_fsync'):os.fsync(fd)
    finally:close_fd(fd)
    with self._span('ledger_publish'):os.replace('metadata-ledger.pending','metadata-ledger.json',src_dir_fd=directory,dst_dir_fd=directory)
    with self._span('ledger_fsync'),self._span('ledger_dir_fsync'):os.fsync(directory)
 @staticmethod
 def _write_all(f,raw):
  view=memoryview(raw)
  while view:
   n=f.write(view)
   if type(n)is not int or not 0<n<=len(view):raise OSError('METADATA_PARTIAL_WRITE')
   view=view[n:]
 def source_identity(self):
  from .paths import PACKAGE_ROOT
  rows={str(p.relative_to(PACKAGE_ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(PACKAGE_ROOT.rglob('*'))if p.is_file()and p.suffix in('.py','.json','.txt')and '__pycache__'not in p.parts}
  return hashlib.sha256(encoded(rows)).hexdigest()
 def admit(self):
  from .inventory import Inventory
  started=time.monotonic_ns()
  with self._locked(started+2_000_000_000)as publication:
   if self.state_path.exists():raise ValueError('METADATA_ONE_ENTRY_NO_RESET')
   if self.inventory is None:raise ValueError('METADATA_FULL_INVENTORY_REQUIRED')
   if not self.mock:
    from .inventory import Inventory
    if type(self.inventory)is not Inventory or self.inventory.evidence!=self.evidence.resolve()or not getattr(self.inventory,'baselinePersisted',False):raise ValueError('EXACT_ORIGINAL_INVENTORY_CAMPAIGN_ROOT_REQUIRED')
   current=self._scan_inventory(self.inventory,started,publication)if type(self.inventory)is Inventory else self.inventory();n=current['metadataBytes'];plan=observer_envelope();future=plan['totalFutureBytes'];reason=None
   if type(n)is not int or n<0:raise ValueError('METADATA_TYPED_CURRENT_INVENTORY')
   if n+future>CAP:reason='METADATA_CURRENT_PLUS_SOURCE_ENVELOPES_AND_CLOSURE'
   if self.free()-future<10*2**30+256*MIB:reason='METADATA_DISK10GiB_PLUS256MiB'
   if not self.mock:
    from .inventory import Inventory
    if type(self.inventory)is not Inventory or self.inventory.evidence!=self.evidence.resolve()or not getattr(self.inventory,'baselinePersisted',False):raise ValueError('EXACT_ORIGINAL_INVENTORY_CAMPAIGN_ROOT_REQUIRED')
    from .pipeline_contract import require_closed_contract
    try:require_closed_contract()
    except BaseException as e:reason='WRITER_CONTRACT:'+str(e)
   value={'format':'aeris-metadata-budget','version':3,'entryInventory':current,'envelope':plan,'remaining':dict(OWNERS),'closureRemaining':CLOSURE,'closingOwners':dict(CLOSING_OWNERS),'failureRecords':0,'usedUpperBound':n,'admitted':reason is None,'refusal':reason,'writes':0,'counters':{k:0 for k in LIMITS},'mockOnly':self.mock,'evidenceRoot':str(self.evidence.resolve()),'budgetRoot':str(self.root.resolve()),'sourceIdentity':self.source_identity(),'inFlight':{},'leaseActors':{},'fileHighWater':{},'failed':None,'closed':False}
   if n+LEDGER>CAP or self.free()-LEDGER<10*2**30+256*MIB:raise ValueError('METADATA_UNDURABLE_ENTRY_CAPACITY')
   self._save(value);self._verified_identity=value['sourceIdentity']
   if reason:raise ValueError(reason)
   return value
 def require_real_actor(self):
  with self._locked():
   state=self._state();self._ready(state)
   if self._verified_identity is None:self._verified_identity=self.source_identity()
   if state['mockOnly']or state['sourceIdentity']!=self._verified_identity:raise ValueError('REAL_ACTOR_REQUIRES_SOURCE_BOUND_NONMOCK_LEDGER')
  return state
 def _ready(self,state,closing=False):
  if state.get('mockOnly')and not self.mock:raise ValueError('MOCK_LEDGER_NOT_RUNTIME_AUTHORITY')
  if state.get('evidenceRoot')!=str(self.evidence.resolve())or state.get('budgetRoot')!=str(self.root.resolve()):raise ValueError('METADATA_OWNER_ROOT_IDENTITY')
  if not state['admitted']or state.get('closed')or state.get('failed')and not closing:raise ValueError('METADATA_REFUSED_OR_POISONED')
  if state['usedUpperBound']+sum(state['remaining'].values())+sum(sum(v.values())for v in state.get('inFlight',{}).values())+state['closureRemaining']+LEDGER>CAP:raise ValueError('METADATA_LEDGER_SUM_CAP')
 def _path(self,path,owner=None,closing=False):
  path=Path(path).absolute()
  if '..'in path.parts or not path.is_relative_to(self.evidence)or any(p.is_symlink()for p in[path,*path.parents]):raise ValueError('METADATA_PATH_ESCAPE_OR_SYMLINK')
  rel=path.relative_to(self.evidence);parts=rel.parts
  if parts and parts[0]=='candidates'or 'raw'in parts or 'AP-state'in parts or path.name in('native-closed.tar','native-restart-metadata.tar','native-original-before-quarantine.tar','product-full-raw.tar.gz'):raise ValueError('METADATA_DO_NOT_RECLASSIFY_ORIGINAL_RAW_EXPORT_ARTIFACT')
  if owner is not None:
   text=rel.as_posix();session=r'sessions/[A-Za-z0-9_-]{1,64}/'
   api=session+r'android-api(?:-restart-[0-9]+)?/'
   observer=r'observer/[A-Za-z0-9_-]{1,64}/'
   patterns={}
   for name in('dto','stream','commands','command_receipts','requests','barriers'):patterns[name]=r'(?:'+api+'|'+observer+').+'
   patterns['dto']=r'(?:'+api+'|'+observer+'|'+session+r'product/media/).+'
   for name in('commands','command_receipts'):patterns[name]=r'(?:'+api+'|'+session+r'android-api-retained/|'+observer+').+'
   patterns.update(lifecycle=session+r'(?:lifecycle|lifecycle-proofs|product/journal|product/state)/.+',host_queries=session+r'host-queries/.+',child_output=session+r'processes/(?:ap|backend)\.(?:stdout|stderr)\.log',monitor=session+r'resources/.+',guardian=r'(?:guardian[^/]*|emulator[^/]*)/.+',campaign=r'(?:attempts/.+|campaign[^/]*\.json|avd-baseline\.json|sessions/[^/]+/(?:simulation|metadata)/.+)',audit=session+r'(?:full-raw-audit\.json|audit[^/]*|restart[^/]*)',external_task=r'(?:(?:diagnostics|reports)/.+|sessions/[^/]+/assisted-progress\.jsonl|'+session+r'product/(?:reports|writer)/.+)')
   if closing and owner=='closure'and text in('reports/owner-terminal.json','reports/owner-error.txt','reports/ui-failure-final.json','reports/hosthealth-ipc-client.bin','guardian/hosthealth-ipc-server.bin','reports/host-disk-attribution.bin','reports/product-writer-stage15.bin'):pass
   elif closing and path.is_relative_to(self.root)and path.name.startswith('failure'):pass
   elif owner not in patterns or re.fullmatch(patterns[owner],text)is None:raise ValueError('METADATA_OWNER_PATH_DOMAIN:'+str(owner))
  return path
 @contextmanager
 def _parent(self,path,create=False,namespace_changes=None):
  # Directory fd traversal prevents final/ancestor symlink substitution between
  # path validation and open. Every opened component is O_NOFOLLOW.
  fds=[os.open(self.evidence,os.O_RDONLY|os.O_DIRECTORY|getattr(os,'O_NOFOLLOW',0))]
  try:
   for part in path.relative_to(self.evidence).parts[:-1]:
    if create:
     try:os.mkdir(part,0o700,dir_fd=fds[-1])
     except FileExistsError:pass
     else:
      if namespace_changes is not None:namespace_changes.add(fds[-1])
    fds.append(os.open(part,os.O_RDONLY|os.O_DIRECTORY|getattr(os,'O_NOFOLLOW',0),dir_fd=fds[-1]))
   yield fds[-1],fds
  finally:
   finish_cleanup([('parent-close',lambda fd=fd:os.close(fd))for fd in reversed(fds)])
 def prepare_directory(self,owner,path):
  path=Path(path).absolute();probe=self._path(path/'.directory-budget-marker',owner)
  with self._locked():
   state=self._state();self._ready(state);self._path(probe,owner);charge=sum(4096 for p in[path,*path.parents]if p.is_relative_to(self.evidence)and not p.exists())
   self._spend(state,owner,charge,False);state['writes']+=1;self._save(state)
   try:
    with self._parent(probe,create=True)as(parent,fds):
     for fd in reversed(fds):os.fsync(fd)
   except BaseException as error:
    state['failed']=type(error).__name__+':'+str(error)[:512]
    try:self._save(state)
    except BaseException:error.add_note('DIRECTORY_FAILURE_LEDGER_UNDURABLE')
    raise
  return {'directory':str(path),'chargedBytes':charge,'durableParentChain':True}
 def secure_open(self,owner,path,*,closing=False):
  path=self._path(path,owner,closing)
  with self._locked():
   self._ready(self._state(),closing);self._path(path,owner,closing)
   with self._parent(path,create=False)as(parent,fds):
    fd=os.open(path.name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,'O_NOFOLLOW',0),0o600,dir_fd=parent)
    state=self._state();key=str(path.relative_to(self.evidence));state['fileHighWater'][key]={'owner':owner,'bytes':0}
    try:self._save(state)
    except BaseException:close_fd(fd);raise
    return fd
 def charge_ephemeral_socket(self,owner,path):
  """Source-fixed Unix health socket allocation charged before bind, no refund."""
  path=self._path(path,owner)
  if not(owner=='guardian'and path.name=='health.sock'or owner=='external_task'and re.fullmatch(r'reports/pw0[12]\.sock',path.relative_to(self.evidence).as_posix())):raise ValueError('SOURCE_PRIVATE_HEALTH_OR_PRODUCT_WRITER_SOCKET_ONLY')
  with self._locked():
   state=self._state();self._ready(state);self._path(path,owner);names=state.setdefault('ephemeralNamespaces',[]);name=str(path.relative_to(self.evidence))
   if name in names or len(names)>=3 or path.exists():raise ValueError('SOURCE_HEALTH_SOCKET_FRESH_BOUND')
   self._spend(state,owner,4096,False);names.append(name);state['writes']+=1;self._save(state)
  return {'path':name,'chargedBytes':4096,'sourceMaximumSockets':3,'durableBeforeBind':True}
 def publish_lifecycle_proof(self,pending,target,io):
  pending=self._path(pending,'lifecycle');target=self._path(target,'lifecycle')
  if pending.parent!=target.parent or not re.fullmatch(r'[a-f0-9]{64}\.json',target.name)or pending.name!=target.name+'.pending':raise ValueError('SOURCE_LIFECYCLE_PROOF_PUBLICATION')
  with self.publication():os.replace(pending,target);io.dirsync(target.parent)
 def ensure(self,owner,charge,*,closing=False):
  with self._locked():
   state=self._state();self._ready(state,closing)
   token=getattr(self.local,'claim',None);pool=state['closingOwners']if closing else(state['inFlight'][token]if token is not None and owner in state['inFlight'].get(token,{})else state['remaining'])
   if owner not in pool or type(charge)is not int or charge<0 or pool[owner]<charge:raise ValueError('METADATA_OWNER_PRE_DISPATCH_CAP:'+owner)
   if self.free()-charge<10*2**30+256*MIB:raise ValueError('METADATA_PER_WRITE_DISK_FLOOR')
 def available(self,owner):
  with self._locked():
   state=self._state();self._ready(state);return state['remaining'][owner]
 def reserve_lease(self,claims):
  with self._span('reserve'):
   token=secrets.token_hex(8)
   with self._locked():
    state=self._state();self._ready(state)
    if len(state['inFlight'])>=16:raise ValueError('METADATA_INFLIGHT_BOUND')
    for owner,n in claims.items():
     if owner not in state['remaining']or type(n)is not int or n<0 or state['remaining'][owner]<n:raise ValueError('METADATA_PRE_DISPATCH_RESERVATION:'+owner)
    for owner,n in claims.items():state['remaining'][owner]-=n
    state['inFlight'][token]=dict(claims);state['leaseActors'][token]={'parentPID':os.getpid(),'reservedHostNs':time.monotonic_ns(),'childPID':None};self._save(state)
   return token

 def bind_lease_child(self,token,pid):
  if type(pid)is not int or pid<=0:raise ValueError('LEASE_ACTUAL_PID')
  with self._locked():
   state=self._state();self._ready(state);row=state['leaseActors'][token]
   if row['parentPID']!=os.getpid()or row['childPID']is not None:raise ValueError('LEASE_CHILD_OWNERSHIP')
   row['childPID']=pid;row['spawnedHostNs']=time.monotonic_ns();self._save(state)
 @contextmanager
 def use_lease(self,token):
  previous=getattr(self.local,'claim',None)
  with self._locked():
   if token not in self._state()['inFlight']:raise ValueError('METADATA_LEASE_NOT_OWNED')
  self.local.claim=token
  try:yield
  finally:self.local.claim=previous
 def release_lease(self,token):
  with self._span('release'):
   with self._locked():
    state=self._state()
    if token not in state['inFlight']:raise ValueError('METADATA_LEASE_NO_DOUBLE_RELEASE')
    left=state['inFlight'].pop(token);state['leaseActors'].pop(token,None)
    for owner,n in left.items():state['remaining'][owner]+=n
    self._save(state)

 @contextmanager
 def operation(self,claims):
  """Atomic multi-owner predispatch reservation, bound to this thread's writes."""
  previous=getattr(self.local,'claim',None)
  token=secrets.token_hex(8)
  with self._span('reserve'):
   with self._locked():
    state=self._state();self._ready(state)
    if len(state['inFlight'])>=16:raise ValueError('METADATA_INFLIGHT_BOUND')
    for owner,n in claims.items():
     if owner not in state['remaining']or type(n)is not int or n<0 or state['remaining'][owner]<n:raise ValueError('METADATA_PRE_DISPATCH_RESERVATION:'+owner)
    for owner,n in claims.items():state['remaining'][owner]-=n
    state['inFlight'][token]=dict(claims);state['leaseActors'][token]={'parentPID':os.getpid(),'reservedHostNs':time.monotonic_ns(),'childPID':None};self._save(state)
  self.local.claim=token
  primary=None
  try:yield token
  except BaseException as error:primary=error;raise
  finally:
   self.local.claim=previous
   try:
    with self._span('release'):
     with self._locked():
      state=self._state();left=state['inFlight'].pop(token,{});state['leaseActors'].pop(token,None)
      for owner,n in left.items():state['remaining'][owner]+=n
      self._save(state)
   except BaseException as release:
    if primary is not None:primary.add_note('OPERATION_RELEASE_UNDURABLE:'+str(release))
    else:raise
 def _spend(self,state,owner,charge,closing):
  if closing:
   if state['closureRemaining']<charge or state['closingOwners'].get(owner,0)<charge:raise ValueError('METADATA_CLOSURE_RESERVE_EXHAUSTED:'+owner)
   state['closureRemaining']-=charge;state['closingOwners'][owner]-=charge
  else:
   token=getattr(self.local,'claim',None);pool=state['inFlight'][token]if token is not None and owner in state['inFlight'].get(token,{})else state['remaining']
   if pool.get(owner,-1)<charge:raise ValueError('METADATA_OWNER_WORST_CASE_EXHAUSTED:'+owner)
   pool[owner]-=charge
  state['usedUpperBound']+=charge
 def reserve_counter(self,kind,n):
  """Pre-fund source-fixed local health credits; no hot ledger calls or reset."""
  if type(n)is not int or(kind,n)not in(('guardianRows',4200),('monitorRows',2100)):raise ValueError('SOURCE_FIXED_HEALTH_COUNTER_CREDITS')
  with self._locked():
   state=self._state();self._ready(state)
   if state['counters'][kind]+n>LIMITS[kind]:raise ValueError('METADATA_SOURCE_COUNTER:'+kind)
   state['counters'][kind]+=n;self._save(state)
  return {'kind':kind,'reservedCredits':n,'globalCeiling':LIMITS[kind],'reservedNotProduced':True,'refunded':False}
 def tick(self,kind):
  with self._locked():
   state=self._state();self._ready(state)
   if kind not in LIMITS or state['counters'][kind]>=LIMITS[kind]:raise ValueError('METADATA_SOURCE_COUNTER:'+kind)
   state['counters'][kind]+=1;self._save(state);return state['counters'][kind]
 def write(self,owner,path,raw,*,append=False,closing=False,_failure=False):
  with self._span('payload_write'):
   path=self._path(path,owner,closing)
   if type(raw)not in(bytes,bytearray,memoryview)or len(raw)>(CLOSURE if closing else OWNERS.get(owner,0)):raise ValueError('METADATA_INPUT_BUFFER_SOURCE_BOUND')
   raw=bytes(raw)
   if owner=='closure'and path.relative_to(self.evidence).as_posix()=='reports/product-writer-stage15.bin'and(append or len(raw)>4096):raise ValueError('SOURCE_PRODUCT_WRITER_STAGE15_EXACT4KiB')
   if owner=='closure'and path.relative_to(self.evidence).as_posix()=='reports/host-disk-attribution.bin'and(append or len(raw)>65536):raise ValueError('SOURCE_HOSTDISK_EXACT64KiB')
   if owner=='closure'and path.relative_to(self.evidence).as_posix()in('reports/hosthealth-ipc-client.bin','guardian/hosthealth-ipc-server.bin')and(append or len(raw)>49152):raise ValueError('SOURCE_HOSTHEALTH_IPC_EXACT48KiB')
   if owner=='closure'and path.relative_to(self.evidence).as_posix()in('reports/owner-terminal.json','reports/owner-error.txt','reports/ui-failure-final.json')and(append or len(raw)>(4096 if path.name=='owner-terminal.json'else 16384 if path.name=='owner-error.txt'else 32768)):raise ValueError('SOURCE_OWNER_TERMINAL_OR_TRACE_EXACT_BOUND')
   with self._locked():
    state=self._state();self._ready(state,closing);self._path(path,owner,closing)
    if _failure:
     if state['failureRecords']>=56:raise ValueError('CLOSURE_FAILURE_RECORD56_BOUND')
     state['failureRecords']+=1;path=self.root/('failure-%06d.json'%state['writes'])
    if owner not in state['remaining']and not closing:raise ValueError('METADATA_UNKNOWN_OWNER')
    if path.exists()and not append:raise FileExistsError('METADATA_NO_OVERWRITE:'+str(path))
    charge=_bound(path,len(raw),append)
    if self.free()-charge<10*2**30+256*MIB:raise ValueError('METADATA_PER_WRITE_DISK_FLOOR')
    if owner=='external_task'and re.fullmatch(r'reports/runtime-event-[0-9]{3}-detail\.json',path.relative_to(self.evidence).as_posix()):
     used=state.get('runtimeEventDetailAllocatedBytes',0)
     if type(used)is not int or used<0 or used+charge>64*1024:raise ValueError('RUNTIME_EVENT_DETAILS_TASK64KiB_ALLOCATED')
     state['runtimeEventDetailAllocatedBytes']=used+charge
    subclass=_product_dto_domain(path,self.evidence,owner)or _product_lifecycle_domain(path,self.evidence,owner)
    if subclass is not None:
     key,limit=subclass;used=state.setdefault('productDTOAllocatedBytes'if owner=='dto'else'productLifecycleAllocatedBytes',{});current=used.get(key,0)
     if type(current)is not int or current<0 or current+charge>limit:raise ValueError('PRODUCT_TASK_SUBALLOCATION:'+owner+':'+key)
     # Before-write credit, including allocation rounding; unknown writes never
     # refund this task-wide balance and another case cannot reset it.
     used[key]=current+charge
    with self._span('quota_charge'):self._spend(state,owner,charge,closing)
    state['writes']+=1;self._save(state)
    try:
     namespace_changes=set();relative=path.relative_to(self.evidence).as_posix();product_path=re.fullmatch(r'sessions/[A-Za-z0-9_-]{1,64}/product/(?:journal|state|media|reports)/[A-Za-z0-9_.-]{1,96}',relative)is not None or relative=='reports/product-clock-proofs.jsonl'
     with self._parent(path,create=True,namespace_changes=namespace_changes)as(parent,fds):
      flags=os.O_WRONLY|getattr(os,'O_NOFOLLOW',0)
      if append:
       try:fd=os.open(path.name,flags|os.O_CREAT|os.O_EXCL,0o600,dir_fd=parent);namespace_changes.add(parent)
       except FileExistsError:fd=os.open(path.name,flags,0o600,dir_fd=parent)
      else:fd=os.open(path.name,flags|os.O_CREAT|os.O_EXCL,0o600,dir_fd=parent);namespace_changes.add(parent)
      try:
       st=os.fstat(fd)
       if not stat.S_ISREG(st.st_mode)or st.st_nlink!=1:raise ValueError('METADATA_PAYLOAD_REGULAR_SINGLE_LINK')
       old_end=st.st_size;offset=old_end if append else 0;new_end=offset+len(raw)
       # APFS sequential-append preallocation may run about1MiB ahead. Extend
       # sparse EOF FIRST and write at a position strictly within that EOF.
       # This controls allocation before write; it is not an observed-size refund.
       os.lseek(fd,offset,os.SEEK_SET)
       try:
        with self._span('payload_data_write'):
         os.ftruncate(fd,new_end);view=memoryview(raw)
         while view:
          n=os.write(fd,view)
          if type(n)is not int or not 0<n<=len(view):raise OSError('METADATA_PARTIAL_WRITE')
          view=view[n:]
        if os.lseek(fd,0,os.SEEK_CUR)!=new_end:raise OSError('METADATA_WRITE_POSITION')
        with self._span('payload_fsync'),self._span('payload_file_fsync'):os.fsync(fd)
       except BaseException as primary:
        try:os.ftruncate(fd,max(old_end,min(new_end,os.lseek(fd,0,os.SEEK_CUR))))
        except BaseException as shrink:primary.add_note('UNCERTAIN_PADDING_PREFIX:'+str(shrink))
        raise
      finally:close_fd(fd)
      # File content and immediate parent always sync. Only unchanged higher
      # product ancestors are omitted; every successful mkdir parent is kept.
      for directory in reversed(fds):
       if not product_path or directory==parent or directory in namespace_changes:
        with self._span('payload_fsync'),self._span('payload_dir_fsync'):os.fsync(directory)
    except BaseException as e:
     state['failed']=type(e).__name__+':'+str(e)[:512]
     try:self._save(state)
     except BaseException:pass
     raise
    return {'bytes':len(raw),'chargedBytes':charge,'writeSequence':state['writes'],'sha256':hashlib.sha256(raw).hexdigest()}

 def append_json(self,owner,path,value,*,maximum,closing=False):
  raw=encoded(value)
  if len(raw)>maximum:raise ValueError('METADATA_JSON_SOURCE_BOUND:'+owner)
  return self.write(owner,path,raw,append=True,closing=closing)
 def failure(self,error,*,detail=None):
  row={'format':'aeris-metadata-failure','version':3,'failure':type(error).__name__+':'+str(error)[:1024],'detail':detail,'failureNotes':[str(n)[:256]for n in getattr(error,'__notes__',())[-8:]],'flightAcceptance':False,'hostNs':time.monotonic_ns()};raw=encoded(row)
  if len(raw)>4096:raw=encoded({**row,'detail':'DETAIL_EXCEEDS_CLOSURE_BOUND'})
  return self.write('closure',self.root/'failure.json',raw,closing=True,_failure=True)
 def snapshot(self):
  with self._locked():return self._state()
 def observe_inventory(self,actual):
  with self._locked():
   state=self._state();self._ready(state)
   observed=actual.get('metadataAccountingUpperBoundAtScan',state['usedUpperBound']+LEDGER)
   if type(observed)is not int or actual['metadataBytes']>observed or actual['metadataBytes']>state['usedUpperBound']+LEDGER:raise ValueError('UNACCOUNTED_OUT_OF_DOMAIN_METADATA_WRITER')
  return actual
 def check(self):
  from .inventory import Inventory
  started=time.monotonic_ns()
  with self._locked(started+2_000_000_000)as token:
   state=self._state();self._ready(state)
   if self.inventory is not None:
    actual=self._scan_inventory(self.inventory,started,token)['metadataBytes']if type(self.inventory)is Inventory else self.inventory()['metadataBytes']
    if actual>state['usedUpperBound']+LEDGER:raise ValueError('UNACCOUNTED_OUT_OF_DOMAIN_METADATA_WRITER')
   if self.inventory is not None:self._deadline(started+2_000_000_000)
   return state
 def poison(self,error):
  with self._locked():
   state=self._state();state['failed']=type(error).__name__+':'+str(error)[:512]
   try:self._save(state)
   except BaseException:error.add_note('METADATA_POISON_LEDGER_UNDURABLE')
 def write_fd(self,owner,path,fd,raw,operation,*,closing=False):
  path=self._path(path,owner,closing);raw=bytes(raw)
  with self._locked():
   state=self._state();self._ready(state,closing);self._path(path,owner,closing);actual=os.fstat(fd);named=path.lstat()
   if not stat.S_ISREG(actual.st_mode)or actual.st_nlink!=1 or(actual.st_dev,actual.st_ino)!=(named.st_dev,named.st_ino):raise ValueError('METADATA_FD_PATH_IDENTITY')
   old=actual.st_size;position=os.lseek(fd,0,os.SEEK_CUR);new=max(old,position+len(raw));key=str(path.relative_to(self.evidence));registered=state['fileHighWater'].get(key)
   if registered is None or registered['owner']!=owner:raise ValueError('METADATA_FD_NOT_REGISTERED_BY_EXCLUSIVE_OPEN')
   high=((new+4095)//4096)*4096;charge=max(0,high-registered['bytes']);registered['bytes']=max(high,registered['bytes'])
   allowance=state['closureRemaining']if closing else state['remaining'].get(owner,-1)
   if charge>allowance or self.free()-charge<10*2**30+256*MIB:raise ValueError('METADATA_EXTERNAL_FD_PREWRITE_REFUSAL')
   self._spend(state,owner,charge,closing);state['writes']+=1;self._save(state)
   try:
    if fcntl.fcntl(fd,fcntl.F_GETFL)&os.O_APPEND:raise ValueError('BUDGET_FD_APPEND_FLAG_NOT_ALLOCATION_CONTROLLED')
    os.ftruncate(fd,new);os.lseek(fd,position,os.SEEK_SET);n=operation()
    if type(n)is not int or not 0<n<=len(raw)or os.lseek(fd,0,os.SEEK_CUR)!=position+n:raise OSError('BUDGET_FD_SHORT_OR_INVALID_WRITE')
    # Short writes expose only their actual written prefix until the journal's
    # existing write loop supplies the rest. Never leave accepted artificial0s.
    if n<len(raw):os.ftruncate(fd,max(old,position+n))
    return n
   except BaseException as e:
    try:os.ftruncate(fd,max(old,min(new,os.lseek(fd,0,os.SEEK_CUR))))
    except BaseException as shrink:e.add_note('UNCERTAIN_PADDING_PREFIX:'+str(shrink))
    state['failed']=type(e).__name__+':'+str(e)[:512]
    try:self._save(state)
    except BaseException:pass
    raise
 def reserve_export(self,target,maximum_bytes):
  target=Path(target).absolute()
  if '..'in target.parts or not target.is_relative_to(self.evidence)or target.name not in('native-closed.tar','native-restart-metadata.tar','native-original-before-quarantine.tar','product-full-raw.tar.gz')or any(p.is_symlink()for p in[target,*target.parents])or type(maximum_bytes)is not int or not 0<maximum_bytes<=168*MIB:raise ValueError('ORIGINAL_EXPORT_DOMAIN')
  relative=target.relative_to(self.evidence).parts
  if len(relative)!=3 or relative[0]!='sessions':raise ValueError('ORIGINAL_REGISTERED_SESSION_EXPORT_DOMAIN')
  registered=False
  for receipt in(self.evidence/'attempts').glob('attempt-*-cases/case-*.json'):
   value=json.loads(receipt.read_bytes())
   if value.get('context',{}).get('run')==relative[1]:registered=True
  if not registered:raise ValueError('EXPORT_CASE_NOT_REGISTERED_IN_ORIGINAL_INVENTORY')
  with self._locked():
   state=self._state();self._ready(state);exports=state.setdefault('exports',{});key=str(target.relative_to(self.evidence))
   if key in exports or sum(v['reservedBytes']for v in exports.values())+maximum_bytes>192*MIB:raise ValueError('EXPORT192MiB_AGGREGATE_RESERVATION')
   exports[key]={'reservedBytes':maximum_bytes,'closed':False};self._save(state);return exports[key]
 def finish_export(self,target):
  target=Path(target).absolute();key=str(target.relative_to(self.evidence))
  with self._locked():
   state=self._state();self._ready(state,True);row=state['exports'][key];actual=target.stat().st_size
   if actual>row['reservedBytes']:raise ValueError('EXPORT_ORIGINAL_CAP_VIOLATION')
   h=hashlib.sha256()
   with target.open('rb')as f:
    for block in iter(lambda:f.read(65536),b''):h.update(block)
   row.update(reservedBytes=actual,closed=True,sha256=h.hexdigest());self._save(state);return row

class BoundedCapture:
 """Parent-owned pipe pump. Output is checked before write, never direct FD.

 On overflow the known prefix is durable and capture is incomplete. This owner
 does not terminate an AP or imply ground; its caller retains ownership.
 """
 def __init__(self,budget,owner,path,maximum_bytes,*,closing=False):
  self.budget=budget;self.owner=owner;self.path=Path(path);self.maximum=maximum_bytes;self.closing=closing;self.bytes=0;self.failure=None;self.complete=False;self.budget.write(owner,self.path,b'',append=True,closing=closing)
 def feed(self,raw):
  raw=bytes(raw);room=self.maximum-self.bytes
  if len(raw)>room:
   prefix=raw[:max(0,room)]
   self.failure='CAPTURE_OVERFLOW_FAILED_PREFIX';primary=ValueError(self.failure)
   try:
    if prefix:self.budget.write(self.owner,self.path,prefix,append=True,closing=self.closing);self.bytes+=len(prefix)
   except BaseException as storage:primary.add_note('PREFIX_STORAGE_SECONDARY:'+str(storage));raise primary from storage
   raise primary
  try:self.budget.write(self.owner,self.path,raw,append=True,closing=self.closing);self.bytes+=len(raw)
  except BaseException as error:self.failure=type(error).__name__+':'+str(error);raise
 def finish(self,eof=True):
  self.complete=eof and self.failure is None
  return {'path':str(self.path),'bytes':self.bytes,'captureComplete':self.complete,'failure':self.failure}

def capture_command(budget,owner,argv,*,deadline_ns,stdout_limit=131072,stderr_limit=16384,now=time.monotonic_ns,spawn=subprocess.Popen,trace=None):
 """Bounded in-memory command capture; caller persists prefix/receipt explicitly."""
 if type(stdout_limit)is not int or not 0<=stdout_limit<=131072 or type(stderr_limit)is not int or not 0<=stderr_limit<=16384:raise ValueError('CAPTURE_SOURCE_LIMIT')
 if budget is not None:budget.ensure(owner,((stdout_limit+stderr_limit+8191)//4096)*4096)
 sel=selectors.DefaultSelector()
 try:
  with trace_span(trace,'popen'):p=spawn(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 except BaseException:
  finish_cleanup([('unspawned-selector-close',sel.close)]);raise
 out={'stdout':bytearray(),'stderr':bytearray()};failure=None;eof=set();first=set()
 try:
  for name,stream in[('stdout',p.stdout),('stderr',p.stderr)]:os.set_blocking(stream.fileno(),False);sel.register(stream,selectors.EVENT_READ,name)
  while sel.get_map():
   if now()>=deadline_ns:raise TimeoutError('BOUNDED_COMMAND_DEADLINE')
   for key,_ in sel.select(min(.05,max(0,(deadline_ns-now())/1e9))):
    name=key.data;limit=stdout_limit if name=='stdout'else stderr_limit;raw=os.read(key.fileobj.fileno(),min(65536,limit+1-len(out[name])))
    if not raw:
     trace.point('eof_'+name)if trace is not None else None;sel.unregister(key.fileobj);eof.add(name);continue
    if name not in first:
     trace.point('first_'+name)if trace is not None else None;first.add(name)
    out[name].extend(raw)
    if len(out[name])>limit:raise ValueError('BOUNDED_COMMAND_OVERFLOW_FAILED_PREFIX:'+name)
  with trace_span(trace,'wait'):code=p.wait(timeout=max(.001,(deadline_ns-now())/1e9))
  if now()>=deadline_ns:raise TimeoutError('BOUNDED_COMMAND_FINAL_DEADLINE_AFTER_EOF')
  if code:raise RuntimeError('BOUNDED_COMMAND_EXIT:'+str(code))
 except BaseException as e:failure=e
 finally:
  def stop_owned():
   if p.poll()is None:p.terminate()
   try:p.wait(timeout=2)
   except subprocess.TimeoutExpired:p.kill();p.wait(timeout=2)
  def drain_ready_prefix():
   # A late Popen/EOF may leave already-available bytes in a pipe. Read only a
   # bounded nonblocking prefix; a failed command never becomes complete here.
   for name,stream in[('stdout',p.stdout),('stderr',p.stderr)]:
    if name in eof:continue
    os.set_blocking(stream.fileno(),False);limit=stdout_limit if name=='stdout'else stderr_limit
    while len(out[name])<=limit:
     try:raw=os.read(stream.fileno(),min(65536,limit+1-len(out[name])))
     except BlockingIOError:break
     if not raw:
      trace.point('eof_'+name)if trace is not None else None;eof.add(name);break
     out[name].extend(raw)
     if name not in first:
      trace.point('first_'+name)if trace is not None else None;first.add(name)
  prior=failure
  with trace_span(trace,'cleanup'):failure=cleanup(failure,[('command-stop-wait',stop_owned),('failed-ready-prefix-drain',drain_ready_prefix),('selector-close',sel.close),('stdout-close',p.stdout.close),('stderr-close',p.stderr.close)])
  if now()>=deadline_ns:
   late=TimeoutError('BOUNDED_COMMAND_FINAL_DEADLINE_AFTER_CLEANUP')
   if failure is None:failure=late
   else:failure.add_note(str(late))
  if failure is not prior or len(getattr(failure,'__notes__',())):
   if budget is not None:
    try:budget.failure(failure,detail={'operation':'capture_command.cleanup','captureComplete':False})
    except BaseException as storage:failure.add_note('CAPTURE_CLEANUP_DIAGNOSTIC_UNDURABLE:'+type(storage).__name__+':'+str(storage)[:256])
 if trace is not None and trace.failure is not None:
  if failure is None:failure=trace.failure
  else:failure.add_note('CAPTURE_TRACE_SECONDARY:'+str(trace.failure)[:256])
 return {'stdout':bytes(out['stdout']),'stderr':bytes(out['stderr']),'exit':p.returncode,'captureComplete':failure is None and len(eof)==2,'failure':failure}
