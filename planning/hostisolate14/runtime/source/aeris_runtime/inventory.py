"""Explicit product-owned allocation ledger; no arbitrary path exclusion from metadata."""
from pathlib import Path
import json,time,stat,threading,os
from contextlib import contextmanager
from .candidate import allocated_unique,walk_allocations,allocated_artifact_union,artifact_roots
from . import policy
from .paths import repository
MIB=2**20
class Inventory:
 def __init__(self,evidence,planning,avd,avd_baseline,*,native=None,artifact_root=None,preview=False):
  self._scan_local=threading.local();self.evidence=Path(evidence).resolve();self.planning=Path(planning).resolve();self.avd=Path(avd).resolve();self.native=native;self.baselinePersisted=not isinstance(avd_baseline,dict);self.baseline=dict(avd_baseline)if isinstance(avd_baseline,dict)else json.loads(Path(avd_baseline).read_bytes())
  self.preview=preview
  if preview and(not isinstance(avd_baseline,dict)or self.evidence.exists()or self.evidence.parent!=repository()/'evidence/hostisolate14'or self.evidence.name not in('s01','s02')):raise ValueError('IPC10_PREVIEW_NO_EXISTING_SLOT')
  self.artifact_root=self.evidence/'candidates'if artifact_root is None else Path(artifact_root).resolve()
  if artifact_root is not None:
   selected=Path(os.environ.get('AERIS_CANDIDATE_DIR','')).resolve()
   if not os.environ.get('AERIS_CANDIDATE_DIR')or self.artifact_root!=selected.parent or self.artifact_root!=repository()/'evidence/hostisolate14/candidates':raise ValueError('EXACT_SELECTED_PARENT_ARTIFACT_SCOPE')
  if self.baseline.get('format')!='aeris-runtime-avd-baseline' or type(self.baseline.get('version'))is not int or self.baseline['version']!=1 or self.baseline.get('path')!=str(self.avd) or type(self.baseline.get('allocatedBytes'))is not int or self.baseline['allocatedBytes']<0 or type(self.baseline.get('observedHostNs'))is not int or not 0<=self.baseline['observedHostNs']<=time.monotonic_ns() or self.baseline.get('growthPolicy')!='SUM_POSITIVE_PER_PATH_DEVICE_INODE_NO_CONTRACTION_OFFSET' or type(self.baseline.get('fileAllocations'))is not dict:raise ValueError('FRESH_ACTUAL_AVD_BASELINE')
  for name,row in self.baseline['fileAllocations'].items():
   if Path(name).is_absolute() or '..'in Path(name).parts or set(row)!={'device','inode','allocatedBytes'} or any(type(v)is not int or v<0 for v in row.values()):raise ValueError('AVD_PER_PATH_BASELINE_TYPE')
  if sum(x['allocatedBytes']for x in self.baseline['fileAllocations'].values())!=self.baseline['allocatedBytes']:raise ValueError('AVD_BASELINE_TOTAL')
 @contextmanager
 def publication_snapshot(self,token,deadline):
  from .metadata_budget import _Publication
  if type(token)is not _Publication or type(deadline)is not int:raise ValueError('EXACT_INVENTORY_PUBLICATION_CAPABILITY')
  token.check(self,deadline);previous=getattr(self._scan_local,'context',None);self._scan_local.context=(token,deadline)
  primary=None
  try:yield
  except BaseException as error:primary=error;raise
  finally:
   try:token.check(self,deadline)
   except BaseException as secondary:
    if primary is None:raise
    primary.add_note('INVENTORY_EXIT_SECONDARY:'+type(secondary).__name__+':'+str(secondary)[:192])
   finally:self._scan_local.context=previous
 def _check_scan_deadline(self):
  context=getattr(self._scan_local,'context',None)
  if context is not None:context[0].fast_check(context[1])
 def __call__(self):
  self._check_scan_deadline();registered=set()
  for receipt in (self.evidence/'attempts').glob('attempt-*-cases/case-*.json'):
   self._check_scan_deadline();value=json.loads(receipt.read_bytes());registered.add(value['context']['run'])
  raw=set();raw_roots=set();exports=set();export_candidates=set();cases=self.evidence/'sessions'
  if cases.exists():
   for case in cases.iterdir():
    self._check_scan_deadline()
    if case.is_symlink() or not case.is_dir():raise ValueError('OWNED_SESSION_ROOT_TYPE')
    if case.name not in registered:continue
    for directory in(case/'raw',case/'simulation/AP-state'):
     if directory.is_symlink()or directory.parent.is_symlink():raise ValueError('REGISTERED_RAW_ROOT_SYMLINK')
     raw_roots.add(directory)
    for filename in ('native-closed.tar','native-restart-metadata.tar','native-original-before-quarantine.tar','product-full-raw.tar.gz'):
     path=case/filename
     export_candidates.add(path)
  # Exact original domains and independent inode sets, one fd-relative walk.
  metadata=0;seen=set();task_tree_bytes=0;artifact=0;artifact_seen=set();export_sizes={};candidate_root=str(self.artifact_root);candidate_prefix=candidate_root+os.sep
  raw_prefixes=tuple(str(path)+os.sep for path in raw_roots);export_names={str(path)for path in export_candidates}
  # Finite task prelude inputs (passive probe, gates and Root receipts) are
  # actual metadata, even though they are outside the current case's s01 tree.
  prelude=self.evidence.parent
  preludes=[]
  for p in prelude.iterdir()if prelude.exists()else[]:
   if p.name in('candidates','s01','s02'):continue
   if p.is_symlink():raise ValueError('HOSTDIAG11_PRELUDE_SYMLINK')
   if p.is_file()or p.name in('passive','qa','reports','before-hold02'):preludes.append(p)
   else:raise ValueError('HOSTDIAG11_UNDECLARED_PRELUDE_ROOT:'+p.name)
  for root in(self.evidence,self.planning,*preludes):
   if root==self.evidence and self.preview and not root.exists():continue
   tree_seen=set();root_name=str(root);evidence_tree=root==self.evidence
   def visit(name,value):
    nonlocal metadata,task_tree_bytes,artifact
    key=(value.st_dev,value.st_ino);physical=value.st_blocks*512
    if key not in tree_seen:tree_seen.add(key);task_tree_bytes+=physical
    is_candidate=name==candidate_root or name.startswith(candidate_prefix)
    if evidence_tree and is_candidate and key not in artifact_seen:artifact_seen.add(key);artifact+=physical
    if(name==root_name and stat.S_ISDIR(value.st_mode))or not stat.S_ISREG(value.st_mode):return
    if raw_prefixes and name.startswith(raw_prefixes):raw.add(name);return
    if name in export_names:exports.add(name);export_sizes[name]=value.st_size;return
    if is_candidate:return
    if key not in seen:seen.add(key);metadata+=physical
   walk_allocations(root_name,visit,deadline_check=self._check_scan_deadline,symlink_error='ALLOCATION_LEDGER_SYMLINK')
  if not self.artifact_root.is_relative_to(self.evidence):
   artifact=allocated_artifact_union(self.artifact_root,deadline_check=self._check_scan_deadline);task_tree_bytes+=artifact
  elif len(artifact_roots(self.artifact_root))>1:artifact=allocated_artifact_union(self.artifact_root,deadline_check=self._check_scan_deadline)
  source_roots=('aeris_runtime','native/mission-runtime','native/betasim-integrated01','native/betasim-application09')
  source_bytes=0;external_bytes=0
  def source_visit(name,value):
   nonlocal source_bytes,metadata
   key=(value.st_dev,value.st_ino)
   if stat.S_ISREG(value.st_mode)and key not in seen:seen.add(key);source_bytes+=value.st_blocks*512;metadata+=value.st_blocks*512
  for name in source_roots:
   walk_allocations(repository()/name,source_visit,deadline_check=self._check_scan_deadline,symlink_error='IPC10_SOURCE_ALIAS')
  from .input_roles10 import inputs
  for row in inputs(verify_hashes=True,deadline_check=self._check_scan_deadline):
   path=repository()/row['path'];value=path.lstat();key=(value.st_dev,value.st_ino)
   if key in seen:continue
   seen.add(key)
   if row['role']=='METADATA_SOURCE_TEXT':source_bytes+=value.st_blocks*512;metadata+=value.st_blocks*512
   else:external_bytes+=value.st_blocks*512
  current=avd_allocations(self.avd,deadline_check=self._check_scan_deadline);growth=sum(max(0,row['allocatedBytes']-self.baseline['fileAllocations'][name]['allocatedBytes'])if name in self.baseline['fileAllocations']and all(row[k]==self.baseline['fileAllocations'][name][k]for k in('device','inode'))else row['allocatedBytes']for name,row in current.items())
  latest=self.native.latest if self.native is not None else None;state={}if latest is None else latest.get('state',{});j=state.get('native',{}).get('journal',{});workspace=state.get('checkpoint',{})
  product=latest is not None and latest.get('format')=='aeris-betasim-native-status'
  product_inventory={}if not product else latest.get('inventory',{})
  complete_product=product and product_inventory.get('scope')=='PRIVATE_FILES_ONLY_NOT_WHOLE_APP_DATA_DIR'
  physical=j.get('physicalSegmentBytes');logical=j.get('logicalBytes');archives=None;archive_count=None
  if product:
   # The new provider has no legacy M1 quota writer. Only genuinely observed
   # managed-files superset is a quota fact. It never represents whole-app data.
   physical=product_inventory.get('allocatedBytes')+32768 if complete_product and type(product_inventory.get('allocatedBytes'))is int else None
   logical=product_inventory.get('logicalBytes')+16384 if complete_product and type(product_inventory.get('logicalBytes'))is int else None
   archives=product_inventory.get('checkpointArchiveBytes')if complete_product else None
   archive_count=product_inventory.get('checkpointArchiveCount')if complete_product else None
   retained=getattr(self.native,'retained_inventory',None)
   if retained is not None:
    if retained.get('format')!='aeris-retained-old-application-private-inventory'or retained.get('package')!='vn.rtr.aeris.mission'or any(type(retained.get(k))is not int or retained[k]<0 for k in('allocatedBytes','plaintextFileLengthBytes')):raise ValueError('RETAINED_OLD_APPLICATION_INVENTORY_UNKNOWN')
    physical=None if physical is None else physical+retained['allocatedBytes'];logical=None if logical is None else logical+retained['plaintextFileLengthBytes']
  self._check_scan_deadline()
  return {'metadataBytes':metadata,'exportBytes':sum(export_sizes.values()),'AVDPositiveGrowthBytes':growth,'artifactBytes':artifact,'nativePhysicalBytes':physical,'nativeLogicalBytes':logical,'checkpointArchiveBytes':archives,'checkpointArchiveCount':archive_count,'sourceEnforcedNativeQuotas':{}if product else{'APKSourceSHA256':None if self.native is None else self.native.source,'nativePhysicalBytes':160*MIB,'nativeLogicalBytes':512*MIB,'checkpointArchiveBytes':512*1024,'checkpointArchiveCount':8},'nativeQuotaObservation':'PRODUCT_PRIVATE_FILES_SUPERSET_OF_NATIVE_JOURNALS_NOT_WHOLE_APP_WITH_OWN_SNAPSHOT_RESERVE'if complete_product else'PRODUCT_PARTIAL_COUNTERS_NOT_FULL_QUOTA_FACTS'if product else'SOURCE_ENFORCED_UNMEASURED_ARCHIVES_NOT_HOST_PRIVATE_INVENTORY','taskAllocatedBytes':task_tree_bytes+source_bytes+external_bytes+growth,'externalReadOnlyInputAllocatedBytes':external_bytes,'externalInputRoleTable':'SOURCE_HELD_EXACT152_ORIGINAL_INPUTS_IPC10','historicalBetasimPlanningNotActiveWriter':True,'nativeQuotaEnforcement':'NEW_PLAINTEXT_PROVIDER_OBSERVED_PRIVATE_FILES_UPPER_BOUND_AND_STRICT_EXPORT'if product else'PACKAGED_LOCAL_NATIVE_WRITER_AND_FINAL_STRICT_EXPORT_AUDIT','nativePhysicalDomain':'PRIVATE_FILES_ALLOCATED_SUPERSET_NOT_WHOLE_APP'if product else'CURRENT_NATIVE_JOURNAL_SEGMENTS','nativeLogicalDomain':'ACTIVE_NEW_PROVIDER_PLAINTEXT_LOGICAL_UPPER_BOUND_NOT_LEGACY_DECODED'if product else'CURRENT_NATIVE_JOURNAL_DECODED_LOGICAL','historicalCompact10Logical':'NOT_REMEASURED_UNCHANGED_HISTORICAL_EVIDENCE'if product else'CURRENT_JOURNAL_ONLY','cachedNativeCountersAreNotFullPrivateInventory':True,'artifactScope':str(self.artifact_root),'allCurrentInputArtifactsCounted':True,'explicitRawExclusionCount':len(raw),'explicitExportPaths':[str(x)for x in sorted(exports)]}



def avd_allocations(root,*,deadline_check=None):
 root=str(Path(root).resolve());prefix=root+os.sep;rows={}
 def visit(name,value):
  if name!=root and stat.S_ISREG(value.st_mode):rows[name[len(prefix):]]={'device':value.st_dev,'inode':value.st_ino,'allocatedBytes':value.st_blocks*512}
 walk_allocations(root,visit,deadline_check=deadline_check,symlink_error='AVD_SYMLINK_BASELINE_OR_CURRENT')
 return rows

def capture_avd_baseline(avd,output,*,budget=None,evidence=None,planning=None,artifact_root=None):
 from .candidate import put
 from pilot.betaintegrated01.runtime.ap_stage import canonical
 rows=avd_allocations(avd);v={'format':'aeris-runtime-avd-baseline','version':1,'path':str(Path(avd).resolve()),'observedHostNs':time.monotonic_ns(),'allocatedBytes':sum(x['allocatedBytes']for x in rows.values()),'fileAllocations':rows,'growthPolicy':'SUM_POSITIVE_PER_PATH_DEVICE_INODE_NO_CONTRACTION_OFFSET'};raw=canonical(v)+b'\n'
 if len(raw)>131072:raise ValueError('BOOTSTRAP_AVD_BASELINE128KiB')
 if budget is not None:budget.write('campaign',output,raw)
 else:
  import shutil
  from .metadata_budget import CAP,LEDGER
  output=Path(output).absolute()
  if evidence is None or planning is None or output!=Path(evidence).absolute()/'avd-baseline.json'or not Path(evidence).is_dir()or any(p.is_symlink()for p in[output,*output.parents]):raise ValueError('FIXED_BOOTSTRAP_BASELINE_PATH')
  current=Inventory(evidence,planning,avd,v,artifact_root=artifact_root)();charge=((len(raw)+4095)//4096)*4096+8192
  if current['metadataBytes']+charge+LEDGER>CAP or shutil.disk_usage(evidence).free-charge<10*2**30+256*MIB:raise ValueError('BOUNDED_BOOTSTRAP_BASELINE_ADMISSION')
  put(output,raw)
 return v
