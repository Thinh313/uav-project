"""Source privileged-probe boundary fixture; no actual SDK/ACK/Android claim."""
from pathlib import Path
from unittest.mock import patch
import base64,hashlib,json,shutil,sys,time
P=Path(__file__).resolve();R=P.parents[1];REPO=R.parents[2];sys.path[:0]=[str(R/'source'),str(REPO)]
from aeris_runtime.metadata_budget import MetadataBudget,encoded
from aeris_runtime.android import AndroidDevice
from aeris_runtime.product_native import ProductNativeProbe
from aeris_runtime.product_writer import ProductWriter
LAB=REPO/'evidence/betasim-integrated01/runtime/.rollover';C={'run':'roll','epoch':'a'*32,'boot':'b'*32,'operator':'pilot','generation':'c'*32,'profileId':'WORKBENCH_SIM_V1'}
SPKI=bytes.fromhex('3059301306072a8648ce3d020106082a8648ce3d03010703420004')
def observation(probe,epoch,key,sequence):
 der=SPKI+key*64;s={'requestNonce':str(sequence)*32,'sourceSHA256':probe.source,'pid':100+sequence,'processEpoch':epoch,'input':{'producerPublicKeyX509Base64':base64.b64encode(der).decode(),'producerKeyId':hashlib.sha256(der).hexdigest(),'producerSignatureAlgorithm':'SHA256withECDSA','configured':False,'pending':False,'journal':{'generation':str(sequence)*32}}};r={'requestNonce':s['requestNonce'],'sourceSHA256':probe.source,'actualPID':s['pid'],'APKSHA256':probe.apk};probe.latest=s;probe._latest_validated_raw=encoded(s);probe.last_ref=probe.device.store.receipt('request-product-%05d.json'%sequence,r);probe.pid=s['pid'];probe.process_epoch=epoch

def deny(f):
 try:f()
 except ValueError:return
 raise AssertionError('not refused')
def main():
 assert not LAB.exists();LAB.mkdir(parents=True);checks=[]
 try:
  b=MetadataBudget(LAB/'metadata-budget',lambda:{'metadataBytes':0},mock=True,free=lambda:64*2**30);b.admit();b.tick('cases');d=AndroidDevice('/mock/adb','emulator-5582',LAB/'sessions/roll/android-api',budget=b,observer_tag='AERIS_PRODUCT_STATUS');p=ProductNativeProbe(d,{'native':{'sourceSHA256':'d'*64,'APK_SHA256':'e'*64}});p.requests=15;observation(p,'f'*32,b'a',1);w=ProductWriter(b,C);r1=w.register_native_probe(p);assert r1['generation']==1 and r1['priorRegistrationRef']is None;checks.append('first-source-bound-registration-immutable')
  deny(lambda:w.register_native_probe(p));checks.append('ordinary-reenrollment-is-not-a-fallback')
  oldref=p.last_ref
  with patch.object(d,'_check_budget_actor',return_value=None),patch.object(d,'_cold_absence',return_value={'path':'original-cold-command'}),patch.object(d,'_installed_sha',return_value=({'path':'installed-path'},{'path':'installed-sha'})):
   transition=p.prepare_rollover(deadline_ns=time.monotonic_ns()+10**9)
  assert p.probe_generation==2 and p.latest is None and p.process_epoch is None and p.requests==15 and transition['previousObservationRef']==oldref and transition['authorityRestorable']is False;checks.append('planned-cold-transition-keeps-old-refs-UNKNOWN-and-global-status-credits')
  observation(p,'f'*32,b'a',2);deny(lambda:w.register_native_probe(p));checks.append('old-epoch-key-cannot-be-registered-as-new-generation')
  observation(p,'1'*32,b'b',3);r2=w.register_native_probe(p);assert r2['generation']==2 and r2['priorRegistrationRef']==r1['rootRegistrationRef']and r2['rolloverSourceRef']==transition['sourceReceiptRef'];assert len(w.native_registrations)==2;assert len(encoded({'version':1,'sequence':1,'ok':True,'committed':True,'ref':{'path':'reports/product-clock-proofs.jsonl','offset':0,'bytes':555,'sha256':'a'*64,'writeSequence':15},'error':None,'nativeRegistration':{k:v for k,v in{**r2,'challenge':'b'*32}.items()if k!='originalStoreRoot'}}))<=2048;deny(lambda:w.register_native_probe(p));deny(lambda:p.prepare_rollover(deadline_ns=time.monotonic_ns()+10**9));checks.append('one-new-epoch-key-registration-with-original-prior-proof-no-third-generation')
  report={'status':'PASS_SOURCE_BOUNDARY_MOCK_NOT_ORIGINAL_ANDROID_ACK','groups':checks,'actualAndroidAP':False,'scope':'privileged source-probe fixture only; complete original ACK/SDK cold lifecycle replay and signatures not claimed'}
 finally:shutil.rmtree(LAB)
 (REPO/'evidence/betasim-integrated01/runtime/native-rollover-mock.json').write_text(json.dumps(report,indent=2)+'\n');print(report['status'],len(checks))
if __name__=='__main__':main()
