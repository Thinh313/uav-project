"""Independent BETA06 admission inventory; reads old data, writes new QA evidence only."""
from pathlib import Path
import hashlib,json,datetime,os
R=Path('.');E=Path('evidence/beta06');E.mkdir(parents=True,exist_ok=True)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  while b:=f.read(1024*1024):h.update(b)
 return h.hexdigest()
def rd(p):return json.loads(Path(p).read_text())
old=Path('evidence/field02/clockvideo05');base=rd(old/'qa-preservation-before01.json');inv=rd(old/'final-artifact-fingerprints01.json');verification=rd(old/'final-verification01.json');errors=[];groups={}
assert verification['artifactInventory']['files']==len(inv['files'])==580
assert sha(old/'final-artifact-fingerprints01.json')==verification['artifactInventory']['sha256']=='a752b6b30fc5fa92dc1f165fc4dabe71b5b4a7b574561d421c283872d7a7fd59'
for key,g in base['groups'].items():
 dif=[]
 for n,h in g.items():
  try:
   if sha(n)!=h:dif.append({'path':n,'status':'HASH_MISMATCH'})
  except OSError as e:dif.append({'path':n,'status':'READ_ERROR','error':str(e)})
 groups[key]={'files':len(g),'differences':dif};errors+=dif
for n,q in inv['files'].items():
 try:
  if Path(n).stat().st_size!=q['bytes']or sha(n)!=q['sha256']:errors.append({'path':n,'status':'CLOCK05_FINAL_ARTIFACT_CHANGED'})
 except OSError as e:errors.append({'path':n,'status':'CLOCK05_FINAL_ARTIFACT_UNREADABLE','error':str(e)})
allold={};total=0
for p in sorted(Path('evidence/field02').rglob('*')):
 if p.is_symlink():
  q={'kind':'SYMLINK','linkTarget':os.readlink(p),'dereferencedRegularFile':p.is_file()}
  if p.is_file():q.update(bytes=p.stat().st_size,sha256=sha(p))
  allold[str(p)]=q
 elif p.is_file():
  q={'kind':'REGULAR_FILE','bytes':p.stat().st_size,'sha256':sha(p)};allold[str(p)]=q;total+=q['bytes']
prior=[]
for p in sorted(Path('evidence/field02/flight/runs').glob('*/request.json')):
 x=rd(p)
 if x.get('mode')=='sitl':prior.append({'run':p.parent.name,'path':str(p),'bytes':p.stat().st_size,'requestSha256':sha(p),'sourcePinsSha256':sha(p.parent/'source-pins.json')})
assert len(prior)==11
previous10={q['run']:q['sha256']for q in base['priorSITLRequests']}
assert all(next(q['requestSha256']for q in prior if q['run']==run)==h for run,h in previous10.items())
extra={str(old/n):{'bytes':(old/n).stat().st_size,'sha256':sha(old/n)}for n in ['final-artifact-fingerprints01.json','final-verification01.json','qa-final-preservation02.json','flight-pins.json','flight-pins02.json','flight-pins03.json']}
r={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'format':'aeris-beta06-independent-admission-preservation-v1','status':'PASS_BASELINE_CAPTURE'if not errors else'FAIL_OLD_EVIDENCE_DRIFT','historicalGroups':base['groups'],'historicalVerified':groups,'oldCLOCK05':{'inventoryFiles':580,'inventorySHA256':sha(old/'final-artifact-fingerprints01.json'),'inventoryFilesMap':inv['files'],'artifacts':extra},'entireImmutableField02':{'root':'evidence/field02','entries':len(allold),'regularFileBytes':total,'files':allold,'semantics':'Regular files exact SHA/bytes; symlinks bind literal link target plus dereferenced regular-file bytes when applicable. Does not fingerprint directory metadata or claim complete repository recovery.'},'permanentLegacySITLRequests':prior,'errors':errors,'limits':['Historical selected protected group SHA semantics follow seven retained negative-test symlinks, not original literal link provenance.','The 95 preexisting Git deletions are not restored or classified as new loss.','This new inventory does not assert all old evidence passed; old NOT_READY/failure records remain immutable.','No AP/server/UI/ADB/build or old path writes by independent QA. New beta namespace has separate256MiB declared budget; old512MiB cap unchanged.']}
p=E/'qa-preservation-before01.json';p.open('x').write(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(p),'status':r['status'],'historicalCounts':{k:q['files']for k,q in groups.items()},'clock05FinalFiles':580,'oldField02Entries':len(allold),'oldRegularBytes':total,'legacySITLRequests':len(prior),'errors':len(errors)}));assert not errors
