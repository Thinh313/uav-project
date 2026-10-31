from pathlib import Path
import sys,json,hashlib,importlib.util,datetime
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[3];E=R/'evidence/phone06-qa';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();freeze=R/'evidence/phone06/builder/source-ready05.json';pins=json.loads(freeze.read_text())['files'];scope=['planning/phone06/receiver06.py','planning/phone06/phase06.py']
for p in scope:assert sha(R/p)==pins[p],p
mapping=json.loads((E/'receiver-input-map01.json').read_text());expected={'format':'aeris-phone06-public-export-expectation','version':1,**mapping['expected']};expect=E/'receiver-expect01.json';expect.open('x').write(json.dumps(expected,indent=2)+'\n');es=sha(expect)
sys.path.insert(0,str(R/'planning/phone06'));spec=importlib.util.spec_from_file_location('qa_receiver05',R/scope[0]);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
results=[];p=E/'package-fixtures01/positive-native.zip';positive=m.verify(p,expected['run'],expect,es);assert positive['status']=='PASS_PUBLIC_PACKAGE_INTEGRITY_ONLY'and positive['missionAcceptance']=='NOT_ASSERTED'and positive['authorityRestorable']is False;results.append({'id':'PQR_POSITIVE','status':'PASS_SCOPED','result':positive})
p=E/'package-fixtures01/wrongreceiver-native.zip';error=None
try:m.verify(p,expected['run'],expect,es)
except ValueError as x:error=str(x)
assert error=='INDEPENDENT_RECEIVER_CONTEXT_BINDING',error
results.append({'id':'PQ16','status':'PASS_SCOPED','refusal':error,'packageSHA256':sha(p),'limit':'wrongreceiver input only; doesnotclaim allcorruption variants tested'})
for p in scope:assert sha(R/p)==pins[p],p
out={'at':datetime.datetime.now().astimezone().isoformat(),'status':'PASS_SCOPED_PUBLIC_PACKAGE_RECEIVER','sourceFreeze':str(freeze.relative_to(R)),'sourceFreezeSha256':sha(freeze),'scopedSourcePins':{p:pins[p]for p in scope},'results':results,'newDistinctInputs':1,'originalCaseReached':'PQ16','expectedContextValuesPredeclared':'receiver-input-map01.json','expectationSha256':es,'expectationEnvelopeMappedAfterStableAPI':True,'positiveCounterexampleBeforeRepair':'receiver-positive-before01.json','producer':'actualfrozenRawArchive96+RawJournal95 withsyntheticMETA/CLOSED','actualSAFDeviceMissionAuthority':'NOT_CHECKED','noNetworkProcessOrDevice':True};(E/'receiver-heldout05.json').open('x').write(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
