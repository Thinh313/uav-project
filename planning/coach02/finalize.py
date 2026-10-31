from pathlib import Path
import hashlib,json,datetime,shutil,subprocess
R=Path(__file__).resolve().parents[2]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,data):
 p=R/name
 with p.open('x') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')
checks={}
for n,groups in [('tests02/results.json',17),('client02.json',6),('ui05.json',10),('guards01/results.json',5),('http02/results.json',7)]:
 p=R/'evidence/coach02'/n;j=json.loads(p.read_text());assert j['status']=='PASS' and j['groups']==groups,(n,j);checks[str(p.relative_to(R))]={'status':j['status'],'groups':groups,'sha256':digest(p)}
for n in ['oracle01.json','static-final01.json']:
 p=R/'evidence/coach02'/n;j=json.loads(p.read_text());assert j['status']=='PASS';checks[str(p.relative_to(R))]={'status':j['status'],'sha256':digest(p)}
b=json.loads((R/'evidence/coach01/preservation-coach02-before.json').read_text());a=json.loads((R/'evidence/coach01/preservation-coach02-after.json').read_text());assert all(a[k]==b[k] for k in ['references','observed','entryMissing','trackedStatus'])
old=json.loads((R/'evidence/coach01/ui-repair01/handoff-final01.json').read_text())['inventory'];changed=[n for n,v in old.items() if digest(R/n)!=v['sha256']];assert set(changed)=={'pilot/coach01/server.mjs','pilot/coach01/index.html'}
archives=json.loads((R/'evidence/coach02/before.json').read_text())['mutable'];assert all(digest(R/v['archive'])==v['sha256'] for v in archives.values())
run=subprocess.run(['node','pilot/coach02/receiver.mjs','evidence/coach02/tests02/reference-package.json'],cwd=R,check=True,capture_output=True,text=True);receiver=json.loads(run.stdout);assert receiver['status']=='VERIFIED_MOCK_REPLAY' and not receiver['authorityRestorable'] and not receiver['sourceAuthenticated']
free=shutil.disk_usage(R).free;assert free>=20*2**30
size=sum(p.stat().st_size for p in (R/'evidence/coach02').rglob('*') if p.is_file());assert size<64*2**20
verification={'format':'aeris-coach02-verification-v1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'READY_CODE_MOCK_REPLAY_SCOPE_ONLY','checks':checks,'testGroups':45,'receiverColdProcess':receiver,'preservation':{'identitiesUnchanged':len(a['observed']),'preexistingMissing':len(a['entryMissing']),'newRestoration':False,'continuousPresenceClaim':False,'unchangedPriorHandoffMembers':len(old)-len(changed),'authorizedChangedMembers':changed,'exactOriginalArchives':True},'limits':{'browserVisual':'NOT_CHECKED','touchHIDAndroidHera':'NOT_CHECKED','UIRealtime1x':'NOT_CHECKED','physicalTransfer':'NOT_MEASURED','humanTrainingOrLLMBaseline':'NOT_MEASURED','sourceAuthenticated':False,'independentHumanQA':False,'SITLRun':False,'newAPKOrSignature':False},'disk':{'freeBytes':free,'admissionGiB':20,'writeFloorGiB':10,'reserveMiB':256,'ownEvidenceBytesBeforeReceipt':size,'verificationBudgetMiB':64},'preview':{'url':'http://127.0.0.1:8897/manual/','pidAtLaunch':54628,'lifetimeMinutes':30,'notBrowserAcceptance':True}}
save('evidence/coach02/verification-final01.json',verification)
files=[]
for prefix in ['pilot/coach02','planning/coach02','evidence/coach02','delivery/coach02-manual']:
 for p in (R/prefix).rglob('*'):
  if p.is_file() and 'workspace01' not in p.relative_to(R).parts:files.append(p)
files += [R/'pilot/coach01/index.html',R/'pilot/coach01/server.mjs',R/'delivery/COMPLETION-COACH02.md',R/'evidence/coach01/preservation-coach02-before.json',R/'evidence/coach01/preservation-coach02-after.json']
assert not any(p.name=='handoff-final01.json' for p in files)
inv={str(p.relative_to(R)):{'bytes':p.stat().st_size,'sha256':digest(p)} for p in sorted(set(files))}
handoff={'format':'aeris-coach02-handoff-v1','scope':verification['status'],'browserVisualAcceptance':'NOT_CHECKED','mutableFutureTrainingStore':'evidence/coach02/workspace01','notSourceAuthentication':True,'inventory':inv}
save('evidence/coach02/handoff-final01.json',handoff)
p=R/'evidence/coach02/handoff-final01.json';hd=digest(p)
with (R/'evidence/coach02/handoff-final01.sha256').open('x') as f:f.write(hd+'  handoff-final01.json\n')
assert all(digest(R/n)==v['sha256'] and (R/n).stat().st_size==v['bytes'] for n,v in inv.items())
print(json.dumps({'status':verification['status'],'groups':45,'handoffMembers':len(inv),'handoffSHA256':hd,'preservationIdentities':len(a['observed']),'preexistingMissing':len(a['entryMissing']),'freeGiB':free/2**30,'noNewDisposableScratch':True}))
