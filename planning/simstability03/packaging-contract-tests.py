from pathlib import Path
import importlib.util,json,hashlib,datetime
R=Path(__file__).resolve().parents[2];p=R/'planning/simstability03/assemble-handoff.py';spec=importlib.util.spec_from_file_location('assembly_contract',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);digest='df3eb4ec961e2fc83116440ec017796593b36847f2e1a601e7dd0a8b11ec5c8f'
for invalid in['../escape','/absolute','a/../b','a\\b','a//b','./file','x\0y']:
 try:m.safe(invalid);raise AssertionError('unsafe accepted')
 except ValueError:pass
for name in['pilot/simhand01/cockpit.mjs','runtime/sitl/arducopter','QUALIFICATION-SIM-STABILITY03.json']:assert m.safe(name)==name
b=m.checksum(b'manifest bytes');assert len(b)==65 and b.endswith(b'\n')and len(b.strip())==64
q={'assemblyAuthorized':True,'sourceManifestSHA256':digest,'runtimeAcceptance':'SCOPED_RESULT_TEST_ONLY','status':'MOCK_NOT_PRODUCT_QUALIFICATION','verifiedOutcomes':['mock'],'remainingGates':['physical acceptance not checked']};assert m.validate_authorization(q,digest)==q
for patch in[{'assemblyAuthorized':False},{'runtimeAcceptance':'PENDING'},{'runtimeAcceptance':'RUNNING_NOT_FINAL'},{'status':'PENDING'},{'sourceManifestSHA256':'0'*64}]:
 try:m.validate_authorization({**q,**patch},digest);raise AssertionError('bad auth accepted')
 except AssertionError as e:assert str(e)!='bad auth accepted'
raw,actual,source,entries,pins,apk=m.source_entries(R/'.local/simstability03/receiver03',digest);assert actual==digest and len(entries)==110 and apk[1]['sha256']==m.APK_SHA
pending={'assemblyAuthorized':False,'sourceManifestSHA256':digest,'runtimeAcceptance':'PENDING','status':'PENDING','verifiedOutcomes':[],'remainingGates':['Await Contractor final declared runtime/SAF/audio status.'],'scope':'TEMPLATE_ONLY_NOT_ASSEMBLY_AUTHORIZATION'}
(R/'planning/simstability03/qualification-pending.template.json').write_text(json.dumps(pending,indent=2)+'\n');receipt={'format':'aeris-simstability03-packaging-preparation','version':1,'status':'PASS_PREPARATION_NOT_FINAL_ASSEMBLY','atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceManifestSHA256':digest,'sourcePayloadFiles':len(entries),'sourcePayloadBytes':sum(x['bytes']for x in entries.values()),'originalAPK':{'path':apk[0],**apk[1]},'scriptSHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'checks':['safe-path rejection','exact65byte checksum','pending/running/unbound authorization rejected','110 member sourceclosure allSHA/mode/type verified','exact unchanged developmentAPK','empty structural mountpoint retained'],'sourceUnchanged':True,'archiveAssembled':False,'runtimeStarted':False,'extractionPerformed':False,'scope':'PREPARATION_ONLY_WAITING_FINAL_CONTRACTOR_STATUS'};(R/'evidence/simstability03/packaging-preparation01.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
