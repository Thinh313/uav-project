"""Actual METAVAL15 host source; ClockTerm14 remains immutable ancestry and selected clock implementation."""
from pathlib import Path
from importlib import import_module
import hashlib
from pilot.betaintegrated01.runtime.ap_stage import canonical
PARENT=import_module('planning.betaintegrated01.cockpit05-clockterm14.runtime.policy')
R=Path(__file__).resolve().parents[4];H='planning.betaintegrated01.cockpit05-metaval15';PARENT_SHA256='615fcf240bdaf128e60a4fc75c9fa317340997801d4e24594f4b56f9751c1400'
duration=PARENT.duration;main_policy=PARENT.main_policy;clock_policy=PARENT.clock_policy;transport_policy=PARENT.transport_policy
case_budget=PARENT.case_budget;task_budget=PARENT.task_budget;campaign_budget=PARENT.campaign_budget
SELECTED=('native_identity.py','runtime/backend.py','runtime/policy.py','adapter/policy.py','adapter/state_binding.py','adapter/ap_supervisor.py','adapter/cold.py','flight/contract.py')
def source_binding():
 value=dict(PARENT.source_binding())
 if len(value)!=214:raise ValueError('METAVAL15_EXACT214_PARENT_ANCESTRY')
 root=Path(__file__).parent.parent
 for relative in SELECTED:
  p=root/relative;value[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
 return dict(sorted(value.items()))
def amendment():
 if PARENT.amendment()['amendmentSHA256']!=PARENT_SHA256:raise ValueError('METAVAL15_FROZEN_CLOCKTERM14_PARENT')
 v=dict(format='aeris-metaval15-host-recording-amendment',version=1,parentAmendmentSHA256=PARENT_SHA256,parentExecutableAncestryFiles=214,sourceSHA256=source_binding(),runtimeModule=H+'.runtime.backend',observerValidatorEntry=H+'.adapter.policy.validate_observer_policy',clockOwnerModule='planning.betaintegrated01.cockpit05-clockterm14.runtime.owner',clockSocketModule='planning.betaintegrated01.cockpit05-clockterm14.runtime.clock_socket',metadataIdentityModule=H+'.native_identity',reusedNativeClient='EXACT_CLOCKTERM14_APK45_AND_THREE_PROTOCOLS_NO_REBUILD',clockDelivery='EVERY_POLL_DRAIN8_AND_EACH_DURABLE_MATCHED_RESPONSE_PUBLISHED_BEFORE_UNRELATED_IO',parentValidation='DECLARED_INHERITANCE_COPY_ONLY_ACTUAL_CONFIG_RETAINS_THIS_TOP_POLICY',diskGuardPolicy=PARENT.amendment()['amendment']['diskGuardPolicy'],clockFreshNs=250000000,speedup=1,capMs=500,durations=[180,1960],requestPeriodNs=100000000,receiveBudgetPerPoll=8,maxPending=8,recentCorrelator=64,publicationHistory=8,uncertaintyPolicy='EXACT_FROZEN_CORRELATOR_NO_NEW_PRECISION_OR_NUMERIC_GATE',diagnosticBytes=32768,physical39TypedBitsChanged=False,nativeSelection='SEPARATE_EXACT_METAVAL15_CLIENT_OVERLAY_NOT_HISTORICAL_NATIVE_APK_LABEL')
 return dict(amendment=v,amendmentSHA256=hashlib.sha256(canonical(v)).hexdigest())
def validate_recording_policy(config):
 selected=amendment()
 if canonical(config.get('externalRecordingPolicy'))!=canonical(selected):raise ValueError('METAVAL15_ACTUAL_TOP_POLICY_REQUIRED')
 inherited=dict(config);inherited['externalRecordingPolicy']=PARENT.amendment();PARENT.validate_recording_policy(inherited);return selected
def build_config(*a,**kw):
 v=PARENT.build_config(*a,**kw);v['externalRecordingPolicy']=amendment();validate_recording_policy(v);return v
