"""Explicit product-owned allocation ledger; no arbitrary path exclusion from metadata."""
from pathlib import Path
import json,time,stat
from .candidate import allocated_unique
from . import policy
from .paths import repository
MIB=2**20
class Inventory:
 def __init__(self,evidence,planning,avd,avd_baseline,*,native=None):
  self.evidence=Path(evidence).resolve();self.planning=Path(planning).resolve();self.avd=Path(avd).resolve();self.native=native;self.baseline=json.loads(Path(avd_baseline).read_bytes())
  if self.baseline.get('format')!='aeris-runtime-avd-baseline' or type(self.baseline.get('version'))is not int or self.baseline['version']!=1 or self.baseline.get('path')!=str(self.avd) or type(self.baseline.get('allocatedBytes'))is not int or self.baseline['allocatedBytes']<0 or type(self.baseline.get('observedHostNs'))is not int or not 0<=self.baseline['observedHostNs']<=time.monotonic_ns() or self.baseline.get('growthPolicy')!='SUM_POSITIVE_PER_PATH_DEVICE_INODE_NO_CONTRACTION_OFFSET' or type(self.baseline.get('fileAllocations'))is not dict:raise ValueError('FRESH_ACTUAL_AVD_BASELINE')
  for name,row in self.baseline['fileAllocations'].items():
   if Path(name).is_absolute() or '..'in Path(name).parts or set(row)!={'device','inode','allocatedBytes'} or any(type(v)is not int or v<0 for v in row.values()):raise ValueError('AVD_PER_PATH_BASELINE_TYPE')
  if sum(x['allocatedBytes']for x in self.baseline['fileAllocations'].values())!=self.baseline['allocatedBytes']:raise ValueError('AVD_BASELINE_TOTAL')
 def __call__(self):
  registered=set()
  for receipt in (self.evidence/'attempts').glob('attempt-*-cases/case-*.json'):
   value=json.loads(receipt.read_bytes());registered.add(value['context']['run'])
  raw=set();exports=set();cases=self.evidence/'sessions'
  if cases.exists():
   for case in cases.iterdir():
    if case.is_symlink() or not case.is_dir():raise ValueError('OWNED_SESSION_ROOT_TYPE')
    if case.name not in registered:continue
    raw.update(p.resolve() for directory in (case/'raw',case/'simulation/AP-state') if directory.exists() for p in directory.rglob('*') if p.is_file())
    for filename in ('native-closed.tar','native-restart-metadata.tar'):
     path=case/filename
     if path.exists():exports.add(path.resolve())
  metadata=0;seen=set()
  for root in (self.evidence,self.planning):
   if not root.exists():continue
   for p in root.rglob('*'):
    if p.is_symlink():raise ValueError('ALLOCATION_LEDGER_SYMLINK')
    if not p.is_file() or p.resolve() in raw or p.resolve() in exports or p.is_relative_to(self.evidence/'candidates'):continue
    st=p.stat();key=(st.st_dev,st.st_ino)
    if key not in seen:seen.add(key);metadata+=st.st_blocks*512
  source_bytes=sum(allocated_unique(repository()/p) for p in ('aeris_runtime','native/mission-runtime'));metadata+=source_bytes
  current=avd_allocations(self.avd);growth=sum(max(0,row['allocatedBytes']-self.baseline['fileAllocations'][name]['allocatedBytes']) if name in self.baseline['fileAllocations'] and all(row[k]==self.baseline['fileAllocations'][name][k]for k in('device','inode')) else row['allocatedBytes'] for name,row in current.items());artifact=allocated_unique(self.evidence/'candidates') if (self.evidence/'candidates').exists() else 0
  latest=self.native.latest if self.native is not None else None;state={} if latest is None else latest.get('state',{});j=state.get('native',{}).get('journal',{});workspace=state.get('checkpoint',{})
  # Native continuously enforces exact local quotas. Cached projections are only
  # supplementary counts; strict tar/history audit independently verifies final bytes.
  return {'metadataBytes':metadata,'exportBytes':sum(p.stat().st_size for p in exports),'AVDPositiveGrowthBytes':growth,'artifactBytes':artifact,'nativePhysicalBytes':j.get('physicalSegmentBytes'),'nativeLogicalBytes':j.get('logicalBytes'),'checkpointArchiveBytes':None,'checkpointArchiveCount':None,'sourceEnforcedNativeQuotas':{'APKSourceSHA256':None if self.native is None else self.native.source,'nativePhysicalBytes':160*MIB,'nativeLogicalBytes':512*MIB,'checkpointArchiveBytes':512*1024,'checkpointArchiveCount':8},'nativeQuotaObservation':'SOURCE_ENFORCED_UNMEASURED_ARCHIVES_NOT_HOST_PRIVATE_INVENTORY','taskAllocatedBytes':allocated_unique(self.evidence)+allocated_unique(self.planning)+source_bytes+growth,'nativeQuotaEnforcement':'PACKAGED_LOCAL_NATIVE_WRITER_AND_FINAL_STRICT_EXPORT_AUDIT','cachedNativeCountersAreNotFullPrivateInventory':True,'explicitRawExclusionCount':len(raw),'explicitExportPaths':[str(x) for x in sorted(exports)]}


def avd_allocations(root):
 root=Path(root).resolve();rows={}
 for p in root.rglob('*'):
  st=p.lstat()
  if stat.S_ISLNK(st.st_mode):raise ValueError('AVD_SYMLINK_BASELINE_OR_CURRENT')
  if stat.S_ISREG(st.st_mode):rows[str(p.relative_to(root))]={'device':st.st_dev,'inode':st.st_ino,'allocatedBytes':st.st_blocks*512}
 return rows

def capture_avd_baseline(avd,output):
 from .candidate import put
 from pilot.betaintegrated01.runtime.ap_stage import canonical
 rows=avd_allocations(avd);v={'format':'aeris-runtime-avd-baseline','version':1,'path':str(Path(avd).resolve()),'observedHostNs':time.monotonic_ns(),'allocatedBytes':sum(x['allocatedBytes']for x in rows.values()),'fileAllocations':rows,'growthPolicy':'SUM_POSITIVE_PER_PATH_DEVICE_INODE_NO_CONTRACTION_OFFSET'};put(output,canonical(v)+b'\n');return v
