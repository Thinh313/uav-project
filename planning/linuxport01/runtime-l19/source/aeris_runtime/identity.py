"""Flat source-bound native/provider identity; safe in host and Linux metadata paths."""
from pathlib import Path
import os,json,hashlib,re
from . import candidate,policy
from .paths import repository
from pilot.betaintegrated01.runtime.ap_stage import canonical
DEV_CERT='3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800'
def selected(config,candidate_dir=None):
 path=Path(candidate_dir or os.environ.get('AERIS_CANDIDATE_DIR',''))
 if not str(path)or str(path)=='.':raise ValueError('EXPLICIT_IMMUTABLE_CANDIDATE_REQUIRED')
 return candidate.load(path,config.get('runtimeCandidateSHA256'))
def native_selection(manifest):
 n=manifest['native'];return {'format':'aeris-runtime-native-selection','version':1,'package':n['package'],'APK_SHA256':n['APK_SHA256'],'sourceSHA256':n['sourceSHA256'],'buildReceiptSHA256':n['buildReceiptSHA256'],'sourcePins':n['sourcePins'],'developmentOnly':True}
def validate_native_selection(config,candidate_dir=None):
 policy.validate_recording_policy(config);m=selected(config,candidate_dir)
 if canonical(config.get('externalNativeClientSelection'))!=canonical(native_selection(m)):raise ValueError('EXACT_RUNTIME_NATIVE_SOURCE_REQUIRED')
 return native_selection(m)
def build_config(candidate_dir,variant,run,epoch,boot,evidence,case_id,maximum_seconds):
 manifest=json.loads((Path(candidate_dir)/'candidate.json').read_bytes());digest=hashlib.sha256(canonical(manifest)).hexdigest();manifest=candidate.load(candidate_dir,digest)
 v=policy.build_config(variant,run,epoch,boot,evidence,case_id,maximum_seconds=maximum_seconds);v.update(runtimeCandidateSHA256=digest,externalNativeClientSelection=native_selection(manifest));return v

def provider_binding(candidate_dir,config,context,*,input_provenance='ROOT_INJECTED_ANDROID_TOUCH'):
 """Build proposal from retained Native expected asset; real AP evidence gates stage."""
 import io,tarfile
 manifest=selected(config,candidate_dir);archive=(Path(candidate_dir)/'native-inputs.tar.gz').read_bytes()
 with tarfile.open(fileobj=io.BytesIO(archive),mode='r:gz') as t:
  raw=t.extractfile('native/mission-runtime/resources/expected-providers.json').read(65537)
 if len(raw)>65536:raise ValueError('EXPECTED_PROVIDER64KiB')
 providers=json.loads(raw);p=providers['profiles'][context['profileId']]
 if p['binarySHA256']!=config['APSHA256'] or p['modelSHA256']!=config['modelSHA256'] or p['configSHA256']!=config['expectedConfigSHA256'] or input_provenance not in ('ROOT_INJECTED_ANDROID_TOUCH','LOCAL_ANDROID_TOUCH_NOT_HID_ATTESTED'):raise ValueError('EXACT_DECLARED_PROVIDER_PHYSICAL_PROFILE')
 value={k:p[k]for k in ('version','mode','profileId','binarySHA256','modelSHA256','configSHA256','endpoint','firmware')};value.update(rootOwnedContainer=True,targetSystem=42,run=context['run'],epoch=context['epoch'],boot=context['boot'],operator=context['operator'],generation=context['generation'],inputProvenance=input_provenance);return value
