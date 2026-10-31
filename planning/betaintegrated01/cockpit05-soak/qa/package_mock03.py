from pathlib import Path
import sys,json,hashlib,copy,importlib.util
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[4];P=Path(__file__).with_name('actual_combined_cold.py');spec=importlib.util.spec_from_file_location('cold05',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
O=R/'evidence/betaintegrated01-cockpit05-soak/qa/package-mock03';O.mkdir();raw=b'MOCK COMMAND EVIDENCE NOT ACTUAL ADB\n';ev=O/'evidence.txt';ev.write_bytes(raw);ctx=dict(run='cockpit05-combined-01',epoch='e',boot='b',generation='g',operator='o',profileId='p',binarySHA256='a'*64,configSHA256='b'*64)
v=dict(package='vn.rtr.aeris.cockpit05',sourceSHA256='4fe53ee61afd133a9075c7e1736e09406fb4449afc7ce2c01c0c45c9a3926c23',apkSHA256='c76669fa97326232c6129d0f93d3b12751a424a0ce724669ff51e29f6db958c3',**{k:ctx[k]for k in('run','epoch','boot','generation')},observedHostNs=1,observationEvidenceSHA256=hashlib.sha256(raw).hexdigest(),observationEvidencePath=str(ev));tests=[]
for name,change,reject in [('positiveSchemaNotActual',{},False),('foreignPackage',{'package':'vn.rtr.aeris.cockpit04'},True),('wrongContext',{'run':'old'},True),('wrongSelectedAPK',{'apkSHA256':'0'*64},True),('wrongEvidenceHash',{'observationEvidenceSHA256':'0'*64},True),('missingEvidence',{'observationEvidencePath':str(O/'absent')},True)]:
 d=O/name;d.mkdir();value={**v,**change};(d/'installed-package-observation.json').write_text(json.dumps(value))
 try:m.installed_package_proof(d,ctx);ok=not reject
 except(AssertionError,ValueError,KeyError,TypeError):ok=reject
 tests.append(dict(id=name,pass_=ok))
assert all(t['pass_']for t in tests)
r={'status':'PASS_PACKAGE_PROOF_BOUNDARIES_NOT_ACTUAL_ADB','tests':tests,'sourceSHA256':hashlib.sha256(P.read_bytes()).hexdigest(),'meaning':'Onlyschema/context/SHAretainedbytes gates; fabricatedMOCKcommandbytes aredeliberatelynotactualdeviceproof. ActualCLI requiresRootliveADBevidenceandfullclosedcase.','ADBCalls':0,'wholeBetaAccepted':False};(O/'results.json').open('x').write(json.dumps(r,indent=2)+'\n');print(r['status'],len(tests))
