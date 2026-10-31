"""Read-only startup-overlay binding, additional to unchanged full raw/flight oracles."""
from pathlib import Path
import json,hashlib
from .policy import validate_observer_policy,INTERVAL_BYTES
from .state_binding import regular_bytes

def verify_observer_capture(out,state,config):
 out=Path(out);state=Path(state)
 files=list(state.glob('message-intervals-chan*.txt'))
 if len(files)!=1 or files[0].name!='message-intervals-chan1.txt' or files[0].is_symlink():raise ValueError('OBSERVER_UNDECLARED_CHANNEL_FILE')
 overlay=validate_observer_policy(config)
 from importlib import import_module
 from pilot.betaintegrated01.runtime.ap_stage import canonical
 native=import_module('planning.betaintegrated01.cockpit05-metaval15.native_identity').validate_native_selection(config)
 launch=json.loads(regular_bytes(out/'ap-supervisor-launch.json',16384));binding=launch['stateBinding']
 if any(launch.get(k)!=config[k]for k in('run','epoch','boot','APSHA256','parameterSHA256')):raise ValueError('OBSERVER_AP_LAUNCH_CONTEXT')
 if binding.get('externalObserverRecordingPolicy')!=overlay or binding.get('passiveIntervalsSHA256')!=overlay['amendment']['fileSHA256']or binding.get('caseID')!=config['caseID']or binding.get('wipeState')is not config['wipeState']:raise ValueError('OBSERVER_LAUNCH_BINDING')
 if binding.get('actualHostRecordingPolicySHA256')!=config['externalRecordingPolicy']['amendmentSHA256']or binding.get('actualNativeClientSelectionSHA256')!=hashlib.sha256(canonical(native)).hexdigest():raise ValueError('METAVAL15_ACTUAL_HOST_AND_CLIENT_BINDING')
 if binding.get('frozenProfilePassiveIntervalsSHA256NotSelectedForThisOverlay')!=config['passiveIntervalsSHA256']:raise ValueError('OBSERVER_EXPLICIT_SUPERSESSION')
 raw=regular_bytes(state/'message-intervals-chan1.txt',4096);owner=regular_bytes(state/'.aeris-control-owner.json',4096)
 if raw!=INTERVAL_BYTES or hashlib.sha256(raw).hexdigest()!=binding['passiveIntervalsSHA256']or hashlib.sha256(owner).hexdigest()!=binding['ownerSHA256']or json.loads(owner).get('caseID')!=config['caseID']:raise ValueError('OBSERVER_CURRENT_STATE_FILE_BINDING')
 command=launch.get('command');serial=['--serial0=tcp:5760:nowait','--serial1=tcp:5762:nowait','--serial2=tcp:5763:nowait']
 if type(command)is not list or any(command.count(v)!=1 for v in serial)or command.count('--speedup')!=1 or command[command.index('--speedup')+1]!='1':raise ValueError('OBSERVER_CHANNEL_COMMAND_MAPPING')
 return {'status':'OBSERVER_STARTUP_FILE_CONTEXT_SOURCE_BOUND_NOT_ACTUAL_CADENCE_ACCEPTANCE','overlay':overlay,'fileSHA256':binding['passiveIntervalsSHA256'],'passiveApplicationTXBytesPolicy':0,'actualCRCHeartbeatCadenceAndAllFreshnessChecksRequired':True,'currentFailedE04Promoted':False,'performanceCauseResolved':False}
