from pathlib import Path
import json,hashlib,datetime,shutil,os,subprocess
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,j):
 with (R/n).open('x') as f:json.dump(j,f,ensure_ascii=False,indent=2);f.write('\n')
checks={}
for name,groups in [('tests03/results.json',14),('ui02.json',10),('http03/results.json',7)]:
 p=R/'evidence/betaops01'/name;j=json.loads(p.read_text());assert j['status']=='PASS' and j['groups']==groups;checks[str(p.relative_to(R))]={'sha256':sha(p),'groups':groups,'status':j['status']}
for name in ['static-final01.json','browser01.json']:
 p=R/'evidence/betaops01'/name;j=json.loads(p.read_text());assert j['status'] in ['PASS','PASS_WITH_DEFERRED'];checks[str(p.relative_to(R))]={'sha256':sha(p),'status':j['status']}
a=json.loads((R/'evidence/coach01/preservation-betaops01-after.json').read_text());b=json.loads((R/'evidence/coach01/preservation-betaops01-before.json').read_text());assert all(a[k]==b[k] for k in ['references','observed','entryMissing','trackedStatus'])
old=json.loads((R/'evidence/coach02/handoff-final01.json').read_text());assert all(sha(R/n)==v['sha256'] for n,v in old['inventory'].items())
for p in (R/'pilot/betaops01').glob('*.mjs'):subprocess.run(['node','--check',str(p)],check=True,capture_output=True)
size=sum(p.lstat().st_size for p in (R/'evidence/betaops01').rglob('*') if p.is_file() and not p.is_symlink());assert size<48*2**20
free=shutil.disk_usage(R).free;assert free>20*2**30
ver={'format':'aeris-betaops01-verification-v1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'clientDate':'2026-10-26','status':'READY_WITH_DEFERRED_DESK_REPLAY_SCOPE','requirements':{'implemented':5,'total':5,'browserDesktop':'OBSERVED_SCOPED','filePickerAndSavedBrowserDownload':'NOT_CHECKED','AndroidSITLNewRun':'NOT_RUN_NOT_REQUIRED_FOR_DESK','hardwareProduction':'NOT_READY'},'scenarioGroups':31,'checks':checks,'preservation':{'identitiesUnchanged':len(a['observed']),'preexistingMissing':len(a['entryMissing']),'coach02MembersUnchanged':len(old['inventory']),'continuousPresenceClaim':False,'restorationAttempted':False},'resources':{'freeBytes':free,'ownEvidenceBytesBeforeFinal':size,'evidenceBudgetMiB':48,'admissionGiB':20,'floorGiB':10,'reserveMiB':256,'noUserCleanupRequest':True,'wholeProjectCopy':False,'newInstallOrBuild':False,'newDisposableScratch':False},'value':'WORKFLOW_IMPLEMENTED_HUMAN_COMPARISON_NOT_MEASURED','independentHumanQA':False,'sourceAuthenticated':False,'preview':{'pidAtFinalLaunch':19546,'url':'http://127.0.0.1:8900/','limitMinutes':30,'mutableStoreExcluded':'evidence/betaops01/workspace01'}}
save('evidence/betaops01/verification-final01.json',ver)
files=[]
for d in ['pilot/betaops01','planning/betaops01','evidence/betaops01','delivery/beta-operations01']:
 for p in (R/d).rglob('*'):
  if 'workspace01' in p.relative_to(R).parts:continue
  if p.is_file() or p.is_symlink():files.append(p)
files += [R/'delivery/COMPLETION-BETAOPS01.md',R/'evidence/coach01/preservation-betaops01-before.json',R/'evidence/coach01/preservation-betaops01-after.json']
inv={}
for p in sorted(set(files)):
 n=str(p.relative_to(R));assert p.name!='handoff-final01.json'
 inv[n]={'kind':'SYMLINK','linkTarget':os.readlink(p)} if p.is_symlink() else {'kind':'REGULAR_FILE','bytes':p.stat().st_size,'sha256':sha(p)}
save('evidence/betaops01/handoff-final01.json',{'format':'aeris-betaops01-handoff-v1','scope':ver['status'],'inventory':inv,'mutableStoreExcluded':ver['preview']['mutableStoreExcluded'],'noSourceAuthentication':True})
p=R/'evidence/betaops01/handoff-final01.json';digest=sha(p)
with (R/'evidence/betaops01/handoff-final01.sha256').open('x') as f:f.write(digest+'  handoff-final01.json\n')
for n,v in inv.items():
 p=R/n
 if v['kind']=='SYMLINK':assert p.is_symlink() and os.readlink(p)==v['linkTarget']
 else:assert sha(p)==v['sha256'] and p.stat().st_size==v['bytes']
print(json.dumps({'status':ver['status'],'scenarioGroups':31,'members':len(inv),'handoffSha256':digest,'ownEvidenceMiB':size/2**20,'freeGiB':free/2**30,'preservedCoach02':len(old['inventory'])}))
