"""Continuous resource guard; original numeric quotas and fail-closed power/sleep policy."""
from pathlib import Path
import hashlib,json,os,re,shutil,subprocess,threading,time
from .admission import DiskGuard
from . import policy
from .candidate import allocated_unique,put
from .paths import repository
from pilot.betaintegrated01.runtime.ap_stage import canonical
MIB=2**20
class ResourceMonitor:
 def __init__(self,root,recording_seconds,campaign,*,inventory,power,guardian,now=time.monotonic_ns,wall=time.time,budget=None):
  self.budget=budget;self.root=Path(root);self.seconds=policy.duration(recording_seconds);self.campaign=campaign;self.inventory=inventory;self.guardian=guardian;self.now=now;self.wall=wall;self.health=None;self.done=threading.Event();self.thread=None;self.failure=None;self.entry=None;self.closure=None;self.close_failure=None
  self._lifecycle_lock=threading.RLock();self._start_attempted=False;self._start_attempts=0;self._start_phase='NEVER_ATTEMPTED';self._constructed_host_ns=self.now()
  if power is not host_power:raise ValueError('SOURCE_REAL_HOST_POWER_PROVIDER_REQUIRED')
 def start(self):
  with self._lifecycle_lock:
   if self.closure is not None or self.close_failure is not None:raise RuntimeError('RESOURCE_MONITOR_START_AFTER_CLOSE')
   if type(self._start_attempted)is not bool or self._start_attempted is not False or type(self._start_attempts)is not int or self._start_attempts!=0 or self._start_phase!='NEVER_ATTEMPTED':raise RuntimeError('RESOURCE_MONITOR_ONE_START_ATTEMPT')
   self._start_attempted=True;self._start_attempts=1;self._start_phase='ATTEMPTED'
   if self.health is not None:raise RuntimeError('RESOURCE_MONITOR_ONE_START')
   from .metadata_budget import MetadataBudget
   from .host_health import HostHealth
   if type(self.budget)is not MetadataBudget:raise ValueError('MONITOR_EXACT_BUDGET_REQUIRED')
   self.budget.require_real_actor();budget=policy.case_budget(shutil.disk_usage(repository()).free,self.seconds)
   if budget['admitted']is not True:raise ValueError('ORIGINAL_WHOLE_CASE_ADMISSION')
   self.health=HostHealth(self.root,self.budget,'monitor',inventory=self.inventory,check_inventory=self._caps);self._start_phase='HEALTH_ALLOCATED';ready=self.health.start();self._start_phase='HEALTH_STARTED';self.disk=self.health.disk;self.check();barrier=self.barrier();self.entry={'admitted':True,'realPriming':True,'capacity':budget,**ready,'healthBarrier':barrier};self._put('resource-entry.json',self.entry);self._start_phase='RUNNING';return self.entry
 def _caps(self,v):
  caps={'metadataBytes':64*MIB,'exportBytes':192*MIB,'AVDPositiveGrowthBytes':512*MIB,'artifactBytes':9*MIB,'nativePhysicalBytes':160*MIB,'nativeLogicalBytes':512*MIB,'checkpointArchiveBytes':512*1024,'checkpointArchiveCount':8,'taskAllocatedBytes':policy.campaign_budget()['taskHardPeakBytes']}
  for key,limit in caps.items():
   if v.get(key) is None and key in ('nativePhysicalBytes','nativeLogicalBytes','checkpointArchiveBytes','checkpointArchiveCount'):
    enforced=v.get('sourceEnforcedNativeQuotas',{})
    if enforced.get(key)!=limit or type(enforced.get(key)) is not int or re.fullmatch('[a-f0-9]{64}',str(enforced.get('APKSourceSHA256'))) is None or v.get('nativeQuotaObservation')!='SOURCE_ENFORCED_UNMEASURED_ARCHIVES_NOT_HOST_PRIVATE_INVENTORY':raise RuntimeError('NATIVE_SOURCE_ENFORCED_QUOTA_DECLARATION')
    continue
   if type(v.get(key))is not int or not 0<=v[key]<=limit:raise RuntimeError('RESOURCE_CAP:'+key)
  return v
 def check(self,n=0):
  if self.failure:raise RuntimeError(self.failure)
  if self.thread is not None and not self.thread.is_alive()and not self.done.is_set():raise RuntimeError('RESOURCE_INVENTORY_OBSERVER_DEAD')
  self.campaign.check();g=self.guardian()
  if type(g.get('hostNs'))is not int or not 0<=self.now()-g['hostNs']<=2_000_000_000 or g.get('alive')is not True or g.get('closed')is not False or g.get('sourceVerified')is not True:raise RuntimeError('OWNED_GUARDIAN_ORIGINAL_SOURCE_LIVENESS')
  if self.health is None:raise RuntimeError('RESOURCE_REAL_HEALTH_NOT_STARTED')
  self.health.check(n)
 def barrier(self):
  self.check();local=self.health.barrier();g=self.guardian();target=g['audit']['producedSeq'];deadline=self.now()+2_000_000_000
  while g['audit']['committedSeq']<target:
   if self.now()>=deadline:raise TimeoutError('GUARDIAN_DURABLE_PREFIX_BARRIER')
   time.sleep(.005);g=self.guardian()
  from .host_health import verify_audit_prefix
  ref={'path':str(self.guardian.root/'health-audit.bin'),'bytes':g['audit']['committedBytes'],'sha256':g['audit']['committedSHA256'],'throughSeq':g['audit']['committedSeq'],'durable':True}
  return {'monitor':local,'monitorOriginalPrefix':verify_audit_prefix(local,'monitor',expected_root=self.root),'guardian':{**ref,'instance':g['instance'],'pid':g['pid'],'pendingNewerRows':g['audit']['pendingRows'],'barrierHostNs':self.now()},'guardianOriginalPrefix':verify_audit_prefix(ref,'guardian',expected_root=self.guardian.root),'durableRequiredPrefixes':True}
 def _put(self,name,value,closing=False):
  raw=canonical(value)+b'\n'
  if len(raw)>32768:raise ValueError('MONITOR_TERMINAL32KiB')
  return self.budget.write('monitor',self.root/name,raw,closing=closing)
 def close(self):
  with self._lifecycle_lock:
   if self.closure is not None:return dict(self.closure)
   if self.close_failure is not None:raise self.close_failure
   try:
    if self._never_started():return self._close_never_started()
    return self._close()
   except BaseException as e:
    self.close_failure=e
    try:self._put('resource-failure.json',{'failure':type(e).__name__+':'+str(e)[:512],'hostNs':self.now(),'disk':None if self.health is None else self.health.disk.diagnostic(),'hostHealthTraces':None if self.health is None else{'acquisition':self.health.power_trace.snapshot(),'writer':self.health.audit.trace.snapshot(),'inventoryFault':getattr(self.health,'inventory_fault',None)},'durablyDrained':False},closing=True)
    except BaseException as secondary:e.add_note('MONITOR_FAILURE_DIAGNOSTIC_SECONDARY:'+str(secondary)[:256])
    raise
 def _never_started(self):
  # An unknown/partial start is never converted into a no-actor disposition.
  return type(self._start_attempted)is bool and self._start_attempted is False and type(self._start_attempts)is int and self._start_attempts==0 and type(self._start_phase)is str and self._start_phase=='NEVER_ATTEMPTED'and self.health is None and self.thread is None and self.entry is None and self.failure is None and not self.done.is_set()
 def _close_never_started(self):
  from .metadata_budget import MetadataBudget
  if not self._never_started()or type(self.budget)is not MetadataBudget:raise RuntimeError('RESOURCE_NO_ACTOR_POSITIVE_PROOF_REQUIRED')
  # A constructor that allocated a lease and then failed has startAttempted=True.
  # Also positively inspect the shared original ledger for any monitor claim.
  with self.budget._locked():
   state=self.budget._state();self.budget._ready(state,closing=True)
   leases=state.get('inFlight');actors=state.get('leaseActors')
   if type(leases)is not dict or type(actors)is not dict or set(leases)!=set(actors)or any(type(claims)is not dict or 'monitor'in claims for claims in leases.values()):raise RuntimeError('RESOURCE_NO_ACTOR_MONITOR_LEASE_UNKNOWN_OR_PRESENT')
   observed=self.now()
   if type(self._constructed_host_ns)is not int or type(observed)is not int or not 0<=self._constructed_host_ns<=observed or type(state.get('writes'))is not int or state['writes']<0 or re.fullmatch('[a-f0-9]{64}',str(state.get('sourceIdentity')))is None:raise RuntimeError('RESOURCE_NO_ACTOR_ORIGINAL_PROOF_FIELDS')
   proof={'startAttempted':False,'startAttempts':0,'startPhase':'NEVER_ATTEMPTED','healthObjectAbsent':True,'threadObjectAbsent':True,'entryAbsent':True,'monitorLeaseClaims':0,'originalLedgerWrites':state['writes'],'originalLedgerSourceIdentity':state['sourceIdentity'],'originalBudgetRoot':str(self.budget.root),'constructedHostNs':self._constructed_host_ns,'observedHostNs':observed,'monitorSourceSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
  value={'format':'aeris-resource-monitor-closure','version':2,'disposition':'NOT_STARTED_NO_ACTOR','status':'CLOSED_NO_ACTOR_NOT_ACCEPTANCE','failure':None,'hostNs':self.now(),'noActorProof':proof,'durablyDrained':False,'health':None,'guardianOriginalPrefix':None,'APGroundProven':False,'flightAcceptance':False,'authorityRestored':False}
  self._put('resource-close.json',value,closing=True);self.done.set();self.closure=dict(value);return value
 def _close(self):
  self.done.set()
  if self.thread:self.thread.join(timeout=8)
  if self.thread and self.thread.is_alive():raise RuntimeError('RESOURCE_MONITOR_DID_NOT_CLOSE')
  if self.health is None:raise RuntimeError('RESOURCE_HEALTH_NEVER_STARTED')
  local=self.health.close()
  if self.failure:raise RuntimeError(self.failure)
  # The guardian continues serving the next case. This explicit prefix fence
  # covers every required guardian row through this case's final observation.
  g=self.guardian();target=g['audit']['producedSeq'];deadline=self.now()+2_000_000_000
  while g['audit']['committedSeq']<target:
   if self.now()>=deadline:raise TimeoutError('GUARDIAN_FINAL_DURABLE_PREFIX_BARRIER')
   time.sleep(.005);g=self.guardian()
  from .host_health import verify_audit_prefix
  ref={'path':str(self.guardian.root/'health-audit.bin'),'bytes':g['audit']['committedBytes'],'sha256':g['audit']['committedSHA256'],'throughSeq':g['audit']['committedSeq'],'durable':True};guardian_proof=verify_audit_prefix(ref,'guardian',expected_root=self.guardian.root)
  value={'guardianOriginalPrefix':guardian_proof,'failure':None,'hostNs':self.now(),'disk':self.disk.diagnostic(),'health':local,'guardianAuditBarrier':{**ref,'instance':g['instance'],'throughSeq':target,'committedSeq':g['audit']['committedSeq'],'pendingNewerRows':g['audit']['pendingRows'],'durable':True},'durablyDrained':True};self._put('resource-close.json',value,closing=True);self.closure=dict(value);return value

def host_power(*,budget=None,path=None,owner='monitor'):
 if budget is None:return _host_power_reserved(budget=budget,path=path,owner=owner)
 with budget.operation({owner:16384}):return _host_power_reserved(budget=budget,path=path,owner=owner)
def _host_power_reserved(*,budget=None,path=None,owner='monitor'):
 from .metadata_budget import capture_command
 result=capture_command(budget,owner,['pmset','-g','batt'],deadline_ns=time.monotonic_ns()+2_000_000_000,stdout_limit=192,stderr_limit=128);raw=result['stdout'];err=result['stderr'];error=result['failure']
 if err and error is None:error=RuntimeError('POWER_STDERR_NOT_EMPTY')
 ref=None
 if budget is not None:
  if path is None:raise ValueError('POWER_ORIGINAL_RAW_PATH')
  path=Path(path);offset=path.stat().st_size if path.exists()else 0;budget.write(owner,path,raw+err,append=True,closing=error is not None);ref=[offset,len(raw),len(err),hashlib.sha256(raw).hexdigest(),hashlib.sha256(err).hexdigest()]
 if error is not None:raise error
 text=raw.decode();m=re.search(r'(\d+)%',text)
 if m is None:raise RuntimeError('UNKNOWN_POWER')
 return {'powerRaw':ref,'AC':"'AC Power'"in text,'batteryPercent':int(m.group(1))}if ref is not None else{'raw':text,'AC':"'AC Power'"in text,'batteryPercent':int(m.group(1))}
