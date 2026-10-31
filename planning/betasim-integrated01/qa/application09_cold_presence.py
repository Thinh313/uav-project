"""Cold absence/PRESENT vs post-install path ordering, RAM original readers."""
from pathlib import Path
from unittest.mock import patch
import copy,hashlib,json,os,sys
R=Path(__file__).resolve().parents[3];T=R/'planning/betasim-integrated01/runtime';sys.path[:0]=[str(T/'source'),str(R)];os.environ['AERIS_REPOSITORY_ROOT']=str(R)
from aeris_runtime.product_native09 import verify_application_original
from aeris_runtime.application09 import PACKAGE,PRESENCE_ARGS
from aeris_runtime.metadata_budget import encoded
checks=[]
def deny(fn):
 try:fn()
 except Exception:return
 raise AssertionError('negative unexpectedly admitted')
def fixture(classification='ABSENT'):
 manifest={'native':{'sourceSHA256':'b'*64,'APK_SHA256':'c'*64}};digest=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest();commandrow={'exit':0,'captureComplete':True,'stdoutRef':{'fixture':'originalstdout'},'stderrRef':{'fixture':'originalstderr'},'failure':None,'startedHostNs':100,'endedHostNs':110}
 presence={'format':'aeris-fixed-development-application-presence','version':1,'package':PACKAGE,'user':0,'classification':classification,'failure':None,'authorityGranted':False,'originalCommandRef':'presence-command',**{k:commandrow[k]for k in('exit','captureComplete','stdoutRef','stderrRef')}}
 proof={'format':'aeris-root-observed-development-application-domain','version':1,'applicationId':PACKAGE,'serial':'emulator-5582','candidateSHA256':digest,'sourceSHA256':'b'*64,'APKSHA256':'c'*64,'privateFilesDirectory':'/data/user/0/'+PACKAGE+'/files','nativeReportedApplicationId':False,'presenceObservationRef':'presence','presenceClassification':classification,'installRef':'install'if classification=='ABSENT'else None,'pathVerificationBasis':'POST_INSTALL_SUCCESS_PATH_VERIFICATION'if classification=='ABSENT'else'PREINSTALL_PRESENT_PATH_VERIFICATION','installedPathRef':'path','installedSHARef':'sha','actualPrivateDirectoryCommandRef':'pwd'}
 original={'app':proof,'presence':presence};commands={'presence-command':(commandrow,list(PRESENCE_ARGS[1:]),b''if classification=='ABSENT'else('package:'+PACKAGE+'\n').encode()),'install':({**commandrow,'startedHostNs':120,'endedHostNs':130},['install','/fake/'+digest+'/native.apk'],b'Performing Streamed Install\nSuccess\n'),'path':({**commandrow,'startedHostNs':140,'endedHostNs':150},['pm','path',PACKAGE],b'package:/data/app/new/base.apk\n'),'sha':(commandrow,['sha256sum','/data/app/new/base.apk'],('c'*64+'  /data/app/new/base.apk\n').encode()),'pwd':(commandrow,['run-as',PACKAGE,'pwd','-P'],('/data/user/0/'+PACKAGE+'\n').encode())};return manifest,proof,presence,original,commands
def check(classification,mutate=None):
 manifest,proof,presence,original,commands=fixture(classification)
 if mutate:mutate(proof,presence,commands)
 def read(root,ref):return encoded(original[ref])
 def command(root,ref):row,args,raw=commands[ref];return row,None,args,raw
 with patch('aeris_runtime.product_native09.read_ref',side_effect=read),patch('aeris_runtime.once_reader.read_ref',side_effect=read),patch('aeris_runtime.status15_reader.command',side_effect=command):
  fn=lambda:verify_application_original('INJECTED_ORIGINAL_READERS_NOT_DEVICE','app',manifest)
  if mutate:deny(fn)
  else:assert fn()==proof
for value in['ABSENT','PRESENT']:check(value);checks.append('valid_'+value+'_uses_presence_list_and_correct_install_path_disposition')
check('ABSENT',lambda p,q,c:c['path'][0].update(startedHostNs=125));checks.append('pm_path_before_original_install_success_refused')
check('ABSENT',lambda p,q,c:c.update(install=(c['install'][0],c['install'][1],b'Failure\n')));checks.append('nonSuccess_install_output_refused_no_absence_fallback')
check('ABSENT',lambda p,q,c:c.update(install=(c['install'][0],['install','/wrong/native.apk'],b'Success\n')));checks.append('install_must_bind_exact_candidate_directory_nativeAPK')
check('PRESENT',lambda p,q,c:p.update(installRef='install'));checks.append('already_present_branch_cannot_reinstall_or_reset_data')
check('ABSENT',lambda p,q,c:c.update(**{'presence-command':(c['presence-command'][0],['pm','path',PACKAGE],b'')}));checks.append('old_pm_path_empty_output_not_an_original_absence_proof')
check('ABSENT',lambda p,q,c:p.update(privateFilesDirectory='/data/user/0/vn.rtr.aeris.mission/files'));checks.append('old_application_private_directory_cannot_certify_new_domain')
sources=[T/'source/aeris_runtime'/n for n in('application09.py','product_native09.py')];out=R/(sys.argv[1]if len(sys.argv)>1 else'evidence/betasim-integrated01/qa/application09-cold-presence01.json');assert not out.exists();out.write_bytes(encoded({'format':'aeris-independent-application09-cold-presence-source-qa','status':'PASS_RAM_ORIGINAL_READER_JOINS_NOT_ACTUAL_INSTALL','checks':checks,'sourcePins':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sources},'fixtureSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'actorsStarted':False,'originalCommandReaderInjected':True}));print(json.dumps({'path':str(out.relative_to(R)),'checks':len(checks),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}))
