"""Fixed package seam checks with injected original-byte readers, no ADB."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import base64,copy,hashlib,json,os,sys
R=Path(__file__).resolve().parents[3];T=R/'planning/betasim-integrated01/runtime';sys.path[:0]=[str(T/'source'),str(R)];os.environ['AERIS_REPOSITORY_ROOT']=str(R)
from aeris_runtime.application09 import AndroidDomain09,PACKAGE,ACTIVITY,RECEIVER,ACTION
from aeris_runtime.android import AndroidDevice
from aeris_runtime.product_native09 import validate,verify_application_original
from aeris_runtime.product_types import selected_types
from aeris_runtime.metadata_budget import encoded
checks=[]
def deny(fn):
 try:fn()
 except Exception:return
 raise AssertionError('negative unexpectedly admitted')
def test(name,fn):fn();checks.append(name)
def device(cls=AndroidDomain09,tag='AERIS_PRODUCT_STATUS',serial='emulator-5582'):
 d=cls.__new__(cls);d.serial=serial;d.observer=SimpleNamespace(tag=tag);d.status_socket=None;d._install_authorization=None;d.preparation_commands=0;return d
def fixed_commands():
 d=device();nonce='a'*32
 for args in[['shell','pm','path',PACKAGE],['shell','run-as',PACKAGE,'pwd','-P'],['shell','pidof',PACKAGE],['shell','am','start','-n',ACTIVITY],['shell','am','broadcast','-a',ACTION,'-n',RECEIVER,'--es','requestNonce',nonce],['shell','run-as',PACKAGE,'cat','files/product-observations01/status-'+nonce+'.json']]:assert d._command_bound(args)>0
 for args in[['shell','pm','path','vn.rtr.aeris.mission'],['shell','run-as','vn.rtr.aeris.mission','cat','files/product-observations01/status-'+nonce+'.json'],['shell','run-as',PACKAGE,'pwd'],['shell','am','start','-n',PACKAGE+'/.ProductActivity'],['shell','am','start','-n','other/vn.rtr.aeris.mission.ProductActivity'],['install','/unowned.apk'],['uninstall',PACKAGE],['shell','pm','clear',PACKAGE]]:deny(lambda:d._command_bound(args))
 for wrong in[device(tag='AERIS_MISSION'),device(serial='emulator-5580')]:deny(lambda:wrong._command_bound(['shell','pm','path',PACKAGE]))
 deny(lambda:device(AndroidDevice)._command_bound(['shell','pm','path',PACKAGE]));deny(lambda:selected_types({'native':{'package':'other'}}))
def snapshot():
 public=bytes.fromhex('3059301306072a8648ce3d020106082a8648ce3d03010703420004')+bytes(range(64));epoch='e'*32;source='s'*64;nonce='a'*32
 q={'format':'aeris-betasim-native-status','version':1,'requestNonce':nonce,'observedElapsedNs':123,'processEpoch':epoch,'pid':1234,'package':PACKAGE,'sourceSHA256':source,'sourceIdentity':{'format':'aeris-betasim-product-source-identity','sourceSHA256':source,'package':PACKAGE,'production':False,'productProtocolSHA256':'p'*64},'input':{'processEpoch':epoch,'authorityRestorable':False,'foreground':True,'configured':False,'closed':False,'failed':False,'pending':False,'sequence':0,'producerPublicKeyX509Base64':base64.b64encode(public).decode(),'producerKeyId':hashlib.sha256(public).hexdigest(),'producerSignatureAlgorithm':'SHA256withECDSA','producerIdentityScope':'EPHEMERAL_SIM_PROCESS_NOT_PHYSICAL_HID_ATTESTATION'},'authorityRestorable':False,'actualImages':0,'inventory':{'scope':'PRIVATE_FILES_ONLY_NOT_WHOLE_APP_DATA_DIR','logicalBytes':0,'allocatedBytes':0,'entries':0,'measuredBeforeOwnSnapshotWrite':True},'workspaceNamespace':'betasim-workspace01','exportBudget':{'reservedBytes':0,'capBytes':192*2**20,'unknownWriteRefunded':False},'webGeometry':{}}
 ack={'version':1,'requestNonce':nonce,'path':'files/product-observations01/status-'+nonce+'.json','sha256':'b'*64,'bytes':1000,'processEpoch':epoch,'pid':1234};return q,ack,{'source':source,'pid':1234,'nonce':nonce,'protocol_sha':'p'*64}
def native_identity():
 q,ack,kw=snapshot();assert validate(q,ack,**kw)is q
 for field,value in[('package','vn.rtr.aeris.mission'),('pid',1235),('sourceSHA256','x'*64),('processEpoch','f'*32)]:bad=copy.deepcopy(q);bad[field]=value;deny(lambda:validate(bad,ack,**kw))
 for field,value in[('package','vn.rtr.aeris.mission'),('sourceSHA256','x'*64),('productProtocolSHA256','x'*64)]:bad=copy.deepcopy(q);bad['sourceIdentity'][field]=value;deny(lambda:validate(bad,ack,**kw))
 bad=copy.deepcopy(q);bad['exportBudget']['reservedBytes']=192*2**20+1;deny(lambda:validate(bad,ack,**kw))
def original_private_join():
 manifest={'native':{'sourceSHA256':'s'*64,'APK_SHA256':'a'*64}};proof={'format':'aeris-root-observed-development-application-domain','version':1,'applicationId':PACKAGE,'serial':'emulator-5582','sourceSHA256':'s'*64,'APKSHA256':'a'*64,'privateFilesDirectory':'/data/user/0/'+PACKAGE+'/files','nativeReportedApplicationId':False,'installedPathRef':'path','installedSHARef':'sha','actualPrivateDirectoryCommandRef':'pwd'}
 proof['candidateSHA256']=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
 replies={'path':(['pm','path',PACKAGE],b'package:/data/app/new/base.apk\n'),'sha':(['sha256sum','/data/app/new/base.apk'],('a'*64+'  /data/app/new/base.apk\n').encode()),'pwd':(['run-as',PACKAGE,'pwd','-P'],('/data/user/0/'+PACKAGE+'\n').encode())}
 def cmd(root,ref):remote,raw=replies[ref];return{},None,remote,raw
 with patch('aeris_runtime.product_native09.read_ref',side_effect=lambda root,ref:encoded(proof)),patch('aeris_runtime.status15_reader.command',side_effect=cmd):
  assert verify_application_original('INJECTED_RAM_NOT_ACTUAL','proof',manifest)==proof
  for field,value in[('applicationId','vn.rtr.aeris.mission'),('sourceSHA256','x'*64),('privateFilesDirectory','/data/user/0/vn.rtr.aeris.mission/files'),('serial','emulator-5580')]:old=proof[field];proof[field]=value;deny(lambda:verify_application_original('RAM','proof',manifest));proof[field]=old
  old=replies['pwd'];replies['pwd']=(['run-as','vn.rtr.aeris.mission','pwd','-P'],b'/data/user/0/vn.rtr.aeris.mission\n');deny(lambda:verify_application_original('RAM','proof',manifest));replies['pwd']=old
  old=replies['sha'];replies['sha']=(old[0],('b'*64+'  /data/app/new/base.apk\n').encode());deny(lambda:verify_application_original('RAM','proof',manifest));replies['sha']=old
test('fixed_new_package_full_FQNs_only_no_oldapp_uninstall_clear_or_arbitrary_install',fixed_commands)
test('new_DTO_package_PID_source_identity_protocol_and_original192_export_bound',native_identity)
test('Root_original_package_APK_source_same_device_and_actual_private_directory_join',original_private_join)
sources=[T/'source/aeris_runtime'/n for n in('application09.py','product_native09.py','product_types.py','android.py')];out=R/(sys.argv[1]if len(sys.argv)>1 else'evidence/betasim-integrated01/qa/application09-01.json');assert not out.exists();out.write_bytes(encoded({'format':'aeris-independent-application09-source-boundary-qa','status':'PASS_RAM_COMMAND_VALIDATION_NOT_ACTUAL_ANDROID','checks':checks,'sourcePins':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sources},'fixtureSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'originalByteCommandReaderInjected':True,'syntheticPublicKeyUsedForDTOSchemaOnly':True,'actualActors':False,'oldAppMigrationOrQuotaRecoveryAcceptance':False}));print(json.dumps({'path':str(out.relative_to(R)),'checks':len(checks),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}))
