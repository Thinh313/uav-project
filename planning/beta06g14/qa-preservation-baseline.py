"""G14 prior-reference + closed G13/prototype protection and exact original G5 data fork."""
from pathlib import Path
import datetime,hashlib,json,os,stat
R=Path(__file__).resolve().parents[2];E=R/'evidence/beta06/generation14';H=lambda b:hashlib.sha256(b).hexdigest()
def raw(p):return(R/p).read_bytes()
def read(p):return json.loads(raw(p))
def previous(p):
 x=read(p)
 if'snapshot'in x:return x['snapshot']
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
assert os.statvfs(R).f_bavail*os.statvfs(R).f_frsize>=20*2**30
base='evidence/beta06/generation13/qa-preservation-before13.json';old=previous(base);assert len(old)==11564
for name,row in old.items():
 got=identity(R/name)
 for key in ['kind','mode','bytes','sha256','linkTarget']:
  if key in row:assert got.get(key)==row[key],name+':'+key
completion_path='evidence/beta06/generation13/qa-final-completion01.json'
assert H(raw(completion_path))=='dee87cedad8afe5ace29154b636aba92eb89f248c5fd685be3799959a3f8df78'
completion=read(completion_path);assert len(completion['files'])==25
for name,row in completion['files'].items():assert len(raw(name))==row['bytes']and H(raw(name))==row['sha256'],name
report='delivery/COMPLETION-BETA06-G13.md';assert H(raw(report))=='d1b017efa7c50c070cc38dc88dabed97f2a937e1110fe51a603361935ef93d5a'
pins=read('evidence/beta06/generation13/flight-pins01.json');helper=read('evidence/beta06/generation13/native-helper-freeze01.json');assert len(pins['files'])==1247 and len(helper['files'])==28
for inventory in [pins,helper]:
 for name,h in inventory['files'].items():assert H(raw(name))==(h if isinstance(h,str)else h['sha256']),name
oldhistory=read('evidence/beta06/generation13/qa-history-inventory01.json');assert len(oldhistory['entries'])==7482
for name,row in oldhistory['entries'].items():
 got=identity(R/name,True)
 for key in ['kind','mode','bytes','sha256','mtimeNs']:assert got[key]==row[key],name+':'+key
roots=['pilot/beta06g13','planning/beta06g13','evidence/beta06/generation13','pilot/heartbeat13fix','planning/heartbeat13fix','evidence/beta06-heartbeat13fix','pilot/heartbeat13sidecarfix','planning/heartbeat13sidecarfix','evidence/beta06-heartbeat13sidecarfix']
delta={}
for name in roots:
 p=R/name;assert p.is_dir()and not p.is_symlink()
 for q in [p,*sorted(p.rglob('*'))]:
  name=str(q.relative_to(R))
  if name not in old:delta[name]=identity(q)
for name in [report,completion_path,*completion['files']]:
 if name not in old:delta[name]=identity(R/name)
request='evidence/beta06/generation13/flight/runs/sa79cb8c8ee88488b9c8b/request.json'
assert H(raw(request))=='595a5047aafcf3bce8e9743a763ec1f3b58b46177b87d3998f366640281f78e0'
assert read(request)['mode']=='sitl'
E.mkdir(exist_ok=True);assert not E.is_symlink()
def put(p,value):
 b=json.dumps(value,separators=(',',':'),allow_nan=False).encode()+b'\n'
 with p.open('xb')as f:f.write(b);f.flush();os.fsync(f.fileno())
 fd=os.open(p.parent,os.O_RDONLY)
 try:os.fsync(fd)
 finally:os.close(fd)
 return{'path':str(p.relative_to(R)),'sha256':H(b),'bytes':len(b)}
at=datetime.datetime.now(datetime.timezone.utc).isoformat()
baseline={'schema':'G14_PROTECTED_REFERENCE_PLUS_CLOSED_DELTA_V1','at':at,'status':'PASS_PRIOR_PROTECTED_AND_CLOSED_G13_PROTOTYPES','previousBaseline':{'path':base,'sha256':H(raw(base)),'paths':len(old),'allLstatModeBytesSHALiteralLinksRehashed':True},'deltaSnapshot':delta,'protectedPaths':len({**old,**delta}),'closedG13Completion':{'path':completion_path,'sha256':H(raw(completion_path)),'report':report,'reportSha256':H(raw(report))},'sourcePreparationChronology':'Root-authorized additive G14 preparation may run in parallel; excluded. No before-all-new-source-effects claim.','provenance':{'known95Missing':'Retained by prior references; not a whole-repository or continuous-presence claim.','prior125Recovery':'Original incident and authorized exact recovery remain protected.','historicalActualBeforeG14':22,'G13ActualAPRequests':1,'G13Request':{'path':request,'sha256':H(raw(request))},'G13ActualDisposition':'N1 raw/standalone media/capture/index partial; required sidecar failed. F1/N2/F2/restart/cold27 not run. Separate repaired sidecar source/mock only.','G13NumericExits':'Root closure and actual controller events record host56792/helper56801/emulator56859/controller56740 exit0; no inference from disappearance.','noOldFilesEdited':True}}
bref=put(E/'qa-preservation-before14.json',baseline)
# Copy only the original closed G5 fixture, never the consumed G13 fork.
prior_copy=read('evidence/beta06/generation13/workspace-copy01.json');rows=[];free=os.statvfs(R).f_bavail*os.statvfs(R).f_frsize;assert free>=20*2**30
for row in prior_copy['files']:
 src=R/row['source'];assert src.is_file()and not src.is_symlink();b=src.read_bytes();assert len(b)==row['bytes']and H(b)==row['sha256']
 rel=src.relative_to(R/'evidence/beta06/generation05/workspace01');dst=E/'workspace01'/rel;dst.parent.mkdir(parents=True,exist_ok=True)
 for parent in [dst.parent,*dst.parents]:
  assert not parent.is_symlink()
  if parent==E:break
 fd=os.open(dst,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,stat.S_IMODE(src.lstat().st_mode))
 with os.fdopen(fd,'wb')as f:f.write(b);f.flush();os.fsync(f.fileno())
 assert H(dst.read_bytes())==row['sha256'];rows.append({'source':row['source'],'copy':str(dst.relative_to(R)),'bytes':len(b),'sha256':H(b)})
assert len(rows)==20 and sum(r['bytes']for r in rows)==870221
for p in sorted([E/'workspace01',*(q for q in(E/'workspace01').rglob('*')if q.is_dir())],key=lambda p:len(p.parts),reverse=True):
 fd=os.open(p,os.O_RDONLY)
 try:os.fsync(fd)
 finally:os.close(fd)
copy={'schema':'G14_EXACT_CLOSED_WORKSPACE_COPY_V1','at':at,'mode':'EXACT_CLOSED_DATA_FORK_NOT_PROJECT_COPY','source':'evidence/beta06/generation05/workspace01','destination':'evidence/beta06/generation14/workspace01','fileCount':20,'bytes':870221,'files':rows,'baseline':bref,'firstWriterRequired':{'writerLockAbsent':not(E/'workspace01/writer.lock').exists(),'exclusiveRootPermitRequired':True},'actualG14Execution':False,'noAuthorityRestoration':True,'freeBytesBeforeFork':free}
cref=put(E/'workspace-copy01.json',copy)
history={}
for p in sorted((R/'evidence/beta06').rglob('*')):
 if p==E or E in p.parents:continue
 row=identity(p,True);assert row['kind']in ['REGULAR_FILE','DIRECTORY'];history[str(p.relative_to(R))]=row
inventory={'schema':'G14_IMMUTABLE_HISTORY_V1','at':at,'root':'evidence/beta06','excludedScope':'evidence/beta06/generation14','entries':history,'totals':{'entries':len(history),'files':sum(r['kind']=='REGULAR_FILE'for r in history.values()),'directories':sum(r['kind']=='DIRECTORY'for r in history.values()),'bytes':sum(r['bytes']for r in history.values())},'preservationProvenance':{'referenceBaseline':bref['path'],'referenceBaselineSha256':bref['sha256'],'priorHistory':'evidence/beta06/generation13/qa-history-inventory01.json','priorHistorySha256':H(raw('evidence/beta06/generation13/qa-history-inventory01.json')),'closedG13FinalRuntimeSha256':H(raw('evidence/beta06/generation13/qa-final-runtime-summary01.json')),'closedPrototypesProtectedInBaselineAndPinnedOnUse':True,'noContinuousPresenceClaim':True}}
href=put(E/'qa-history-inventory01.json',inventory)
print(json.dumps({'baseline':bref,'protectedPaths':baseline['protectedPaths'],'closedDelta':len(delta),'copy':cref,'history':href,'historyTotals':inventory['totals'],'oldWrites':0}))
