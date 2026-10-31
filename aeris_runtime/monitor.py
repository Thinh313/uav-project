"""Continuous resource guard; original numeric quotas and fail-closed power/sleep policy."""
from pathlib import Path
import json,os,re,shutil,subprocess,threading,time
from .admission import DiskGuard
from . import policy
from .candidate import allocated_unique,put
from .paths import repository
from pilot.betaintegrated01.runtime.ap_stage import canonical
MIB=2**20
class ResourceMonitor:
 def __init__(self,root,recording_seconds,campaign,*,inventory,power,guardian,now=time.monotonic_ns,wall=time.time):
  self.root=Path(root);self.seconds=policy.duration(recording_seconds);self.campaign=campaign;self.inventory=inventory;self.power=power;self.guardian=guardian;self.now=now;self.wall=wall;self.disk=DiskGuard(repository());self.lock=threading.Lock();self.done=threading.Event();self.thread=None;self.failure=None;self.entry=None;self.closure=None;self.last_observed_ns=None
 def start(self):
  if self.thread is not None:raise RuntimeError('RESOURCE_MONITOR_ONE_START')
  self.root.mkdir(parents=True,exist_ok=True);budget=policy.case_budget(shutil.disk_usage(repository()).free,self.seconds)
  if budget['admitted'] is not True:raise ValueError('ORIGINAL_WHOLE_CASE_ADMISSION')
  p=self._power(entry=True);self._caps(self.inventory());prime=self.disk.prime();self.check();self.entry={'admitted':True,'realPriming':True,'capacity':budget,'power':p,'actualPrime':prime};put(self.root/'resource-entry.json',canonical(self.entry)+b'\n');self.last_observed_ns=self.now();self.thread=threading.Thread(target=self._run,name='aeris-resource-monitor');self.thread.start();return self.entry
 def _power(self,entry=False):
  p=self.power()
  if type(p.get('AC'))is not bool or type(p.get('batteryPercent'))is not int or not 0<=p['batteryPercent']<=100:raise RuntimeError('UNKNOWN_POWER')
  if not p['AC'] and (p['batteryPercent']<30 if entry else p['batteryPercent']<=20):raise RuntimeError('POWER_ENTRY30_OR_STOP20')
  return p
 def _caps(self,v):
  caps={'metadataBytes':64*MIB,'exportBytes':192*MIB,'AVDPositiveGrowthBytes':512*MIB,'artifactBytes':4*MIB,'nativePhysicalBytes':160*MIB,'nativeLogicalBytes':512*MIB,'checkpointArchiveBytes':512*1024,'checkpointArchiveCount':8,'taskAllocatedBytes':policy.campaign_budget()['taskHardPeakBytes']}
  for key,limit in caps.items():
   if v.get(key) is None and key in ('nativePhysicalBytes','nativeLogicalBytes','checkpointArchiveBytes','checkpointArchiveCount'):
    enforced=v.get('sourceEnforcedNativeQuotas',{})
    if enforced.get(key)!=limit or type(enforced.get(key)) is not int or re.fullmatch('[a-f0-9]{64}',str(enforced.get('APKSourceSHA256'))) is None or v.get('nativeQuotaObservation')!='SOURCE_ENFORCED_UNMEASURED_ARCHIVES_NOT_HOST_PRIVATE_INVENTORY':raise RuntimeError('NATIVE_SOURCE_ENFORCED_QUOTA_DECLARATION')
    continue
   if type(v.get(key))is not int or not 0<=v[key]<=limit:raise RuntimeError('RESOURCE_CAP:'+key)
  return v
 def check(self,n=0):
  if self.failure:raise RuntimeError(self.failure)
  if self.thread is not None and (not self.thread.is_alive() and not self.done.is_set() or self.last_observed_ns is not None and self.now()-self.last_observed_ns>2_000_000_000):raise RuntimeError('RESOURCE_MONITOR_OBSERVER_STALE')
  self.campaign.check();g=self.guardian()
  if type(g.get('hostNs'))is not int or not 0<=self.now()-g['hostNs']<=2_000_000_000 or g.get('alive')is not True or g.get('closed')is not False or g.get('sourceVerified')is not True:raise RuntimeError('OWNED_GUARDIAN_ORIGINAL_SOURCE_LIVENESS')
  with self.lock:self.disk.check(n)
 def _run(self):
  last=self.now();wall=self.wall();tick=0
  try:
   with (self.root/'resource-guard.jsonl').open('x') as f:
    while not self.done.wait(.5):
     self.check();p=self._power();n=self.now();w=self.wall();gap=(w-wall)-(n-last)/1e9
     if n-last>2_000_000_000 or abs(gap)>2:raise RuntimeError('SUSPEND_OR_MONITOR_SCHEDULING_GAP')
     last=n;wall=w;self.last_observed_ns=n;tick+=1;v=self._caps(self.inventory()) if tick%10==0 else None
     row={'hostNs':n,'power':p,'wallMonoGapSeconds':gap,'freeBytes':shutil.disk_usage(repository()).free,'inventory':v,'disk':self.disk.diagnostic()};f.write(json.dumps(row)+'\n');f.flush();os.fsync(f.fileno())
  except BaseException as e:
   self.failure=type(e).__name__+':'+str(e);put(self.root/'resource-failure.json',canonical({'failure':self.failure,'hostNs':self.now(),'disk':self.disk.diagnostic()})+b'\n')
 def close(self):
  if self.closure is not None:return dict(self.closure)
  self.done.set()
  if self.thread:self.thread.join(timeout=8)
  if self.thread and self.thread.is_alive():raise RuntimeError('RESOURCE_MONITOR_DID_NOT_CLOSE')
  value={'failure':self.failure,'hostNs':self.now(),'disk':self.disk.diagnostic()};put(self.root/'resource-close.json',canonical(value)+b'\n');self.closure=dict(value);return value

def host_power():
 raw=subprocess.check_output(['pmset','-g','batt'],text=True,timeout=2);m=re.search(r'(\d+)%',raw)
 if m is None:raise RuntimeError('UNKNOWN_POWER')
 return {'raw':raw,'AC':"'AC Power'" in raw,'batteryPercent':int(m.group(1))}
