"""G8 isolated retained single-owner launcher. Imported tests never allocate or execute."""
from pathlib import Path
import os,sys,json,stat,hashlib,selectors,subprocess,time,datetime,signal,shutil,re
R=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(R/'pilot/beta06g3'))
from prepare_executable import _directory_fd,_hash_fd,_identity
sys.path.insert(0,str(R/'pilot/beta06g4/flight'))
from readiness import SerialReadiness
DOCKER='/usr/local/bin/docker'
IMAGE_ID='sha256:e27f0236daf88218a8a76a2c58c4c185e36fbc0c67e05d12ca5af9292f442f84'
IMAGE='rtr-aeris-sim32-trace-builder@'+IMAGE_ID
BINARY='1d3479f1fd2b9c6d85c95f38eeb8c105e6735ea1dc372736ddc07efd5162fc41'
PROFILE='beta06g8-native-arm64-exec-4.7.1'
STREAM=2*2**20; META=256*1024
sys.path.insert(0,str(R/'pilot/beta06g8'))
from quota import admit as quota_admit,load_policy
QP=load_policy()
def check_quota(root):
 if root!=R:return # Pure fake-run fixtures cannot point at the actual campaign.
 return quota_admit('runtime',remaining_ap=4,remaining_hosts=2,closed_runs=[],claim_id='runtime-resource-scan')

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(65536),b''):h.update(b)
 return h.hexdigest()
def put(p,d):
 p=Path(p);encoded=json.dumps(d,indent=2).encode();limit=8192 if p.name.endswith('-result.json') else 64*1024
 if len(encoded)>limit:raise ValueError('EXACT_SERIALIZED_METADATA_BOUND')
 out=p.parent.parent if p.parent.name=='diagnostics' else p.parent
 if (out/'request.json').exists():
  fixed=sum(q.stat().st_size for q in out.rglob('*')if q.is_file()and q.name!='raw.jsonl'and 'ap-state'not in q.parts and not(q.parent.name=='diagnostics'and(q.name.endswith('.bin')or q.name.endswith('-result.json'))))
  reserve=0 if p.name=='closure.json' else 512*1024
  if fixed+len(encoded)>2*2**20-reserve:raise ValueError('AP_FIXED2MIB_CLOSURE_RESERVED')
 with p.open('xb') as f:f.write(encoded);f.flush();os.fsync(f.fileno())
 fd=os.open(p.parent,os.O_RDONLY|os.O_DIRECTORY)
 try:os.fsync(fd)
 finally:os.close(fd)
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def qualify(path):
 p=Path(path);parent=_directory_fd(p.parent);fd=None
 try:
  fd=os.open(p.name,os.O_RDONLY|os.O_NOFOLLOW,dir_fd=parent);s=os.fstat(fd)
  if not stat.S_ISREG(s.st_mode) or s.st_size!=7172336 or stat.S_IMODE(s.st_mode)!=0o755:raise ValueError('EXACT_REGULAR_7172336_MODE0755_REQUIRED')
  os.lseek(fd,0,0);header=os.read(fd,64)
  if header[:6]!=b'\x7fELF\x02\x01' or int.from_bytes(header[18:20],'little')!=183:raise ValueError('ELF64_LE_AARCH64_REQUIRED')
  if _hash_fd(fd)!=BINARY or _identity(s)!=_identity(os.fstat(fd)) or _identity(s)!=_identity(os.stat(p.name,dir_fd=parent,follow_symlinks=False)):raise ValueError('DESCRIPTOR_BOUND_BINARY_SHA_IDENTITY_REQUIRED')
  return {'path':str(p.relative_to(R)),'sha256':BINARY,'bytes':s.st_size,'mode':'0755','device':s.st_dev,'inode':s.st_ino,'mtimeNs':s.st_mtime_ns,'descriptorBound':True}
 finally:
  if fd is not None:os.close(fd)
  os.close(parent)

class Budget:
 def __init__(self,limit):self.limit=limit;self.retained=0;self.observed=0
class Capture:
 """At most one 64KiB read per selected pipe; no reader queue or accumulated output."""
 def __init__(self,argv,base,budgets,*,popen=subprocess.Popen,clock=time.monotonic):
  self.argv=argv;self.base=Path(base);self.clock=clock;self.started=clock();self.budgets=budgets;self.files={};self.counts={};self.hashes={};self.selector=selectors.DefaultSelector();self.failure=None;self.finished=False;self.proc=None
  try:
   for key in ['stdout','stderr']:
    self.files[key]=self.base.with_name(self.base.name+'-'+key+'.bin').open('xb');self.counts[key]={'observedBytes':0,'retainedBytes':0,'overflow':False};self.hashes[key]=hashlib.sha256()
   self.proc=popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=0)
   for key in self.files:self.selector.register(getattr(self.proc,key),selectors.EVENT_READ,key)
  except BaseException as e:
   self.failure='SPAWN_OR_CAPTURE_FAILED:'+repr(e);self.finish();raise
 def pump(self,timeout=.05):
  for key,_ in self.selector.select(timeout):
   stream=key.data
   try:data=os.read(key.fileobj.fileno(),65536)
   except OSError as e:self.failure='CAPTURE_READ_FAILED:'+repr(e);raise RuntimeError(self.failure)
   if not data:self.selector.unregister(key.fileobj);key.fileobj.close();continue
   b=self.budgets[stream];c=self.counts[stream];c['observedBytes']+=len(data);b.observed+=len(data);keep=data[:max(0,b.limit-b.retained)]
   if keep:self.files[stream].write(keep);self.files[stream].flush();os.fsync(self.files[stream].fileno());self.hashes[stream].update(keep);c['retainedBytes']+=len(keep);b.retained+=len(keep)
   if len(keep)!=len(data):c['overflow']=True;self.failure='CAPTURE_OVERFLOW';raise RuntimeError(self.failure)
 def complete(self):return self.proc is not None and self.proc.poll() is not None and not self.selector.get_map()
 def finish(self,terminate=False):
  if self.finished:return
  if self.proc and terminate and self.proc.poll() is None:self.proc.terminate()
  # Drain termination to a fixed deadline; never wait indefinitely on inherited pipes.
  deadline=self.clock()+2
  if self.proc:
   while not self.complete() and self.clock()<deadline:
    try:self.pump(.02)
    except BaseException as e:self.failure=self.failure or repr(e);break
   if self.proc.poll() is None:
    self.proc.kill()
    try:self.proc.wait(timeout=1)
    except BaseException:self.failure=self.failure or 'CAPTURE_PROCESS_KILL_UNKNOWN'
   if self.selector.get_map():self.failure=self.failure or 'CAPTURE_DRAIN_INCOMPLETE'
  for key in list(self.selector.get_map().values()):
   try:key.fileobj.close()
   except OSError:pass
  self.selector.close()
  for f in self.files.values():f.flush();os.fsync(f.fileno());f.close()
  result={'argv':self.argv,'startedMono':self.started,'finishedMono':self.clock(),'returncode':self.proc.poll() if self.proc else None,'error':self.failure,'streams':{k:{**v,'sha256':self.hashes[k].hexdigest(),'path':self.base.name+'-'+k+'.bin'} for k,v in self.counts.items()},'fsynced':True}
  
  if len(json.dumps(result).encode())>8192:raise RuntimeError('CAPTURE_RESULT8KIB_BOUND')
  put(self.base.with_name(self.base.name+'-result.json'),result);self.finished=True;return result
 def text(self,stream='stdout'):
  # Only bounded retained command metadata is read, never attached whole logs.
  return self.base.with_name(self.base.name+'-'+stream+'.bin').read_text(errors='replace')

class Runner:
 def __init__(self,out):
  self.out=out;self.meta=Budget(160*1024);self.closure_meta=Budget(64*1024);self.closure_control=Budget(32*1024);self.closing=False;self.attached={'stdout':Budget(STREAM),'stderr':Budget(STREAM)};self.event=Budget(META);self.sequence=0;self.background=[];self.normal_captures=0;self.closure_captures=0
 def capture(self,argv,label,kind='meta'):
  cleanup=label in ['closure-before','closure-stop','wait','terminal-inspect']
  if cleanup:
   if self.closure_captures>=4:raise RuntimeError('EXACT_FOUR_RESERVED_CLOSURE_COMMANDS')
   self.closure_captures+=1
  else:
   if self.normal_captures>=423:raise RuntimeError('AP_CAPTURE_COUNT_RESERVE_CLOSURE')
   self.normal_captures+=1
  metadata=self.closure_control if self.closing and label in ['closure-stop','wait'] else self.closure_meta if self.closing else self.meta
  budgets=self.attached if kind=='attached' else {'stdout':self.event,'stderr':self.event} if kind=='events' else {'stdout':metadata,'stderr':metadata}
  c=Capture(argv,self.out/label,budgets);return c
 def command(self,argv,label,timeout=8,check=True):
  c=self.capture(argv,label);deadline=time.monotonic()+timeout
  try:
   while not c.complete():
    for b in self.background:
     if not b.finished:b.pump(0)
    c.pump(.03)
    if time.monotonic()>deadline:raise RuntimeError('COMMAND_DEADLINE:'+label)
   result=c.finish()
   if result['error'] or (check and result['returncode']!=0):raise RuntimeError('COMMAND_FAILED:'+label)
   return c.text()
  except BaseException as e:c.failure=c.failure or str(e);c.finish(terminate=True);raise
 def tick(self):
  for b in self.background:
   if not b.finished:b.pump(0)


def identity(i,cid,rid,ap):
 if i.get('Id')!=cid or i.get('Name')!='/aeris-beta06g8-'+rid or i.get('Image')!=IMAGE_ID or i.get('Config',{}).get('Labels',{}).get('aeris.task')!='beta06g8' or i['Config']['Labels'].get('aeris.run')!=rid:raise ValueError('EXACT_CID_NAME_RUN_TASK_REQUIRED')
 cfg=i['Config'];a=cfg.get('Cmd',[]);h=i['HostConfig'];env=cfg.get('Env',[])
 def at(flag):return a[a.index(flag)+1]
 if cfg.get('Entrypoint') not in [None,[]] or a[0]!='/aeris/arducopter' or at('--model')!='quad' or at('--speedup')!='1' or at('--home')!='10.854,106.807,10,0' or at('--defaults')!='/aeris/copter.parm,/task/sitl.parm':raise ValueError('QUALIFIED_LIVE_ENTRY')
 if [x for x in env if x.startswith('AERIS_DIRECT_TRACE=')]!=['AERIS_DIRECT_TRACE=0'] or any(x.split('=',1)[0] in ['LD_PRELOAD','AERIS_AP_TRACE','AERIS_INSTRUMENT'] for x in env):raise ValueError('QUALIFIED_LIVE_ENV')
 if h.get('LogConfig',{}).get('Type')!='json-file' or h.get('LogConfig',{}).get('Config',{}).get('max-size')!='2m' or h.get('LogConfig',{}).get('Config',{}).get('max-file')!='2':raise ValueError('QUALIFIED_LOG_BOUNDS')
 if h.get('AutoRemove') is not False or h.get('Privileged') is not False or h.get('CapAdd') not in [None,[]] or h.get('NanoCpus')!=1000000000 or h.get('Memory')!=268435456 or [x.upper() for x in h.get('CapDrop',[])]!=['ALL'] or not any(x in ['no-new-privileges','no-new-privileges=true'] for x in h.get('SecurityOpt',[])) or h.get('NetworkMode')!='bridge':raise ValueError('QUALIFIED_LIVE_RESOURCES')
 mounts=[x for x in i.get('Mounts',[]) if x['Destination']=='/aeris/arducopter']
 if len(mounts)!=1 or mounts[0]['Type']!='bind' or mounts[0]['RW'] is not False or Path(mounts[0]['Source'])!=ap:raise ValueError('QUALIFIED_LIVE_BINARY_MOUNT')
 return i

def request_cap(e):
 requests=list((e/'runs').glob('*/request.json'))
 actual=[p for p in requests if json.loads(p.read_text()).get('mode')=='sitl']
 if len(actual)>4:raise ValueError('MAX_FOUR_G8_REQUESTS')
 return len(actual)
def inventory_guard(rows,rid):
 if len(rows)>=4:raise ValueError('MAX_FOUR_RETAINED_G8_CONTAINERS')
 for i in rows:
  cid=i.get('Id','');name=i.get('Name','');labels=i.get('Config',{}).get('Labels',{})
  if not re.fullmatch('[a-f0-9]{64}',cid) or not re.fullmatch('/aeris-beta06g8-s[a-f0-9]{20}',name) or labels.get('aeris.task')!='beta06g8' or name!='/aeris-beta06g8-'+labels.get('aeris.run','') or i['State'].get('Running'):raise ValueError('RETAINED_OWNERSHIP_OR_RUNNING_REFUSAL')
  if not isinstance(i.get('SizeRw'),int) or i['SizeRw']<0 or i['SizeRw']>64*2**20:raise ValueError('RETAINED_WRITABLE64MIB_OR_UNKNOWN')
  logs=i.get('HostConfig',{}).get('LogConfig',{})
  if logs.get('Type')!='json-file' or logs.get('Config',{}).get('max-size')!='2m' or logs.get('Config',{}).get('max-file')!='2':raise ValueError('RETAINED_LOG_BOUND_REQUIRED')
  if labels['aeris.run']==rid:raise ValueError('DUPLICATE_RUN_NO_RETRY')

def run(rid,*,root=R,runner_factory=Runner):
 if not re.fullmatch('s[a-f0-9]{20}',rid):raise ValueError('EXACT_RUN_ID')
 e=root/'evidence/beta06/generation08/flight';out=e/'runs'/rid
 if not out.is_dir():raise ValueError('PREEXISTING_REQUEST_REQUIRED')
 diag=out/'diagnostics';diag.mkdir();runner=runner_factory(diag);cid=None;error=None;stopped=False;attach=events=None;owned=False;polls=0;before=None;owner_parent=os.getppid();start=time.monotonic();stop_signal=[False]
 def inspect(label):return json.loads(runner.command([DOCKER,'inspect','--size',cid],label))[0]
 def state(label):return json.loads(runner.command([DOCKER,'inspect','--format','{{json .State}}',cid],label))
 def check_running(label):
  s=state(label)
  if not s.get('Running'):raise RuntimeError('GUEST_EXIT_BEFORE_CLOSURE:'+str(s))
  return s
 for sig in [signal.SIGTERM,signal.SIGINT]:signal.signal(sig,lambda *_:stop_signal.__setitem__(0,True))
 try:
  pins=root/'evidence/beta06/generation08/flight-pins01.json'
  if (out/'source-pins.json').read_bytes()!=pins.read_bytes():raise ValueError('EXACT_GENERATION07_PINS')
  for p,h in json.loads(pins.read_text())['files'].items():
   if sha(root/p)!=h:raise ValueError('SOURCE_PIN:'+p)
  request_cap(e);check_quota(root)
  a=json.loads((out/'admission.json').read_text());samples=a['samples']
  if len(samples)!=31 or a['durationMs']<30000 or min(x['freeBytes'] for x in samples)<29*2**30 or max(max(x['freeBytes'] for x in samples[:i+1])-v['freeBytes'] for i,v in enumerate(samples))>256*2**20 or shutil.disk_usage(root).free<29*2**30:raise ValueError('STABLE_ADMISSION_REQUIRED')
  retained=runner.command([DOCKER,'ps','-aq','--no-trunc','--filter','label=aeris.task=beta06g8'],'retained-ids').split()
  if len(retained)>4 or any(not re.fullmatch('[a-f0-9]{64}',x) for x in retained):raise ValueError('RETAINED_CONTAINER_CAP_OR_IDS')
  inventory=[json.loads(runner.command([DOCKER,'inspect','--size',x],'retained-'+str(n)))[0] for n,x in enumerate(retained)];inventory_guard(inventory,rid);put(diag/'retained-before.json',inventory)
  image=json.loads(runner.command([DOCKER,'image','inspect',IMAGE],'image'))[0]
  if image['Id']!=IMAGE_ID or image['Architecture']!='arm64' or image['Os']!='linux' or image['Config'].get('Entrypoint'):raise ValueError('EXACT_CACHED_IMAGE_REQUIRED')
  if any(v.split('=',1)[0] in ['LD_PRELOAD','AERIS_AP_TRACE','AERIS_INSTRUMENT'] or v.startswith('AERIS_DIRECT_TRACE=') and v!='AERIS_DIRECT_TRACE=0' for v in image['Config'].get('Env',[])):raise ValueError('CACHED_IMAGE_ENV_REFUSAL')
  ap=root/'.local/beta06g3/arducopter';artifact=qualify(ap);put(diag/'artifact.json',artifact)
  name='aeris-beta06g8-'+rid;labels={'aeris.task':'beta06g8','aeris.run':rid};apstate=out/'ap-state';apstate.mkdir()
  argv=[DOCKER,'create','--name',name,'--label','aeris.task=beta06g8','--label','aeris.run='+rid,'--platform','linux/arm64','--pull','never','--network','bridge','--cpus','1','--memory','256m','--cap-drop','ALL','--security-opt','no-new-privileges','--log-driver','json-file','--log-opt','max-size=2m','--log-opt','max-file=2','-p','127.0.0.1:5972:5760','-v',str(root/'runtime/sitl')+':/aeris:ro','-v',str(ap)+':/aeris/arducopter:ro','-e','AERIS_DIRECT_TRACE=0','-v',str(root/'pilot/field02/flight')+':/task:ro','-v',str(apstate)+':/state','-w','/state',IMAGE,'/aeris/arducopter','-w','--model','quad','--home','10.854,106.807,10,0','--defaults','/aeris/copter.parm,/task/sitl.parm','--speedup','1']
  event_since=utc()
  put(diag/'intent.json',{'eventSince':event_since,'at':utc(),'argv':argv,'artifact':artifact,'labels':labels,'name':name,'ordinal':request_cap(e),'retained':True,'autoremove':False,'ownerParentPid':owner_parent,'APDeadlineS':540})
  # No intervening allocation or retry between descriptor requalification and create.
  if qualify(ap)!=artifact:raise ValueError('ARTIFACT_CHANGED_IMMEDIATELY_BEFORE_CREATE')
  created=runner.command(argv,'create');cid=created.strip()
  if not re.fullmatch('[a-f0-9]{64}',cid):raise ValueError('FULL_CREATED_CID_REQUIRED')
  before=identity(inspect('created-inspect'),cid,rid,ap);owned=True
  if before['State'].get('Running'):raise ValueError('CREATED_MUST_NOT_ALREADY_RUN')
  put(diag/'created.json',{'containerId':cid,'name':name,'labels':labels,'inspectSha256':sha(diag/'created-inspect-stdout.bin')})
  events=runner.capture([DOCKER,'events','--since',event_since,'--filter','container='+cid,'--format','{{json .}}'],'events','events');runner.background.append(events)
  attach=runner.capture([DOCKER,'start','--attach',cid],'attach','attached');runner.background.append(attach)
  ready_deadline=min(start+540,time.monotonic()+25);readiness=SerialReadiness('attach:'+cid);offsets={'stdout':0,'stderr':0}
  def consume_console():
   for stream in offsets:
    with (diag/('attach-'+stream+'.bin')).open('rb') as f:
     f.seek(offsets[stream]);chunk=f.read(65536)
    if chunk:readiness.feed(stream,chunk,attempt='attach:'+cid);offsets[stream]+=len(chunk)
  while True:
   runner.tick()
   if events.proc.poll() is not None:raise RuntimeError('EVENT_CAPTURE_EXITED')
   # Test liveness before accepting even already-durable complete marker text.
   if attach.proc.poll() is not None:raise RuntimeError('GUEST_ATTACH_EARLY_EXIT:'+str(attach.proc.poll()))
   if os.getppid()!=owner_parent:raise RuntimeError('APP_PARENT_LOST')
   if time.monotonic()>ready_deadline:raise RuntimeError('GUEST_SERIAL_READY_DEADLINE')
   consume_console()
   if readiness.ready(alive=attach.proc.poll() is None):break
   time.sleep(.05)
  running=identity(inspect('running-inspect'),cid,rid,ap);s=running['State']
  if not s.get('Running') or s.get('Pid',0)<=0:raise ValueError('ACTUAL_RUNNING_PID_REQUIRED')
  # inspect drains captures; finish observing its durable prefixes before hashing.
  for stream in offsets:
   while offsets[stream]<(diag/('attach-'+stream+'.bin')).stat().st_size:consume_console()
  proof=readiness.proof(alive=attach.proc.poll() is None)
  for stream in offsets:
   path=diag/('attach-'+stream+'.bin')
   if path.stat().st_size!=proof['streams'][stream]['retainedPrefixBytes'] or sha(path)!=proof['streams'][stream]['retainedPrefixSha256']:raise RuntimeError('READY_RETAINED_STREAM_SHA_OR_COUNT_DRIFT')
   proof['streams'][stream]['path']='diagnostics/'+path.name
   proof['streams'][stream]['captureFsyncedBeforeRead']=True
  put(out/'guest-ready.json',{'at':utc(),'containerId':cid,'serial0ListeningObserved':True,'basis':'BOUNDED_SAME_ATTEMPT_DUAL_STREAM_ATTACHED_CONSOLE_BEFORE_ONE_HOST_CONNECTION','noTCPProbeOrRetry':True,'proof':proof})
  put(out/'launch.json',{'at':utc(),'containerId':cid,'containerName':name,'labels':labels,'imageId':IMAGE_ID,'pid':s['Pid'],'startedAt':s['StartedAt'],'command':argv,'binarySha256':BINARY,'qualifiedProfile':PROFILE,'binaryPath':str(ap.relative_to(root)),'binaryMode':'0755','retained':True,'createReceipt':'diagnostics/create-result.json','platform':'linux/arm64','observerEnabled':False,'port':5972,'physics':'ARDUPILOT_INTERNAL_QUAD_NOT_SIM32_OR_HERA','speedup':1,'freeBytes':shutil.disk_usage(root).free,'forecastBytes':256*2**20,'hardDeadlineS':540,'attemptTotalMaximumS':600,'ownerParentPid':owner_parent})
  rebooted=False;next_inspect=0;next_usage=0;disk=[]
  while not stop_signal[0] and not (out/'stop-request.json').exists():
   runner.tick();now=time.monotonic();free=shutil.disk_usage(root).free;disk.append((now,free));disk=[x for x in disk if now-x[0]<=15];dt=now-disk[0][0];rate=max(0,(disk[0][1]-free)/dt) if dt>=2 else 0
   if os.getppid()!=owner_parent:raise RuntimeError('APP_PARENT_LOST_CLOSE_OWNED_SIMULATOR')
   if now-start>540:raise RuntimeError('OWNED_SIMULATOR_DEADLINE')
   if free<28*2**30 or free-rate*15<20*2**30:raise RuntimeError('RESOURCE_28GIB_OR_FORECAST20GIB')
   if events.proc.poll() is not None:raise RuntimeError('EVENT_CAPTURE_EXITED')
   if attach.proc.poll() is not None:raise RuntimeError('ATTACHED_PROCESS_EXITED')
   if now>=next_inspect:
    check_running('poll-'+str(polls));polls+=1;next_inspect=now+2
   if now>=next_usage:
    check_quota(root)
    if sum(1 for p in apstate.rglob('*'))>128:raise RuntimeError('AP_STATE128_ENTRY_QUOTA')
    if sum(1 for p in out.rglob('*'))>1536:raise RuntimeError('AP_SLOT1536_ENTRY_QUOTA')
    if sum(p.stat().st_size for p in out.rglob('*')if p.is_file())>90*2**20:raise RuntimeError('AP_SLOT90MIB_QUOTA')
    if sum(p.stat().st_size for p in apstate.rglob('*') if p.is_file())>64*2**20:raise RuntimeError('AP_STATE64MIB')
    # Inspect size/logs is bounded and periodic, preserving retained writable state.
    size=json.loads(runner.command([DOCKER,'inspect','--size','--format','{{json .SizeRw}}',cid],'usage-'+str(polls)))
    if not isinstance(size,int) or size<0 or size>64*2**20:raise RuntimeError('CONTAINER_WRITABLE64MIB_OR_UNKNOWN')
    next_usage=now+15
   if (out/'fault-request.json').exists() and not rebooted:
    if json.loads((out/'fault-request.json').read_text())!={'kind':'REBOOT_OWNED_AP_PROCESS','run':rid}:raise ValueError('FAULT_REQUEST_BOUND')
    rebooted=True;b=identity(inspect('reboot-before'),cid,rid,ap)
    put(out/'reboot-intent.json',{'containerId':cid,'beforePid':b['State']['Pid'],'beforeStartedAt':b['State']['StartedAt'],'at':utc(),'method':'EXACT_CID_EXPLICIT_STOP_START_ONCE'})
    runner.command([DOCKER,'stop','-t','2',cid],'reboot-stop');attach.finish();runner.background.remove(attach)
    attach=runner.capture([DOCKER,'start','--attach',cid],'reboot-attach','attached');runner.background.append(attach)
    deadline=time.monotonic()+5;after=None
    while time.monotonic()<deadline:
     runner.tick();after=identity(inspect('reboot-after-'+str(polls)),cid,rid,ap);polls+=1
     if after['State'].get('Running') and after['State']['Pid']>0:break
     if attach.proc.poll() is not None:raise RuntimeError('REBOOT_START_EXITED')
     time.sleep(.05)
    if not after['State'].get('Running') or after['State']['Pid']==b['State']['Pid'] or after['State']['StartedAt']==b['State']['StartedAt']:raise RuntimeError('ACTUAL_REBOOT_PID_TIME_REQUIRED')
    put(out/'reboot-observation.json',{'restarted':True,'containerId':cid,'beforePid':b['State']['Pid'],'afterPid':after['State']['Pid'],'beforeStartedAt':b['State']['StartedAt'],'afterStartedAt':after['State']['StartedAt'],'at':utc(),'source':'DOCKER_ACTUAL_OWNED_AP_PROCESS_RESTART','noReconnect':True,'mavlinkNewBootObserved':False,'attachedCapture':'reboot-attach','sameContainer':True})
   time.sleep(.05)
 except BaseException as ex:error=str(ex)
 finally:
  # Failed capture must never prevent exact owned-CID closure commands.
  runner.background=[];runner.closing=True
  closure_errors=[];terminal=None
  if cid:
   try:
    terminal=identity(inspect('closure-before'),cid,rid,root/'.local/beta06g3/arducopter');owned=True
   except BaseException as ex:closure_errors.append(str(ex))
   if owned and (terminal is None or terminal['State'].get('Running')):
    try:runner.command([DOCKER,'stop','-t','3',cid],'closure-stop')
    except BaseException as ex:closure_errors.append(str(ex))
   try:runner.command([DOCKER,'wait',cid],'wait',timeout=5)
   except BaseException as ex:closure_errors.append(str(ex))
   try:
    terminal=identity(inspect('terminal-inspect'),cid,rid,root/'.local/beta06g3/arducopter');stopped=terminal['State'].get('Running') is False
    if not stopped:raise RuntimeError('STOPPED_NOT_OBSERVED')
   except BaseException as ex:closure_errors.append(str(ex))
  for c in [attach,events]:
   if c:
    try:
     result=c.finish(terminate=(c is events))
     if result and result.get('error') and not (c is events and result['error']=='CAPTURE_DRAIN_INCOMPLETE'):closure_errors.append(result['error'])
    except BaseException as ex:closure_errors.append(str(ex))
  # No rm, prune or name lookup. A failed inspect cannot authorize stopping an unowned CID.
  if error or closure_errors:
   if cid and owned:
    try:
     recovery=runner.capture([DOCKER,'logs',cid],'recovered-logs','attached');end=time.monotonic()+3
     while not recovery.complete() and time.monotonic()<end:recovery.pump(.03)
     recovery.finish(terminate=not recovery.complete());put(diag/'recovered-label.json',{'diagnosticRecoveryOnly':True,'uninterruptedAttachmentProven':False})
    except BaseException as ex:closure_errors.append('RECOVERY:'+str(ex))
  put(out/'closure.json',{'containerId':cid,'stopped':stopped,'error':'; '.join(x for x in [error,*closure_errors] if x) or None,'explicitStop':stop_signal[0] or (out/'stop-request.json').exists(),'freeBytes':shutil.disk_usage(root).free,'stateRetained':True,'containerRetained':bool(cid),'ownedIdentityValidated':owned,'terminalState':terminal.get('State') if terminal else None,'writableBytes':terminal.get('SizeRw') if terminal else None,'containerWritableLimitBytes':64*2**20,'containerLogLimitBytes':4*2**20,'notFlightCompletion':True,'noAutomaticRetry':True,'noContainerDeleted':True,'captureBudgets':{'stdoutObserved':runner.attached['stdout'].observed,'stdoutRetained':runner.attached['stdout'].retained,'stderrObserved':runner.attached['stderr'].observed,'stderrRetained':runner.attached['stderr'].retained,'eventsObserved':runner.event.observed,'metadataObserved':runner.meta.observed+getattr(runner,'closure_meta',Budget(0)).observed+getattr(runner,'closure_control',Budget(0)).observed},'at':utc()})
 return 1 if error or closure_errors or not stopped else 0

if __name__=='__main__':sys.exit(run(sys.argv[1]))
