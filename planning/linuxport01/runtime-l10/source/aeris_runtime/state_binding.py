"""Fresh owned simulation AP state, flat typed identity before child dispatch."""
from pathlib import Path
from .cleanup import close_fd
import os,json,stat,hashlib
from . import policy,identity
from .paths import PACKAGE_ROOT,repository
from pilot.betaintegrated01.runtime.ap_stage import canonical,exclusive
INTERVAL_BYTES=b'0 200\n245 250\n242 1000\n'
PROBE_INTERVAL_BYTES=b'0 200\n245 250\n242 1000\n33 200\n2 1000\n'
def readonly_probe_intervals():
 raw=(PACKAGE_ROOT/'assets/readonly-probe-intervals-rc01.txt').read_bytes()
 if raw!=PROBE_INTERVAL_BYTES:raise ValueError('READONLY_PROBE_PINNED_INTERVAL_BYTES')
 return raw
def regular_bytes(path,bound):
 fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
 try:
  st=os.fstat(fd)
  if not stat.S_ISREG(st.st_mode)or st.st_nlink!=1 or st.st_size>bound:raise ValueError('STATE_FILE_TYPE_OR_BOUND')
  with os.fdopen(fd,'rb',closefd=False)as f:return f.read(bound+1)
 finally:close_fd(fd)
def observer_policy():
 path=PACKAGE_ROOT/'assets/observer-intervals.txt';raw=path.read_bytes()
 if raw!=INTERVAL_BYTES:raise ValueError('EXACT_OBSERVER_INTERVALS')
 return {'format':'aeris-runtime-observer-policy','version':1,'channel':1,'stateRelativePath':'message-intervals-chan1.txt','fileSHA256':hashlib.sha256(raw).hexdigest(),'fileBytes':len(raw),'intervalsMs':{'0':200,'245':250,'242':1000},'passiveApplicationTXBytes':0,'physical39TypedBitsChanged':False}
def readonly_probe_marker(config):
 value=config.get('readOnlyBootProbeRC01')
 if value is None:return None
 if type(value)is not dict or set(value)!={'format','version','context','priorContext','oldFaultSHA256','stateMode','oldStateUntouched','authorityRestorable','nativeActivityStarted'}or value['format']!='aeris-readonly-ap-boot-probe-rc01'or type(value['version'])is not int or value['version']!=1 or value['stateMode']!='COLD_CONFIG_NO_EEPROM_OR_MISSION_RETENTION_CLAIM'or value['oldStateUntouched']is not True or value['authorityRestorable']is not False or value['nativeActivityStarted']is not False or not __import__('re').fullmatch('[a-f0-9]{64}',value['oldFaultSHA256']):raise ValueError('READONLY_PROBE_EXACT_SOURCE_SCOPE')
 from .lifecycle import Context
 if Context(**value['context']).value()!=value['context']or Context(**value['priorContext']).value()!=value['priorContext']or any(value['context'][k]!=config[k]for k in('run','epoch','boot'))or value['context']['boot']==value['priorContext']['boot']or value['context']['run']==value['priorContext']['run']or config.get('wipeState')is not False:raise ValueError('READONLY_PROBE_DISTINCT_CONTEXT_NO_WIPE')
 return value

def validate_readonly_probe_state(config,state,raw):
 marker=readonly_probe_marker(config)
 if marker is None:raise ValueError('READONLY_PROBE_REQUIRED')
 policy.validate_recording_policy(config);native=identity.validate_native_selection(config);state=Path(state)
 if state.is_symlink()or not state.is_dir()or(state/'eeprom.bin').exists():raise ValueError('READONLY_PROBE_EXACT_FRESH_STATE_NO_RETENTION')
 owner_raw=regular_bytes(state/'.aeris-control-owner.json',4096);owner=json.loads(owner_raw);intervals=regular_bytes(state/'message-intervals-chan1.txt',4096)
 if owner!={'caseID':config['caseID'],'readOnlyBootProbeRC01':marker}or intervals!=readonly_probe_intervals() or len(list(state.glob('message-intervals-chan*.txt')))!=1:raise ValueError('READONLY_PROBE_STATE_OWNER_AND_INTERVALS')
 return {'caseID':config['caseID'],'wipeState':False,'ownerSHA256':hashlib.sha256(owner_raw).hexdigest(),'stateMode':marker['stateMode'],'passiveIntervalsSHA256':hashlib.sha256(intervals).hexdigest(),'oldStateUntouched':True,'missionRetentionProven':False,'EEPROMRetentionProven':False,'flightAuthorityGranted':False,'scope':'READONLY_NEW_CONTEXT_COLD_CONFIG_NOT_PHYSICAL_PREFLIGHT'}

def prepare_readonly_probe_state(state,config):
 marker=readonly_probe_marker(config);state=Path(state)
 if marker is None or state.exists()or state.parent.is_symlink():raise ValueError('READONLY_PROBE_FRESH_OWNED_PATH')
 state.mkdir();exclusive(state/'.aeris-control-owner.json',canonical({'caseID':config['caseID'],'readOnlyBootProbeRC01':marker})+b'\n');exclusive(state/'message-intervals-chan1.txt',readonly_probe_intervals())
 return {'path':str(state),'stateMode':marker['stateMode'],'oldStateUntouched':True,'missionRetentionProven':False,'EEPROMRetentionProven':False}

def validate_state(config,state,raw):
 if config.get('readOnlyBootProbeRC01')is not None:return validate_readonly_probe_state(config,state,raw)
 policy.validate_recording_policy(config);native=identity.validate_native_selection(config);state=Path(state);raw=Path(raw)
 if state.is_symlink()or not state.is_dir():raise ValueError('OWNED_STATE_DIRECTORY')
 if type(config.get('caseID'))is not str or not 1<=len(config['caseID'])<=64 or type(config.get('wipeState'))is not bool or config['wipeState']is not True:raise ValueError('FRESH_SIMULATION_STATE_REQUIRED')
 files=list(state.glob('message-intervals-chan*.txt'))
 if len(files)!=1 or files[0].name!='message-intervals-chan1.txt'or files[0].is_symlink():raise ValueError('ONLY_SELECTED_OBSERVER_CHANNEL')
 owner_raw=regular_bytes(state/'.aeris-control-owner.json',4096);owner=json.loads(owner_raw);intervals=regular_bytes(files[0],4096);observer=observer_policy()
 if owner.get('caseID')!=config['caseID']or intervals!=INTERVAL_BYTES or(state/'eeprom.bin').exists():raise ValueError('FRESH_STATE_BINDING')
 return {'caseID':config['caseID'],'wipeState':True,'ownerSHA256':hashlib.sha256(owner_raw).hexdigest(),'passiveIntervalsSHA256':observer['fileSHA256'],'stateMode':'FRESH_CASE_FACTORY_WIPE','externalObserverRecordingPolicy':observer,'actualHostRecordingPolicySHA256':config['externalRecordingPolicy']['amendmentSHA256'],'actualNativeClientSelectionSHA256':hashlib.sha256(canonical(native)).hexdigest(),'scope':'LOCAL_SIMULATION_NOT_PHYSICAL_GROUND'}
def prepare_fresh_case_state(state,case_id):
 state=Path(state)
 if type(case_id)is not str or not 1<=len(case_id)<=64 or state.exists()or state.parent.is_symlink():raise ValueError('FRESH_STATE_REQUIRED')
 state.mkdir();exclusive(state/'.aeris-control-owner.json',canonical({'caseID':case_id})+b'\n');exclusive(state/'message-intervals-chan1.txt',INTERVAL_BYTES)
 return {'state':str(state),'caseID':case_id,'observerPolicy':observer_policy()}
