"""Versioned campaign closure for clock-owner02; no process/device activity on import."""
from pathlib import Path
from importlib import import_module
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
OLD=import_module('planning.betaintegrated01.cockpit05-entry10.full.contract')
PACKAGE=OLD.PACKAGE;ACTIVITY=OLD.ACTIVITY;APK_SHA256=OLD.APK_SHA256;SOURCE_SHA256=OLD.SOURCE_SHA256
BUILD=OLD.BUILD;PROVIDERS=OLD.PROVIDERS
EVIDENCE='evidence/betaintegrated01-cockpit05-clockflight02'
RUNTIME='planning.betaintegrated01.cockpit05-clockowner02.runtime.backend'
POLICY='planning.betaintegrated01.cockpit05-clockowner02.policy'
NAMESPACE='planning.betaintegrated01.cockpit05-clockflight02'
BASELINE_RECEIPT='evidence/betaintegrated01-cockpit05-entry10-flight/actual-combined01/control/restart-recovery-supplement01.json'
CASES={'short':{'directory':'actual-short01','run':'cockpit05-clockflight02-short-01','maximumSeconds':180,'holdSeconds':5},'long':{'directory':'actual-combined01','run':'cockpit05-clockflight02-combined-01','maximumSeconds':1960,'holdSeconds':1802}}

def sha(path):return OLD.sha(path)
def policy():return import_module(POLICY)
def task_budget(free_bytes=None):return policy().task_budget(free_bytes)
def case_budget(free_bytes=None,maximum_seconds=1960):return policy().case_budget(free_bytes,maximum_seconds=maximum_seconds)
def campaign_budget(free_bytes=None):return policy().campaign_budget(free_bytes)
def build_config(*args,**kwargs):return policy().build_config(*args,**kwargs)
def expected_context(*args,**kwargs):return OLD.expected_context(*args,**kwargs)
def build_input_contract(repository=ROOT):
 value=OLD.build_input_contract(repository);value['metadataSHA256'][BASELINE_RECEIPT]=sha(Path(repository)/BASELINE_RECEIPT)
 return {**value,'format':'aeris-clockflight02-input-closure','newEvidenceRoot':EVIDENCE,'runtimeEntryModule':RUNTIME,'priorDraftRevisions':[1,2,3,4,5,6],'newActualDraftRevision':None,'baselinePolicy':'EXACT_CURRENT_R6_ALL_HISTORY_NO_SEED_CLEAR_OR_NEW_DRAFT','newCasePolicies':CASES,'capacity':task_budget(),'actualThirtyMinuteAccepted':False}
def selected_sources():
 return {str(p.relative_to(ROOT)):sha(p)for p in sorted((ROOT/'planning/betaintegrated01/cockpit05-clockflight02').rglob('*.py'))if '__pycache__'not in p.parts}
def make_manifest():
 p=policy();v=build_input_contract();v['sourceSHA256'].update(selected_sources());v['sourceSHA256'].update(p.source_binding());v['externalRecordingPolicy']=p.amendment();return v
def verify_full_inputs():
 v=json.loads((ROOT/EVIDENCE/'host/input-contract01.json').read_text())
 if v.get('runtimeEntryModule')!=RUNTIME:raise ValueError('NEW_CLOCK_OWNER_RUNTIME_REQUIRED')
 for name,h in {**v['sourceSHA256'],**v['metadataSHA256']}.items():
  if sha(ROOT/name)!=h:raise ValueError('SELECTED_SOURCE_DRIFT:'+name)
 if v['externalRecordingPolicy']!=policy().amendment():raise ValueError('EXTERNAL_RECORDING_POLICY_DRIFT')
 return v
if __name__=='__main__':
 target=ROOT/EVIDENCE/'host/input-contract01.json';target.parent.mkdir(parents=True,exist_ok=True)
 with target.open('x')as f:json.dump(make_manifest(),f,indent=2);f.write('\n')
 print(json.dumps({'path':str(target),'sha256':sha(target),'actualLaunches':0}))
