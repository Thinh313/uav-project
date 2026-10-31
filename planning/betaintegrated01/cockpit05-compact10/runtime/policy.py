"""Explicit host prepare-once/profiling amendment; physical AP/model/profile unchanged."""
from pathlib import Path
from importlib import import_module
import hashlib,json
from pilot.betaintegrated01.runtime.ap_stage import canonical
BASE=import_module('planning.betaintegrated01.cockpit05-clockowner02.policy')
OBS=import_module('planning.betaintegrated01.cockpit05-observer05.policy')
R=Path(__file__).resolve().parents[4];H='planning.betaintegrated01.cockpit05-compact10.runtime'
duration=BASE.duration;main_policy=BASE.main_policy;clock_policy=BASE.clock_policy;transport_policy=BASE.transport_policy;case_budget=OBS.case_budget;task_budget=OBS.case_budget;campaign_budget=OBS.campaign_budget

def source_binding():
 v=BASE.source_binding()
 for name in ('profile.py','journal.py','frame_adapter.py','backend.py','policy.py'):
  p=Path(__file__).parent/name;v[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
 return dict(sorted(v.items()))
def amendment():
 value=dict(format='aeris-compact10-host-recording-amendment',version=1,parentAmendmentSHA256=BASE.amendment()['amendmentSHA256'],sourceSHA256=source_binding(),runtimeModule=H+'.backend',diskGuardPolicy=BASE.DISK_POLICY,clockFreshNs=250000000,speedup=1,capMs=500,durations=[180,1960],hostJournalPhysicalAndLogicalBytes='EXACT_ORIGINAL_V2_PREPARE_CANONICAL_BODY_ONCE',profile='WRITE_FSYNC_ALL_REUSE_DIAGNOSTICIO_CLOCKS_OTHER_PHASE_METRICS_FIRST_EVERY16_COUNT_ALL_AFTER_CLOSE_ONLY',profileMetadataMaximumBytes=131072)
 return dict(amendment=value,amendmentSHA256=hashlib.sha256(canonical(value)).hexdigest())
def build_config(*args,**kwargs):
 c=OBS.build_config(*args,**kwargs);c['externalRecordingPolicy']=amendment();validate_recording_policy(c);return c
def validate_recording_policy(config):
 if canonical(config.get('externalRecordingPolicy'))!=canonical(amendment()):raise ValueError('COMPACT10_HOST_SOURCE_AMENDMENT_REQUIRED')
 copy=dict(config);copy['externalRecordingPolicy']=BASE.amendment();BASE.validate_recording_policy(copy);return amendment()
