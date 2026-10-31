from pathlib import Path
import sys,json,hashlib,copy,importlib.util
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[5];P=Path(__file__).resolve().parent.parent/'actual_combined_cold.py';spec=importlib.util.spec_from_file_location('cold05',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
O=R/'evidence/betaintegrated01-cockpit05-entry10-flight/qa/package-mock02';O.mkdir();H='c76669fa97326232c6129d0f93d3b12751a424a0ce724669ff51e29f6db958c3';S='4fe53ee61afd133a9075c7e1736e09406fb4449afc7ce2c01c0c45c9a3926c23';ADB=['/opt/homebrew/share/android-commandlinetools/platform-tools/adb','-s','emulator-5582'];PKG='vn.rtr.aeris.cockpit05';INST='/data/app/~~MOCK/vn.rtr.aeris.cockpit05-MOCK/base.apk';ctx=__import__('importlib').import_module('planning.betaintegrated01.cockpit05-entry10.full.contract').expected_context('cockpit05-entry10-combined-01','e','b','g','o')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v));return p
checks=[]
for name in ['positiveSyntheticReceiptsNotActualADB','foreignSerial','oldPackageArgv','timeout','exitBool','stdoutHashMismatch','stdoutBytesMismatch','multiplePackagePaths','hashWrong','hashOtherPath','receiptOutsideAndroid','receiptSHAMismatch','foreignExpectedPackage','evidenceHashMismatch']:
 C=O/name;C.mkdir();ar=C/'android';ar.mkdir();pathdir=ar/'0001';pathdir.mkdir();hashdir=ar/'0002';hashdir.mkdir()
 recs=[]
 for d,argv,out in[(pathdir,ADB+['shell','pm','path',PKG],('package:'+INST+'\n').encode()),(hashdir,ADB+['shell','sha256sum',INST],(H+'  '+INST+'\n').encode())]:
  (d/'stdout.bin').write_bytes(out);(d/'stderr.bin').write_bytes(b'');recs.append(dict(argv=argv,exit=0,timedOut=False,stdoutBytes=len(out),stderrBytes=0,stdoutSHA256=hashlib.sha256(out).hexdigest(),stderrSHA256=hashlib.sha256(b'').hexdigest()))
 if name=='foreignSerial':recs[0]['argv'][2]='emulator-9999'
 if name=='oldPackageArgv':recs[0]['argv'][-1]='vn.rtr.aeris.cockpit04'
 if name=='timeout':recs[0]['timedOut']=True
 if name=='exitBool':recs[0]['exit']=False
 if name=='stdoutHashMismatch':recs[0]['stdoutSHA256']='0'*64
 if name=='stdoutBytesMismatch':recs[0]['stdoutBytes']+=1
 if name in('multiplePackagePaths','hashWrong','hashOtherPath'):
  index=0 if name=='multiplePackagePaths'else 1;d=pathdir if index==0 else hashdir
  out=(('package:'+INST+'\npackage:'+INST+'\n')if index==0 else(('0'*64 if name=='hashWrong'else H)+'  '+(INST if name=='hashWrong'else INST.replace('base.apk','other.apk'))+'\n')).encode();(d/'stdout.bin').write_bytes(out);recs[index]['stdoutBytes']=len(out);recs[index]['stdoutSHA256']=hashlib.sha256(out).hexdigest()
 pp=put(pathdir/'receipt.json',recs[0]);hp=put(hashdir/'receipt.json',recs[1])
 evidence=dict(package=PKG,expectedPackage=PKG,installedAPK_SHA256=H,selectedAPKSourceSHA256=S,APKPathReadCommandReceipt=str(pp),APKPathReadCommandReceiptSHA256=sha(pp),APKHashReadCommandReceipt=str(hp),APKHashReadCommandReceiptSHA256=sha(hp))
 if name=='receiptOutsideAndroid':other=put(C/'outside.json',recs[0]);evidence.update(APKPathReadCommandReceipt=str(other),APKPathReadCommandReceiptSHA256=sha(other))
 if name=='receiptSHAMismatch':evidence['APKPathReadCommandReceiptSHA256']='0'*64
 if name=='foreignExpectedPackage':evidence['expectedPackage']='vn.rtr.aeris.cockpit04'
 ep=put(C/'installed-package-observation-evidence.json',evidence);value=dict(package=PKG,sourceSHA256=S,apkSHA256=H,**{k:ctx[k]for k in('run','epoch','boot','generation')},observedHostNs=1,observationEvidenceSHA256=sha(ep),observationEvidencePath=str(ep))
 if name=='evidenceHashMismatch':value['observationEvidenceSHA256']='0'*64
 put(C/'installed-package-observation.json',value)
 try:m.installed_package_proof(C,ctx);ok=name=='positiveSyntheticReceiptsNotActualADB'
 except(AssertionError,ValueError,KeyError,TypeError):ok=name!='positiveSyntheticReceiptsNotActualADB'
 checks.append(dict(id=name,pass_=ok))
assert all(c['pass_']for c in checks)
paths=[P,R/'planning/betaintegrated01/cockpit05-entry10/full/receiver05.py',R/'planning/betaintegrated01/cockpit05-entry10/full/contract.py'];r={'status':'PASS_CURRENT_RETAINED_COMMAND_PROOF_MOCK_NOT_ACTUAL_ADB','tests':checks,'sourcePins':{str(p.relative_to(R)):sha(p)for p in paths},'scope':'SyntheticretainedADBcommandreceipts only; validatesargv/target/path/hash/bytecounts/exit/timeouts/insideandroid. Notactualdeviceexecution or thirtyminutes.','ADBCalls':0,'wholeBetaAccepted':False};(O/'results.json').open('x').write(json.dumps(r,indent=2)+'\n');print(r['status'],len(checks))
