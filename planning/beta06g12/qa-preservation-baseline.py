"""Bounded G12 by-reference protection, immutable history inventory and 20-file data fork."""
from pathlib import Path
import datetime,hashlib,json,os,stat
R=Path(__file__).resolve().parents[2];E=R/'evidence/beta06/generation12';H=lambda b:hashlib.sha256(b).hexdigest()
def raw(p):return(R/p).read_bytes()
def read(p):return json.loads(raw(p))
def previous(p):
 x=read(p)
 if'snapshot'in x:return x['snapshot']
 assert H(raw(x['previousBaseline']['path']))==x['previousBaseline']['sha256'];return{**previous(x['previousBaseline']['path']),**x['deltaSnapshot']}
def identity(p,mtime=False):
 s=p.lstat();kind='SYMLINK'if stat.S_ISLNK(s.st_mode)else'DIRECTORY'if stat.S_ISDIR(s.st_mode)else'REGULAR_FILE';assert kind!='REGULAR_FILE'or stat.S_ISREG(s.st_mode)
 v={'kind':kind,'mode':oct(stat.S_IMODE(s.st_mode)),'bytes':0,'sha256':None}
 if kind!='DIRECTORY':b=p.read_bytes();v.update(bytes=len(b),sha256=H(b))
 if kind=='SYMLINK':v['linkTarget']=os.readlink(p)
 if mtime:v['mtimeNs']=str(s.st_mtime_ns)
 return v
base='evidence/beta06/generation11/qa-preservation-before11.json';old=previous(base);assert len(old)==10001
for n,row in old.items():
 actual=identity(R/n)
 for k in ['kind','mode','bytes','sha256','linkTarget']:
  if k in row:assert actual.get(k)==row[k],n+':'+k
# G11 and its additive ground11fix proposal close before this snapshot. Current G12 preparation is excluded by contract.
delta={};roots=['pilot/beta06g11','planning/beta06g11','evidence/beta06/generation11','planning/ground11fix']
for n in roots:
 p=R/n;assert p.is_dir()and not p.is_symlink()
 for q in [p,*sorted(p.rglob('*'))]:
  rel=str(q.relative_to(R))
  if rel not in old:delta[rel]=identity(q)
report='delivery/COMPLETION-BETA06-G11.md';assert(R/report).is_file();delta[report]=identity(R/report)
completion=read('evidence/beta06/generation11/qa-final-completion01.json')
assert H(raw('evidence/beta06/generation11/qa-final-completion01.json')).startswith('18bb6148')
for path,row in completion['files'].items():assert len(raw(path))==row['bytes']and H(raw(path))==row['sha256']
pins=read('evidence/beta06/generation11/flight-pins01.json');helpers=read('evidence/beta06/generation11/native-helper-freeze01.json');assert len(pins['files'])==1071 and len(helpers['files'])==25
for inventory in [pins,helpers]:
 for n,h in inventory['files'].items():assert H(raw(n))==(h if isinstance(h,str)else h['sha256']),n
oldhistory=read('evidence/beta06/generation11/qa-history-inventory01.json');assert len(oldhistory['entries'])==6052
for n,row in oldhistory['entries'].items():
 actual=identity(R/n,mtime=True)
 for k in ['kind','mode','bytes','sha256','mtimeNs']:assert actual[k]==row[k],n+':'+k
E.mkdir(exist_ok=True);assert not E.is_symlink()
def put(path,value):
 b=json.dumps(value,separators=(',',':'),allow_nan=False).encode()+b'\n'
 with path.open('xb')as f:f.write(b);f.flush();os.fsync(f.fileno())
 fd=os.open(path.parent,os.O_RDONLY)
 try:os.fsync(fd)
 finally:os.close(fd)
 return{'path':str(path.relative_to(R)),'sha256':H(b),'bytes':len(b)}
at=datetime.datetime.now(datetime.timezone.utc).isoformat();baseline={'schema':'G12_PROTECTED_REFERENCE_PLUS_CLOSED_DELTA_V1','at':at,'status':'PASS_ALL_PRIOR_PROTECTED_BYTES_BEFORE_G12_RUNTIME','sourcePreparationChronology':'Additive new G12 preparation may be parallel by Root authorization; excluded from old-root snapshot. No before-all-source-effects claim.','previousBaseline':{'path':base,'sha256':H(raw(base)),'paths':len(old),'allLstatModeBytesSHALiteralLinksRehashed':True},'deltaSnapshot':delta,'protectedPaths':len({**old,**delta}),'closedG11Completion':{'path':'evidence/beta06/generation11/qa-final-completion01.json','sha256':H(raw('evidence/beta06/generation11/qa-final-completion01.json')),'report':report,'reportSha256':H(raw(report))},'provenance':{'known95HistoricallyMissing':'Retained by prior baseline references; not a whole-repository continuity claim.','prior125ExactRecovery':'Prior incident and authorized exact recovery remain protected, no continuous-presence claim.','G11ActualAP':0,'G11AndroidBoots':1,'historicalActualRequests':19,'hostChildNumericExit':'G11 managed host16766 exit0 recorded; helper numeric exit NOT_RECORDED. G10 qualification preserved by reference.','noOldFilesEdited':True,'qaCommandCorrection':'Initial read-only ENOENT used stale before10 basename in generation11; corrected to before11 before any output or fork effects.'}};bref=put(E/'qa-preservation-before12.json',baseline)
# Exact original G5 fixture only, never consumed G11 workspace.
copyPrior=read('evidence/beta06/generation11/workspace-copy01.json');rows=[];free=os.statvfs(R).f_bavail*os.statvfs(R).f_frsize;assert free>=20*2**30,'DISK_FLOOR_BEFORE_BOUNDED_DATA_FORK'
for row in copyPrior['files']:
 src=R/row['source'];assert src.is_file()and not src.is_symlink();b=src.read_bytes();assert len(b)==row['bytes']and H(b)==row['sha256'];rel=src.relative_to(R/'evidence/beta06/generation05/workspace01');dst=E/'workspace01'/rel;dst.parent.mkdir(parents=True,exist_ok=True)
 for ancestor in [dst.parent,*dst.parents]:
  assert not ancestor.is_symlink()
  if ancestor==E:break
 fd=os.open(dst,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,stat.S_IMODE(src.lstat().st_mode))
 try:
  with os.fdopen(fd,'wb')as f:f.write(b);f.flush();os.fsync(f.fileno())
 finally:pass
 assert H(dst.read_bytes())==row['sha256'];rows.append({'source':row['source'],'copy':str(dst.relative_to(R)),'bytes':len(b),'sha256':H(b)})
assert len(rows)==20 and sum(r['bytes']for r in rows)==870221
for d in sorted([E/'workspace01',*(p for p in(E/'workspace01').rglob('*')if p.is_dir())],key=lambda x:len(x.parts),reverse=True):
 fd=os.open(d,os.O_RDONLY)
 try:os.fsync(fd)
 finally:os.close(fd)
copy={'schema':'G12_EXACT_CLOSED_WORKSPACE_COPY_V1','at':at,'mode':'EXACT_CLOSED_DATA_FORK_NOT_PROJECT_COPY','source':'evidence/beta06/generation05/workspace01','destination':'evidence/beta06/generation12/workspace01','fileCount':20,'bytes':870221,'files':rows,'baseline':bref,'firstWriterRequired':{'writerLockAbsent':not(E/'workspace01/writer.lock').exists(),'exclusiveRootPermitRequired':True},'actualG12Execution':False,'noAuthorityRestoration':True,'freeBytesBeforeFork':free};cref=put(E/'workspace-copy01.json',copy)
history={};root=R/'evidence/beta06'
for p in sorted(root.rglob('*')):
 if p==E or E in p.parents:continue
 row=identity(p,mtime=True);assert row['kind']in ['REGULAR_FILE','DIRECTORY'],'NO_SYMLINK_HISTORICAL_SCOPE';history[str(p.relative_to(R))]=row
inv={'schema':'G12_IMMUTABLE_HISTORY_V1','at':at,'root':'evidence/beta06','excludedScope':'evidence/beta06/generation12','entries':history,'totals':{'entries':len(history),'files':sum(v['kind']=='REGULAR_FILE'for v in history.values()),'directories':sum(v['kind']=='DIRECTORY'for v in history.values()),'bytes':sum(v['bytes']for v in history.values())},'preservationProvenance':{'referenceBaseline':bref['path'],'referenceBaselineSha256':bref['sha256'],'priorHistory':'evidence/beta06/generation11/qa-history-inventory01.json','priorHistorySha256':H(raw('evidence/beta06/generation11/qa-history-inventory01.json')),'closedG11FinalRuntimeSha256':H(raw('evidence/beta06/generation11/qa-final-runtime-summary01.json')),'ground11fixPreserved':True,'noContinuousPresenceClaim':True}};href=put(E/'qa-history-inventory01.json',inv)
print(json.dumps({'baseline':bref,'protectedPaths':baseline['protectedPaths'],'closedDelta':len(delta),'copy':cref,'history':href,'historyTotals':inv['totals'],'oldWrites':0}))
