"""One flat typed policy. No historical runtime policy or contract inheritance."""
from pathlib import Path
import hashlib,json
from .paths import PACKAGE_ROOT,repository
from .dependencies import LEAVES
from pilot.betaintegrated01.runtime.ap_stage import canonical
_POLICY_PATH=PACKAGE_ROOT/'assets/resource-policy.json'
_DATA=json.loads(_POLICY_PATH.read_bytes())
DISK_POLICY=_DATA['diskGuardPolicy'];MIB=2**20;GIB=2**30
def duration(n):
 if type(n)is not int or n not in(180,1960):raise ValueError('EXACT180_OR1960_DURATION')
 return n
def _journal(kind,n):
 from .foundation.journal_base import Policy
 return Policy(**_DATA['cases'][str(duration(n))][kind])
def main_policy(n):return _journal('mainJournal',n)
def clock_policy(n):return _journal('clockJournal',n)
def transport_policy(n):return _journal('transportJournal',n)
def clock_events(n):return _DATA['cases'][str(duration(n))]['clockEvents']
def case_budget(free_bytes=None,maximum_seconds=1960):
 if free_bytes is not None and(type(free_bytes)is not int or not 0<=free_bytes<2**63):raise ValueError('TYPED_FREE_BYTES')
 v=json.loads(json.dumps(_DATA['cases'][str(duration(maximum_seconds))]['budget']));v['actualFreeBytes']=free_bytes;v['admitted']=None if free_bytes is None else free_bytes>=v['requiredFreeBytes'];v['policyOrigin']='FLAT_PRODUCT_RUNTIME_SAME_ACCEPTED_NUMERIC_BOUNDS';return v
task_budget=case_budget
def campaign_budget(free_bytes=None):
 v=json.loads(json.dumps(_DATA['campaign']));v['actualFreeBytes']=free_bytes;v['admitted']=None if free_bytes is None else free_bytes>=v['taskHardPeakBytes']+10*GIB+256*MIB;return v
def source_binding():
 files=[p for p in PACKAGE_ROOT.rglob('*') if p.is_file() and p.suffix in ('.py','.json','.txt') and '__pycache__' not in p.parts]
 selected={str(Path('aeris_runtime')/p.relative_to(PACKAGE_ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
 selected.update({name:hashlib.sha256((repository()/name).read_bytes()).hexdigest() for name in LEAVES})
 return selected
def amendment():
 body={'format':'aeris-runtime-recording-policy','version':1,'sourceSHA256':source_binding(),'diskGuardPolicy':DISK_POLICY,'clockFreshNs':250000000,'inputFreshNs':200000000,'loopMs':500,'geographyFreshNs':1500000000,'speedup':1,'capMs':500,'durations':[180,1960],'clockPublication':'PER_DURABLE_MATCHED_RESPONSE_IMMUTABLE_AFTER_FSYNC','receiveBudget8':8,'nativeAuthorityOwner':'NATIVE_CONTROL_OWNER_ONLY','scope':'SIMULATION_PROCESS_LIFECYCLE_NOT_PHYSICAL_AUTOPILOT_SHUTDOWN'}
 return {'amendment':body,'amendmentSHA256':hashlib.sha256(canonical(body)).hexdigest()}
def profile_path(variant):
 if variant not in('nominal','loss'):raise ValueError('PROFILE')
 return repository()/'pilot/betaintegrated01/cockpit04/profiles'/variant/'run-profile02.json'
def validate_recording_policy(config):
 duration(config.get('maximumSeconds'));path=profile_path(config.get('controlScenario'));raw=path.read_bytes();profile=json.loads(raw)
 if config.get('expectedConfigSHA256')!=hashlib.sha256(raw).hexdigest()or config.get('referenceProfile')!=str(path.relative_to(repository())):raise ValueError('PHYSICAL_PROFILE_SHA')
 for k,v in profile.items():
  if k=='taskBudget':continue
  if k not in config or canonical(config[k])!=canonical(v):raise ValueError('PHYSICAL_PROFILE_TYPED_FIELD:'+k)
 if canonical(config.get('externalResourcePolicy'))!=canonical(case_budget(maximum_seconds=config['maximumSeconds'])):raise ValueError('EXACT_FLAT_RESOURCE_BUDGET')
 if canonical(config.get('externalRecordingPolicy'))!=canonical(amendment()):raise ValueError('EXACT_FLAT_RUNTIME_SOURCE_POLICY')
 return amendment()
def build_config(variant,run,epoch,boot,evidence,case_id,*,maximum_seconds=1960):
 path=profile_path(variant);raw=path.read_bytes();profile=json.loads(raw);v={**profile,'run':run,'epoch':epoch,'boot':boot,'evidence':str(Path(evidence).resolve()),'maximumSeconds':duration(maximum_seconds),'bind':['127.0.0.1',9012],'caseID':case_id,'wipeState':True,'expectedConfigSHA256':hashlib.sha256(raw).hexdigest(),'referenceProfile':str(path.relative_to(repository())),'externalRecordingPolicy':amendment(),'externalResourcePolicy':case_budget(maximum_seconds=maximum_seconds)};validate_recording_policy(v);return v
