"""Case and aggregate quotas; exact physical provider plus external clockowner amendment."""
from pathlib import Path
from importlib import import_module
import hashlib,json
from .admission import DISK_POLICY
from pilot.betaintegrated01.runtime.ap_stage import canonical
R=Path(__file__).resolve().parents[3];GIB=2**30;MIB=2**20
H='planning.betaintegrated01.cockpit05-clockowner02'


def duration(value):
    if type(value)is not int or value not in(180,1960):raise ValueError('EXACT180_OR1960_DURATION')
    return value


def clock_events(seconds):return (duration(seconds)+15)*120+100


def clock_policy(seconds):
    j=import_module('planning.betaintegrated01.cockpit05-entry10.runtime.journal')
    return j.Policy(segment_bytes=MIB,quota_bytes=(64 if duration(seconds)==180 else 512)*MIB,max_record_bytes=2048,max_segments=544,termination_reserve_bytes=32768)


def case_budget(free_bytes=None,maximum_seconds=1960):
    seconds=duration(maximum_seconds)
    if free_bytes is not None and(type(free_bytes)is not int or not 0<=free_bytes<2**63):raise ValueError('FREE_BYTES')
    c={'hostMainJournalQuota':(384*MIB if seconds==180 else 6*GIB),'clockJournalQuota':clock_policy(seconds).quota_bytes,'APRaw':seconds*1200*10*64+10*64,'APMetadata':16*MIB,'transport':(32 if seconds==180 else 256)*MIB,'nativeAVDAllocatedGrowth':512*MIB,'globalNativeExports':192*MIB,'globalMetadata':64*MIB,'globalUnit':128*MIB}
    peak=sum(c.values());required=max(10*GIB,peak+10*GIB+256*MIB)
    return {'format':'aeris-clockowner02-case-budget','version':1,'maximumSeconds':seconds,'categories':c,'taskHardPeakBytes':peak,'requiredFreeBytes':required,'entryBytes':10*GIB,'floorBytes':10*GIB,'reserveBytes':256*MIB,'actualFreeBytes':free_bytes,'admitted':None if free_bytes is None else free_bytes>=required,'clockMaximumEventsIncludingPublicationsAndBinding':clock_events(seconds),'clockMaxRecordBytesIncludingFraming':2048,'clockWorstRecordBytes':clock_events(seconds)*2048,'conditionalQuotaCompletion':True,'hostRawCopyOrExport':False,'nativeExportCapBytes':(24 if seconds==180 else 168)*MIB,'freshAdmissionEachCase':True}


def task_budget(free_bytes=None,maximum_seconds=1960):return case_budget(free_bytes,maximum_seconds)


def campaign_budget(free_bytes=None):
    short=case_budget(maximum_seconds=180);long=case_budget(maximum_seconds=1960)
    shared=sum(long['categories'][k]for k in('nativeAVDAllocatedGrowth','globalNativeExports','globalMetadata','globalUnit'))
    peak=short['taskHardPeakBytes']+long['taskHardPeakBytes']-shared
    return {'format':'aeris-clockowner02-campaign-hard-cap','taskHardPeakBytes':peak,'globalMetadataCapBytes':64*MIB,'globalExportCapBytes':192*MIB,'globalAVDPositiveGrowthBytes':512*MIB,'nativeOriginalParts':{'short':160*MIB,'long':160*MIB,'system':192*MIB},'cases':[180,1960],'admitted':None,'freshCaseAdmissionRequired':True,'retainedShortAlreadyConsumesActualDf':True}


def source_binding():
    root=R/'planning/betaintegrated01/cockpit05-clockowner02'
    old=json.loads((R/'evidence/betaintegrated01-cockpit05-entry10-flight/host/input-contract01.json').read_bytes());paths=set(old['sourceSHA256'])
    for name,expected in old['sourceSHA256'].items():
        if hashlib.sha256((R/name).read_bytes()).hexdigest()!=expected:raise ValueError('FROZEN_SOURCE_DRIFT:'+name)
    paths.update(str(p.relative_to(R))for p in sorted(root.rglob('*.py'))if '/qa/'not in str(p)and p.name!='mock.py')
    paths.update(str(p.relative_to(R))for p in (R/'planning/betaintegrated01/cockpit05-clockdiag01').glob('*.py'))
    return {name:hashlib.sha256((R/name).read_bytes()).hexdigest()for name in sorted(paths)}


def amendment():
    value={'format':'aeris-clockowner02-recording-amendment','version':1,'diskGuardPolicy':dict(DISK_POLICY),'runtimeModule':H+'.runtime.backend','physicalProfile02ResourceLabelsSupersededOnly':True,'sourceSHA256':source_binding(),'durations':[180,1960],'clockFreshNs':250000000,'speedup':1,'capMs':500,'clockPublication':'IMMUTABLE_REFERENCE_ONLY_AFTER_FSYNC','clockQuotas':{'180':64*MIB,'1960':512*MIB}}
    return {'amendment':value,'amendmentSHA256':hashlib.sha256(canonical(value)).hexdigest()}


def build_config(repository,variant,run,epoch,boot,evidence,case_id,*,maximum_seconds=1960,wipe_state=True,state_reuse=None):
    duration(maximum_seconds)
    if variant not in('nominal','loss'):raise ValueError('PROFILE')
    p=Path(repository)/'pilot/betaintegrated01/cockpit04/profiles'/variant/'run-profile02.json';profile=json.loads(p.read_bytes())
    value={**profile,'run':run,'epoch':epoch,'boot':boot,'evidence':str(Path(evidence).resolve()),'maximumSeconds':maximum_seconds,'bind':['127.0.0.1',9012],'caseID':case_id,'wipeState':wipe_state,'expectedConfigSHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'referenceProfile':str(p.relative_to(Path(repository))),'externalRecordingPolicy':amendment(),'externalResourcePolicy':case_budget(maximum_seconds=maximum_seconds)}
    if not wipe_state:
        if state_reuse is None:raise ValueError('REBOOT_STATE_BINDING_REQUIRED')
        value['stateReuse']=state_reuse
    validate_recording_policy(value);return value


def validate_recording_policy(config):
    duration(config.get('maximumSeconds'));variant=config.get('controlScenario')
    if variant not in('nominal','loss'):raise ValueError('PROFILE')
    p=R/'pilot/betaintegrated01/cockpit04/profiles'/variant/'run-profile02.json';raw=p.read_bytes();profile=json.loads(raw)
    if config.get('expectedConfigSHA256')!=hashlib.sha256(raw).hexdigest()or config.get('referenceProfile')!=str(p.relative_to(R)):raise ValueError('PHYSICAL_PROFILE_SHA')
    for k,v in profile.items():
        if k=='taskBudget':continue
        if k not in config or canonical(config[k])!=canonical(v):raise ValueError('PHYSICAL_PROFILE_TYPED_FIELD:'+k)
    if canonical(config.get('externalRecordingPolicy'))!=canonical(amendment()):raise ValueError('EXTERNAL_RECORDING_POLICY_EXACT_SOURCE_REQUIRED')
    return amendment()


def main_policy(seconds):
    j=import_module('planning.betaintegrated01.cockpit05-entry10.runtime.journal');duration(seconds)
    return j.Policy(segment_bytes=(8 if seconds==180 else 16)*MIB,quota_bytes=384*MIB if seconds==180 else 6*GIB,max_record_bytes=2048,max_segments=64 if seconds==180 else 448,termination_reserve_bytes=16384)


def transport_policy(seconds):
    j=import_module('planning.betaintegrated01.cockpit05-entry10.runtime.journal');duration(seconds)
    return j.Policy(segment_bytes=MIB,quota_bytes=(32 if seconds==180 else 256)*MIB,max_record_bytes=16384,max_segments=40 if seconds==180 else 320,termination_reserve_bytes=32768)
