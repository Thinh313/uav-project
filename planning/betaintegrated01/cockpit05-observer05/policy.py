"""Explicit observation-only startup cadence overlay. No physical/provider rewrites."""
from pathlib import Path
from importlib import import_module
import hashlib,json,re
from pilot.betaintegrated01.runtime.ap_stage import canonical
R=Path(__file__).resolve().parents[3];H='planning.betaintegrated01.cockpit05-observer05'
OLD=import_module('planning.betaintegrated01.cockpit05-clockowner02.policy')
INTERVAL_PATH='planning/betaintegrated01/cockpit05-observer05/config/message-intervals-chan1.txt';PROOF_PATH='planning/betaintegrated01/cockpit05-observer05/config/feature-proof01.json';INTERVAL_BYTES=b'0 200\n245 250\n242 1000\n';OBSERVER_RESERVE=2**20

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def source_binding():
 v=dict(OLD.source_binding())
 for name in('policy.py','state_binding.py','ap_supervisor.py','cold.py'):
  p=Path(__file__).parent/name;v[str(p.relative_to(R))]=sha(p)
 for n in(INTERVAL_PATH,PROOF_PATH):v[n]=sha(R/n)
 return v

def feature_proof():
 p=R/PROOF_PATH;v=json.loads(p.read_bytes());assert v['APSHA256']==sha(R/v['APBinary'])
 binary=(R/v['APBinary']).read_bytes()
 for s in v['exactArtifactContainsSymbolsAndPath']:
  if s.encode()not in binary:raise ValueError('AP_INTERVALS_FEATURE_NOT_PRESENT')
 for n,h in v['sourceSHA256'].items():
  if sha(R/n)!=h:raise ValueError('CACHED_AP_FEATURE_SOURCE_DRIFT')
 return v

def amendment():
 if (R/INTERVAL_PATH).read_bytes()!=INTERVAL_BYTES:raise ValueError('INTERVAL_SOURCE_BYTES')
 v={'format':'aeris-external-observer-recording-policy','version':1,'channel':1,'serialEndpoint':'tcp:5762:nowait','stateRelativePath':'message-intervals-chan1.txt','sourceRelativePath':INTERVAL_PATH,'fileSHA256':sha(R/INTERVAL_PATH),'fileBytes':len(INTERVAL_BYTES),'intervalsMs':{'0':200,'245':250,'242':1000},'APSHA256':feature_proof()['APSHA256'],'featureProofPath':PROOF_PATH,'featureProofSHA256':sha(R/PROOF_PATH),'supersedes':'ONLY_FROZEN_PROFILE_PASSIVE_INTERVAL_STATE_FILE_BINDING_NOT_PHYSICAL_PARAMETERS','physical39TypedBitsChanged':False,'passiveApplicationTXBytes':0,'freshnessGeographyNs':1500000000,'freshnessFrameNs':250000000,'freshnessNativeNs':200000000,'pacerCapMs':500,'requestedSpeedup':1,'cadenceNotPerformanceRootCauseRepair':True}
 return {'amendment':v,'amendmentSHA256':hashlib.sha256(canonical(v)).hexdigest()}

def validate_observer_policy(config):
 OLD.validate_recording_policy(config)
 if canonical(config.get('externalObserverRecordingPolicy'))!=canonical(amendment()):raise ValueError('OBSERVER_EXACT_EXTERNAL_AMENDMENT_REQUIRED')
 return amendment()

def build_config(*a,**kw):
 v=OLD.build_config(*a,**kw);v['externalObserverRecordingPolicy']=amendment();validate_observer_policy(v);return v

def case_budget(free_bytes=None,maximum_seconds=1960):
 v=OLD.case_budget(free_bytes,maximum_seconds);v['categories']['observerStateAndHelpersReserve']=OBSERVER_RESERVE;v['taskHardPeakBytes']+=OBSERVER_RESERVE;v['requiredFreeBytes']+=OBSERVER_RESERVE;v['admitted']=None if free_bytes is None else free_bytes>=v['requiredFreeBytes'];return v

def task_budget(free_bytes=None,maximum_seconds=1960):return case_budget(free_bytes,maximum_seconds)
def campaign_budget(free_bytes=None):
 v=OLD.campaign_budget(free_bytes);v['taskHardPeakBytes']+=OBSERVER_RESERVE;v['observerStateAndHelpersReserve']=OBSERVER_RESERVE;return v
