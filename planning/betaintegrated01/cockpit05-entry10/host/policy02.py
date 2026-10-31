"""Explicit host-recording-only amendment; physical provider configSHA remains pinned."""
from pathlib import Path
from importlib import import_module
import hashlib,json
from pilot.betaintegrated01.runtime.ap_stage import canonical
from pilot.betaintegrated01.cockpit04.revision02.capacity import journal_policy,transport_policy
from .admission import DISK_POLICY
from .policy import task_budget as original_task_budget
R=Path(__file__).resolve().parents[4]
H='planning.betaintegrated01.cockpit05-entry10'


def task_budget(free_bytes=None):
    return {**original_task_budget(free_bytes),
      'selectedRuntimeMigration':'WIRED_CODE_MOCK_ONLY_EXPLICIT_NEW9MODULE_IMPORTGRAPH',
      'newActualControllerResourcesFullGuardian':'NOT_IMPLEMENTED',
      'actualRuntimeLaunches':0,'actualThirtyMinuteAccepted':False}


def source_binding():
    root=R/'planning/betaintegrated01/cockpit05-entry10'
    paths=[root/'host/admission.py',root/'host/policy02.py',*sorted((root/'runtime').rglob('*.py'))]
    return {str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in paths}


def amendment():
    body={'format':'aeris-explicit-host-recording-policy-amendment','version':1,
      'scope':'HOST_RECORDING_ENTRY_RESOURCE_ONLY_PHYSICAL_PROVIDER_UNCHANGED',
      'supersedes':'run-profile02.hostDiskGuardPolicy.entryBytes20GiB_ONLY',
      'diskGuardPolicy':dict(DISK_POLICY),'runtimeModule':H+'.runtime.backend',
      'sourceSHA256':source_binding(),'fullCaseBudget':task_budget(),
      'physicalProfileConfigSHA256Unchanged':True,'typed39APModelPacerFsyncUnchanged':True}
    return {'amendment':body,'amendmentSHA256':hashlib.sha256(canonical(body)).hexdigest()}


def validate_recording_policy(config):
    if type(config)is not dict:raise ValueError('CONFIG_SCHEMA')
    provided=config.get('externalRecordingPolicy');expected=amendment()
    if type(provided)is not dict or canonical(provided)!=canonical(expected):raise ValueError('EXTERNAL_RECORDING_POLICY_EXACT_VERSION_SHA_SOURCE_REQUIRED')
    variant=config.get('controlScenario')
    if variant not in('nominal','loss'):raise ValueError('PHYSICAL_PROFILE_VARIANT')
    p=R/'pilot/betaintegrated01/cockpit04/profiles'/variant/'run-profile02.json';raw=p.read_bytes();profile=json.loads(raw)
    if config.get('expectedConfigSHA256')!=hashlib.sha256(raw).hexdigest():raise ValueError('PHYSICAL_PROFILE_CONFIG_SHA_REQUIRED')
    if config.get('referenceProfile')!=str(p.relative_to(R)):raise ValueError('PHYSICAL_PROFILE_REFERENCE_REQUIRED')
    for key,value in profile.items():
        if key=='taskBudget':continue # Old resource bucket explicitly superseded, unchanged source retained.
        if key not in config or canonical(config[key])!=canonical(value):raise ValueError('PHYSICAL_PROFILE_FIELD_CHANGED_OR_TYPED_DIFFERENT:'+key)
    if type(config.get('maximumSeconds'))is not int or config['maximumSeconds']!=1960:raise ValueError('ONE1960_RECORDING_ONLY')
    return expected


def build_config(*args,**kwargs):
    module=import_module('planning.betaintegrated01.cockpit05-soak.host.contract')
    value=module.build_config(*args,**kwargs);value['externalRecordingPolicy']=amendment();value['externalResourcePolicy']=task_budget()
    validate_recording_policy(value)
    return value
