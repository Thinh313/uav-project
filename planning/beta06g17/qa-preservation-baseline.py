"""G17 prior-reference + closed G15/STABILITY16 protection and full old beta06 inventory."""
from pathlib import Path
import datetime,hashlib,json,os,stat
R=Path(__file__).resolve().parents[2];E=R/'evidence/beta06/generation17';H=lambda b:hashlib.sha256(b).hexdigest()
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
def exact(rows,keys):
 for n,r in rows.items():
  v=identity(R/n,'mtimeNs'in keys)
  for k in keys:
   if k in r:assert v.get(k)==r[k],n+':'+k
free=os.statvfs(R).f_bavail*os.statvfs(R).f_frsize;assert free>=20*2**30
base='evidence/beta06/generation15/qa-preservation-before15.json';old=previous(base);assert len(old)==12671;exact(old,['kind','mode','bytes','sha256','linkTarget'])
pins=read('evidence/beta06/generation15/flight-pins01.json');assert H(raw('evidence/beta06/generation15/flight-pins01.json'))=='71704519543544466fc12ac7ef8d09ba89d01f6de28b2d8f06893c20a51a4237';helper=read(pins['helperFreeze']['path']);assert H(raw(pins['helperFreeze']['path']))==pins['helperFreeze']['sha256'];assert len(pins['files'])==1414 and len(helper['files'])==26
for x in [pins,helper]:
 for n,h in x['files'].items():assert H(raw(n))==(h if isinstance(h,str)else h['sha256']),n
prior_history='evidence/beta06/generation15/qa-history-inventory01.json';hist=read(prior_history);assert len(hist['entries'])==8385;exact(hist['entries'],['kind','mode','bytes','sha256','mtimeNs'])
s16='evidence/stability16/handoff-manifest01.json';handoff=read(s16)
for n,r in handoff['files'].items():assert len(raw(n))==r['bytes']and H(raw(n))==r['sha256'],n
assert H(raw('evidence/stability16/qa-final01.json'))=='86d0d61cfa49e153e06fa1470def6774d1be062699f4a9091d868ab53ef8d3ab'
qa_s16=read('evidence/stability16/qa-preservation01.json');exact(qa_s16['closedG15Snapshot'],['kind','mode','bytes','sha256','linkTarget']);assert len(qa_s16['closedG15Snapshot'])==204
roots=['pilot/beta06g15','planning/beta06g15','evidence/beta06/generation15','pilot/stability16','planning/stability16','evidence/stability16'];delta={}
for n in roots:
 p=R/n;assert p.is_dir()and not p.is_symlink()
 for q in [p,*sorted(p.rglob('*'))]:
  name=str(q.relative_to(R))
  if name not in old:delta[name]=identity(q)
for n in [s16,*handoff['files']]:
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
b={'schema':'G17_PROTECTED_REFERENCE_PLUS_CLOSED_DELTA_V1','at':at,'status':'PASS_PRIOR_PROTECTED_AND_CLOSED_G15_STABILITY16','previousBaseline':{'path':base,'sha256':H(raw(base)),'paths':len(old),'allLstatModeBytesSHALiteralLinksRehashed':True},'deltaSnapshot':delta,'protectedPaths':len({**old,**delta}),'closedSTABILITY16Handoff':{'path':s16,'sha256':H(raw(s16)),'entries':len(handoff['files']),'report':'delivery/COMPLETION-STABILITY16.md','reportSha256':H(raw('delivery/COMPLETION-STABILITY16.md'))},'sourcePreparationChronology':'Authorized additive G17 preparation may occur concurrently, excluded. No before-all-source-effects claim.','provenance':{'known95Missing':'Exact preexisting paths enumerated in stability16/qa-preservation01; none in expected12671. No restore or whole repository/continuous presence claim.','prior125Recovery':'Original incident and authorized exact recovery remain protected by reference.','historicalActualBeforeG17':22,'G15ActualAP':0,'G15ActualHostBoot':1,'G15ActualAndroidBoot':1,'G15ActualDisposition':'Ground STALE_OBSERVATION before Connect/AP; later stale-quota guard closure. Earlier UI/HB initiatorUNKNOWN; later native ClamshellSleep directly retained.','G15NeverWrittenProofs':'qa-n1-fault01/native-prefix01/closure-summary01/final-runtime-summary01 remain absent after unchanged28GiB writer refusal. Do not manufacture a closed G15 final proof.','STABILITY16':'READY scoped source/mock only, not integrated Android/SITL; failedcounterexample/oldsource/unknowncauses retained.','newActualRuntimeByQA':0,'noOldFilesEdited':True}}
bref=put(E/'qa-preservation-before17.json',b)
history={}
for p in sorted((R/'evidence/beta06').rglob('*')):
 if p==E or E in p.parents:continue
 r=identity(p,True);assert r['kind']in ['REGULAR_FILE','DIRECTORY'];history[str(p.relative_to(R))]=r
inv={'schema':'G17_IMMUTABLE_HISTORY_V1','at':at,'root':'evidence/beta06','excludedScope':'evidence/beta06/generation17','entries':history,'totals':{'entries':len(history),'files':sum(r['kind']=='REGULAR_FILE'for r in history.values()),'directories':sum(r['kind']=='DIRECTORY'for r in history.values()),'bytes':sum(r['bytes']for r in history.values())},'preservationProvenance':{'referenceBaseline':bref['path'],'referenceBaselineSha256':bref['sha256'],'priorHistory':prior_history,'priorHistorySha256':H(raw(prior_history)),'closedG15AllCurrentEvidenceIncluded':True,'closedSTABILITY16OutsideBeta06ProtectedByBaselineAndPinnedOnUse':True,'noContinuousPresenceClaim':True}}
href=put(E/'qa-history-inventory01.json',inv)
print(json.dumps({'baseline':bref,'protectedPaths':b['protectedPaths'],'closedDelta':len(delta),'literalSymlinks':sum(r['kind']=='SYMLINK'for r in{**old,**delta}.values()),'history':href,'historyTotals':inv['totals'],'freeBytes':free,'oldWrites':0}))
