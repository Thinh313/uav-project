"""Explicit Observer11 host-policy inheritance; actual config always retains the new top policy."""
from pathlib import Path
from importlib import import_module
import hashlib
from pilot.betaintegrated01.runtime.ap_stage import canonical
PARENT=import_module('planning.betaintegrated01.cockpit05-compact10.runtime.policy')
CADENCE=import_module('planning.betaintegrated01.cockpit05-observer05.policy')
R=Path(__file__).resolve().parents[4]
H='planning.betaintegrated01.cockpit05-observer11'
PARENT_SHA256='ddb5bec06a511c9164d757ea01971d9b5820e5a73a7706dc21babdc29a5ea8e3'
duration=PARENT.duration;main_policy=PARENT.main_policy;clock_policy=PARENT.clock_policy;transport_policy=PARENT.transport_policy
case_budget=PARENT.case_budget;task_budget=PARENT.task_budget;campaign_budget=PARENT.campaign_budget

def source_binding():
    value=dict(PARENT.source_binding())
    if len(value)!=198:raise ValueError('OBSERVER11_EXACT198_PARENT_SOURCE_CLOSURE')
    root=Path(__file__).parent.parent
    for relative in ('runtime/backend.py','runtime/policy.py','adapter/policy.py','adapter/state_binding.py','adapter/ap_supervisor.py','adapter/cold.py'):
        path=root/relative
        value[str(path.relative_to(R))]=hashlib.sha256(path.read_bytes()).hexdigest()
    if len(value)!=204:raise ValueError('OBSERVER11_EXACT204_SOURCE_CLOSURE')
    return dict(sorted(value.items()))

def amendment():
    parent=PARENT.amendment()
    if parent['amendmentSHA256']!=PARENT_SHA256:raise ValueError('OBSERVER11_FROZEN_COMPACT10_PARENT_AMENDMENT')
    cadence=CADENCE.amendment()
    adapter_path=Path(__file__).parent.parent/'adapter/policy.py'
    value={'format':'aeris-observer11-host-recording-amendment','version':1,
           'parentAmendmentSHA256':PARENT_SHA256,'sourceSHA256':source_binding(),
           'runtimeModule':H+'.runtime.backend',
           'observerValidatorEntry':H+'.adapter.policy.validate_observer_policy',
           'observerValidatorSourceSHA256':hashlib.sha256(adapter_path.read_bytes()).hexdigest(),
           'inheritedObserverCadenceAmendmentSHA256':cadence['amendmentSHA256'],
           'parentValidation':'DECLARED_INHERITANCE_COPY_ONLY_ACTUAL_CONFIG_RETAINS_THIS_TOP_POLICY',
           'startupIdleGuard':'EXISTING_50MS_SOCKET_TIMEOUT_CALLS_SAME_REAL_PRIMED_MAIN_JOURNAL_GUARD_NO_RESET',
           'diskGuardPolicy':PARENT.BASE.DISK_POLICY,'clockFreshNs':250000000,'speedup':1,'capMs':500,
           'durations':[180,1960],'physical39TypedBitsChanged':False,'nativeAPKChanged':False}
    return {'amendment':value,'amendmentSHA256':hashlib.sha256(canonical(value)).hexdigest()}

def validate_recording_policy(config):
    selected=amendment()
    if canonical(config.get('externalRecordingPolicy'))!=canonical(selected):raise ValueError('OBSERVER11_ACTUAL_TOP_POLICY_REQUIRED')
    inherited=dict(config)
    inherited['externalRecordingPolicy']=PARENT.amendment()
    PARENT.validate_recording_policy(inherited)
    return selected

def build_config(*args,**kwargs):
    value=PARENT.build_config(*args,**kwargs)
    value['externalRecordingPolicy']=amendment()
    validate_recording_policy(value)
    return value
