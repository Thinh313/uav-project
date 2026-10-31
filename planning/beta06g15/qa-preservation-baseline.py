"""G15: previous protected reference + closed G14/portfix, exact G5 data fork."""
from pathlib import Path
import datetime,hashlib,json,os,stat
R=Path(__file__).resolve().parents[2];E=R/'evidence/beta06/generation15';H=lambda b:hashlib.sha256(b).hexdigest()
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
base='evidence/beta06/generation14/qa-preservation-before14.json';old=previous(base);assert len(old)==12497
for name,row in old.items():
 got=identity(R/name)
 for k in ['kind','mode','bytes','sha256','linkTarget']:
  if k in row:assert got.get(k)==row[k],name+':'+k
cp='evidence/beta06/generation14/qa-final-completion01.json';assert H(raw(cp))=='c5074936664e865a4dc0f7e89dd6ae25ae1be768544b74a28adf3b19a431fc62';completion=read(cp)
for name,row in completion['files'].items():assert len(raw(name))==row['bytes']and H(raw(name))==row['sha256'],name
assert completion['actualHosts']==completion['actualAndroidBoots']==completion['actualAP']==0
report='delivery/COMPLETION-BETA06-G14.md';assert H(raw(report))=='4b81c1c6891554144424278861fe7a9c390cff49a06e57e2028b685bb2cb1cc7'
pins=read('evidence/beta06/generation14/flight-pins01.json');hp=pins['helperFreeze']['path'];helper=read(hp)
assert H(raw(hp))==pins['helperFreeze']['sha256']and hp.endswith('native-helper-freeze02.json')
assert len(pins['files'])==1332 and len(helper['files'])==26
for inv in [pins,helper]:
 for name,h in inv['files'].items():assert H(raw(name))==(h if isinstance(h,str)else h['sha256']),name
prior_history='evidence/beta06/generation14/qa-history-inventory01.json';oh=read(prior_history);assert len(oh['entries'])==8285
for name,row in oh['entries'].items():
 got=identity(R/name,True)
 for k in ['kind','mode','bytes','sha256','mtimeNs']:assert got[k]==row[k],name+':'+k
roots=['pilot/beta06g14','planning/beta06g14','evidence/beta06/generation14','planning/port14fix','evidence/beta06-port14fix'];delta={}
for name in roots:
 p=R/name;assert p.is_dir()and not p.is_symlink()
 for q in [p,*sorted(p.rglob('*'))]:
  n=str(q.relative_to(R))
  if n not in old:delta[n]=identity(q)
for n in [cp,report,*completion['files']]:
 if n not in old:delta[n]=identity(R/n)
E.mkdir(exist_ok=True);assert not E.is_symlink()
def put(p,x):
 b=json.dumps(x,separators=(',',':'),allow_nan=False).encode()+b'\n'
 with p.open('xb')as f:f.write(b);f.flush();os.fsync(f.fileno())
 fd=os.open(p.parent,os.O_RDONLY)
 try:os.fsync(fd)
 finally:os.close(fd)
 return{'path':str(p.relative_to(R)),'sha256':H(b),'bytes':len(b)}
at=datetime.datetime.now(datetime.timezone.utc).isoformat()
b={'schema':'G15_PROTECTED_REFERENCE_PLUS_CLOSED_DELTA_V1','at':at,'status':'PASS_PRIOR_PROTECTED_AND_CLOSED_G14_PORTFIX','previousBaseline':{'path':base,'sha256':H(raw(base)),'paths':len(old),'allLstatModeBytesSHALiteralLinksRehashed':True},'deltaSnapshot':delta,'protectedPaths':len({**old,**delta}),'closedG14Completion':{'path':cp,'sha256':H(raw(cp)),'report':report,'reportSha256':H(raw(report))},'sourcePreparationChronology':'Root-authorized additive G15 preparation excluded; not a before-all-source-effects snapshot.','provenance':{'known95Missing':'Prior references retained; not whole repository or continuous presence.','prior125Recovery':'Authorized exact recovery and original incident remain protected.','historicalActualBeforeG15':22,'G14ActualHosts':0,'G14ActualAndroid':0,'G14ActualAP':0,'G14Failure':'Strict kernel address grammar before host Popen; original offending row UNKNOWN.','portFix':'Independent23 fake-only and Builder passive capture distinct; no actual G14retry.','noOldFilesEdited':True}}
bref=put(E/'qa-preservation-before15.json',b)
oldcopy=read('evidence/beta06/generation14/workspace-copy01.json');rows=[];free=os.statvfs(R).f_bavail*os.statvfs(R).f_frsize;assert free>=20*2**30
for row in oldcopy['files']:
 src=R/row['source'];assert src.is_file()and not src.is_symlink();data=src.read_bytes();assert len(data)==row['bytes']and H(data)==row['sha256']
 rel=src.relative_to(R/'evidence/beta06/generation05/workspace01');dst=E/'workspace01'/rel;dst.parent.mkdir(parents=True,exist_ok=True)
 for parent in [dst.parent,*dst.parents]:
  assert not parent.is_symlink()
  if parent==E:break
 fd=os.open(dst,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,stat.S_IMODE(src.lstat().st_mode))
 with os.fdopen(fd,'wb')as f:f.write(data);f.flush();os.fsync(f.fileno())
 assert H(dst.read_bytes())==row['sha256'];rows.append({'source':row['source'],'copy':str(dst.relative_to(R)),'bytes':len(data),'sha256':H(data)})
assert len(rows)==20 and sum(r['bytes']for r in rows)==870221
for p in sorted([E/'workspace01',*(q for q in(E/'workspace01').rglob('*')if q.is_dir())],key=lambda p:len(p.parts),reverse=True):
 fd=os.open(p,os.O_RDONLY)
 try:os.fsync(fd)
 finally:os.close(fd)
copy={'schema':'G15_EXACT_CLOSED_WORKSPACE_COPY_V1','at':at,'mode':'EXACT_CLOSED_DATA_FORK_NOT_PROJECT_COPY','source':'evidence/beta06/generation05/workspace01','destination':'evidence/beta06/generation15/workspace01','fileCount':20,'bytes':870221,'files':rows,'baseline':bref,'firstWriterRequired':{'writerLockAbsent':not(E/'workspace01/writer.lock').exists(),'exclusiveRootPermitRequired':True},'actualG15Execution':False,'noAuthorityRestoration':True,'freeBytesBeforeFork':free};cref=put(E/'workspace-copy01.json',copy)
hist={}
for p in sorted((R/'evidence/beta06').rglob('*')):
 if p==E or E in p.parents:continue
 r=identity(p,True);assert r['kind']in ['REGULAR_FILE','DIRECTORY'];hist[str(p.relative_to(R))]=r
inventory={'schema':'G15_IMMUTABLE_HISTORY_V1','at':at,'root':'evidence/beta06','excludedScope':'evidence/beta06/generation15','entries':hist,'totals':{'entries':len(hist),'files':sum(r['kind']=='REGULAR_FILE'for r in hist.values()),'directories':sum(r['kind']=='DIRECTORY'for r in hist.values()),'bytes':sum(r['bytes']for r in hist.values())},'preservationProvenance':{'referenceBaseline':bref['path'],'referenceBaselineSha256':bref['sha256'],'priorHistory':prior_history,'priorHistorySha256':H(raw(prior_history)),'closedG14FinalRuntimeSha256':H(raw('evidence/beta06/generation14/qa-final-runtime-summary01.json')),'closedPortfixProtectedInBaselineAndPinnedOnUse':True,'noContinuousPresenceClaim':True}};href=put(E/'qa-history-inventory01.json',inventory)
print(json.dumps({'baseline':bref,'protectedPaths':b['protectedPaths'],'closedDelta':len(delta),'copy':cref,'history':href,'historyTotals':inventory['totals'],'oldWrites':0}))
