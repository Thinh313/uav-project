"""Isolated NativeIO04 package plus frozen clockowner02 physical/runtime closure."""
from pathlib import Path
from importlib import import_module
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[4]
OLD=import_module('planning.betaintegrated01.cockpit05-nativeio04.flight.contract')
PACKAGE='vn.rtr.aeris.cockpitio04';ACTIVITY=PACKAGE+'/.CockpitActivity'
BUILD='evidence/betaintegrated01-cockpit05-nativeio04/native/build-01.json'
PROVIDERS=OLD.PROVIDERS;EVIDENCE='evidence/betaintegrated01-cockpit05-observer05';NAMESPACE='planning.betaintegrated01.cockpit05-observer05.flight'
RUNTIME=OLD.RUNTIME;POLICY=OLD.POLICY
OBSERVER='planning.betaintegrated01.cockpit05-observer05'
OLD_PACKAGE='vn.rtr.aeris.cockpit05';BASELINE_RECEIPT=OLD.BASELINE_RECEIPT
CURRENT_BASELINE_RECEIPT='evidence/betaintegrated01-cockpit05-nativeio04/root-closeout01/device-final.json'
CASES={'short':{'directory':'actual-short01','run':'cockpit05-observer05-short-01','maximumSeconds':180,'holdSeconds':5},'long':{'directory':'actual-combined01','run':'cockpit05-observer05-combined-01','maximumSeconds':1960,'holdSeconds':1802}}
ARTIFACT_RESERVE=4*2**20

def sha(path):return OLD.sha(path)
def build_receipt():return json.loads((ROOT/BUILD).read_text())
def __getattr__(name):
 if name=='APK_SHA256':return build_receipt()['sha256']
 if name=='SOURCE_SHA256':return build_receipt()['sourceSHA256']
 raise AttributeError(name)
def policy():return import_module(POLICY)
def with_artifact_budget(b):
 b=json.loads(json.dumps(b));b['categories']['newIsolatedAPKAndArchiveReserve']=ARTIFACT_RESERVE;b['taskHardPeakBytes']+=ARTIFACT_RESERVE;b['requiredFreeBytes']+=ARTIFACT_RESERVE;b['admitted']=None if b['actualFreeBytes']is None else b['actualFreeBytes']>=b['requiredFreeBytes'];return b
def task_budget(free_bytes=None):return case_budget(free_bytes)
def case_budget(free_bytes=None,maximum_seconds=1960):return with_artifact_budget(observer().case_budget(free_bytes,maximum_seconds))
def campaign_budget(free_bytes=None):
 b=observer().campaign_budget(free_bytes);b['taskHardPeakBytes']+=ARTIFACT_RESERVE;b['newIsolatedAPKAndArchiveReserve']=ARTIFACT_RESERVE;return b
def observer():return import_module(OBSERVER+'.policy')
def build_config(*a,**kw):return observer().build_config(*a,**kw)
def expected_context(*a,**kw):return OLD.expected_context(*a,**kw)
def selected_sources():return {str(p.relative_to(ROOT)):sha(p)for p in sorted(Path(__file__).parent.rglob('*.py'))if '__pycache__'not in p.parts and '/qa/'not in str(p)}
def build_input_contract(repository=ROOT):
 r=Path(repository);prior=json.loads((r/'evidence/betaintegrated01-cockpit05-nativeio04/host/input-contract01.json').read_text());v=json.loads(json.dumps(prior));receipt=build_receipt();apk=r/receipt['apk'];assert sha(apk)==receipt['sha256'];assert len(receipt['sourcePins'])==37
 sources=dict(prior['sourceSHA256']);sources.update(receipt['sourcePins']);sources.update(policy().source_binding());sources.update(observer().source_binding());sources.update(observer().feature_proof()['sourceSHA256']);sources.update(selected_sources())
 for name,h in sources.items():
  if sha(r/name)!=h:raise ValueError('SOURCE_DRIFT:'+name)
 with zipfile.ZipFile(apk)as z:
  assert z.read('assets/expected-providers.json')==(r/PROVIDERS).read_bytes()
  assert json.loads(z.read('assets/source-identity.json'))['sourceSHA256']==receipt['sourceSHA256']
  dex=z.read('classes.dex');assert b'Lvn/rtr/aeris/cockpitio04/CockpitActivity;'in dex and b'Lvn/rtr/aeris/cockpit05/CockpitActivity;'not in dex
 metadata=dict(prior['metadataSHA256']);metadata.update({n:sha(r/n)for n in(BUILD,BASELINE_RECEIPT,CURRENT_BASELINE_RECEIPT,'evidence/betaintegrated01-cockpit05-clockowner02/host/source-manifest01.json','evidence/betaintegrated01-cockpit05-observer05/host/source-manifest01.json')})
 v.update(format='aeris-observer05-current-package-input-closure',package=PACKAGE,activity=ACTIVITY,apk=receipt['apk'],apkSHA256=receipt['sha256'],APKSourceSHA256=receipt['sourceSHA256'],sourceSHA256=sources,metadataSHA256=metadata,newEvidenceRoot=EVIDENCE,runtimeEntryModule=RUNTIME,externalRecordingPolicy=policy().amendment(),externalObserverRecordingPolicy=observer().amendment(),capacity=task_budget(),priorDraftRevisions=[1],newActualDraftRevision=None,baselinePolicy='EXACT_CURRENT15_PRIVATE_R1_CLOSED_SHORT_PLUS_OLD233_NO_SAVE_OR_SEED',newCasePolicies=CASES,oldPackage=OLD_PACKAGE,oldPackageBaselineSHA256=sha(r/BASELINE_RECEIPT),newIsolatedArtifactReserveBytes=ARTIFACT_RESERVE)
 return v
def make_manifest():return build_input_contract()
def verify_full_inputs():
 v=json.loads((ROOT/EVIDENCE/'host/input-contract01.json').read_text())
 if v['runtimeEntryModule']!=RUNTIME or v['package']!=PACKAGE:raise ValueError('ISOLATED_PACKAGE_RUNTIME')
 for n,h in {**v['sourceSHA256'],**v['metadataSHA256']}.items():
  if sha(ROOT/n)!=h:raise ValueError('SELECTED_SOURCE_DRIFT:'+n)
 if v['externalRecordingPolicy']!=policy().amendment():raise ValueError('FROZEN_RUNTIME_AMENDMENT_DRIFT')
 if v['externalObserverRecordingPolicy']!=observer().amendment():raise ValueError('OBSERVER_RECORDING_AMENDMENT_DRIFT')
 return v
if __name__=='__main__':
 p=ROOT/EVIDENCE/'host/input-contract01.json';p.parent.mkdir(parents=True,exist_ok=True);p.open('x').write(json.dumps(make_manifest(),indent=2)+'\n');print(json.dumps({'path':str(p),'sha256':sha(p)}))
