"""Independent, additive STABILITY16 preservation audit. Never restores/mutates old inputs."""
from pathlib import Path
import datetime,hashlib,json,os,stat,subprocess
R=Path(__file__).resolve().parents[2];P=Path(__file__).resolve().parent;E=R/'evidence/stability16';H=lambda b:hashlib.sha256(b).hexdigest()
def raw(p):return(R/p).read_bytes()
def read(p):return json.loads(raw(p))
def previous(p):
 x=read(p)
 if 'snapshot'in x:return x['snapshot']
 assert H(raw(x['previousBaseline']['path']))==x['previousBaseline']['sha256']
 return{**previous(x['previousBaseline']['path']),**x['deltaSnapshot']}
def identity(p,mtime=False):
 s=p.lstat();kind='SYMLINK'if stat.S_ISLNK(s.st_mode)else'DIRECTORY'if stat.S_ISDIR(s.st_mode)else'REGULAR_FILE'
 assert kind!='REGULAR_FILE'or stat.S_ISREG(s.st_mode)
 row={'kind':kind,'mode':oct(stat.S_IMODE(s.st_mode)),'bytes':0,'sha256':None}
 if kind!='DIRECTORY':b=p.read_bytes();row.update(bytes=len(b),sha256=H(b))
 if kind=='SYMLINK':row['linkTarget']=os.readlink(p)
 if mtime:row['mtimeNs']=str(s.st_mtime_ns)
 return row
def compare(rows,keys):
 missing=[];mismatch=[];errors=[]
 for n,want in rows.items():
  try:got=identity(R/n,'mtimeNs'in keys)
  except FileNotFoundError:missing.append(n);continue
  except Exception as ex:errors.append({'path':n,'error':type(ex).__name__+':'+str(ex)});continue
  bad={k:{'expected':want.get(k),'actual':got.get(k)}for k in keys if k in want and got.get(k)!=want.get(k)}
  if bad:mismatch.append({'path':n,'fields':bad})
 return{'expectedPaths':len(rows),'exactPaths':len(rows)-len(missing)-len(mismatch)-len(errors),'missing':missing,'mismatch':mismatch,'readErrors':errors}
base='evidence/beta06/generation15/qa-preservation-before15.json';rows=previous(base);assert len(rows)==12671
protected=compare(rows,['kind','mode','bytes','sha256','linkTarget'])
pins_path='evidence/beta06/generation15/flight-pins01.json';pins=read(pins_path);assert H(raw(pins_path))=='71704519543544466fc12ac7ef8d09ba89d01f6de28b2d8f06893c20a51a4237'
helper_path=pins['helperFreeze']['path'];helper=read(helper_path);assert H(raw(helper_path))==pins['helperFreeze']['sha256'];assert len(pins['files'])==1414 and len(helper['files'])==26
def file_rows(x):return{n:{'kind':'REGULAR_FILE','sha256':h if isinstance(h,str)else h['sha256']}for n,h in x['files'].items()}
pincheck=compare(file_rows(pins),['kind','sha256']);helpercheck=compare(file_rows(helper),['kind','sha256'])
hp='evidence/beta06/generation15/qa-history-inventory01.json';history=read(hp);assert len(history['entries'])==8385
historycheck=compare(history['entries'],['kind','mode','bytes','sha256','mtimeNs'])
deleted=subprocess.check_output(['git','ls-files','--deleted','-z'],cwd=R).decode().rstrip('\x00').split('\x00');deleted=sorted(n for n in deleted if n)
assert len(deleted)==95,'CURRENT_TRACKED_LOSS_COUNT_CHANGED_REVIEW_REQUIRED'
git_missing_expected=[]
for n in deleted:
 assert not os.path.lexists(R/n),'GIT_DELETED_PATH_EXISTS'
 if n in rows:git_missing_expected.append(n)
categories={}
for n in deleted:categories[n.split('/')[0]]=categories.get(n.split('/')[0],0)+1
snapshot={}
for root in ['pilot/beta06g15','planning/beta06g15','evidence/beta06/generation15']:
 p=R/root
 for q in [p,*sorted(p.rglob('*'))]:snapshot[str(q.relative_to(R))]=identity(q)
planned=['qa-n1-fault01.json','qa-native-prefix01.json','qa-closure-summary01.json','qa-final-runtime-summary01.json']
free=os.statvfs(R).f_bavail*os.statvfs(R).f_frsize;assert free>=20*2**30,'DISK_FLOOR20_WRITES_STOP'
ok=all(not c['missing']and not c['mismatch']and not c['readErrors']for c in[protected,pincheck,helpercheck,historycheck])
report={'schema':'STABILITY16_INDEPENDENT_PRESERVATION_V1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_DECLARED_PROTECTED_INPUTS_WITH_PREEXISTING_GIT95_LOSSES'if ok else'FAIL_PROTECTED_INPUT_DRIFT','baseline':{'path':base,'sha256':H(raw(base))},'protected':protected,'literalSymlinkCount':sum(r['kind']=='SYMLINK'for r in rows.values()),'pins':{'path':pins_path,'sha256':H(raw(pins_path)),**pincheck},'helpers':{'path':helper_path,'sha256':H(raw(helper_path)),**helpercheck},'history':{'path':hp,'sha256':H(raw(hp)),**historycheck},'gitTrackedDeletions':{'count':len(deleted),'paths':deleted,'categories':categories,'intersectionWithExpectedProtectedBaseline':git_missing_expected,'preexistingEvidence':'These 95 Git-deleted paths were already enumerated in the G15 task/session before STABILITY16. Current exact paths recorded here; no responsible actor or deletion time inferred.','notWholeRepositoryIntact':True,'noRestorationPerformed':True},'closedG15Snapshot':snapshot,'G15FinalProofs':{'currentlyPresent':{n:(R/'evidence/beta06/generation15'/n).exists()for n in planned},'limit':'Absence of never-written final receipts is not a new protected-file deletion. G15 unchanged28GiB writer refused before output, as retained tool/session evidence; this additive task may write only above20GiB.'},'freeBytesBeforeWrite':free,'requiredFloorBytes':20*2**30,'noActualRuntimeByQA':True,'oldInputWrites':0,'scratchCreated':False,'recipe':{'path':str(Path(__file__).relative_to(R)),'sha256':H(Path(__file__).read_bytes())}}
b=(json.dumps(report,indent=2)+'\n').encode();assert len(b)<1024*1024
scope_roots=[P,R/'pilot/stability16',E];total=sum(p.stat().st_size for root in scope_roots if root.exists()for p in root.rglob('*')if p.is_file());assert total+len(b)<=32*2**20
out=E/'qa-preservation01.json'
with out.open('xb')as f:f.write(b);f.flush();os.fsync(f.fileno())
fd=os.open(E,os.O_RDONLY)
try:os.fsync(fd)
finally:os.close(fd)
print(json.dumps({'path':str(out.relative_to(R)),'sha256':H(b),'bytes':len(b),'status':report['status'],'protectedExpected':len(rows),'protectedMissing':len(protected['missing']),'protectedMismatch':len(protected['mismatch']),'gitMissing':len(deleted),'gitMissingInProtectedBaseline':git_missing_expected,'pins':pincheck,'helpers':helpercheck,'historyExpected':len(history['entries']),'historyMissing':len(historycheck['missing']),'historyMismatch':len(historycheck['mismatch']),'G15ClosedSnapshotPaths':len(snapshot),'freeBytes':free}))
