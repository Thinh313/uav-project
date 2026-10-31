from pathlib import Path
import json,hashlib,os,stat,datetime,sys,subprocess
R=Path(__file__).resolve().parents[2]; E=R/'evidence/workbench01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads((R/p).read_text())
def previous(p):
 x=read(p)
 if 'snapshot' in x:return x['snapshot']
 ref=x['previousBaseline'];assert sha(R/ref['path'])==ref['sha256']
 return {**previous(ref['path']),**x['deltaSnapshot']}
def identity(p):
 s=p.lstat(); k='SYMLINK' if p.is_symlink() else 'DIRECTORY' if p.is_dir() else 'REGULAR_FILE'
 d={'kind':k,'mode':oct(stat.S_IMODE(s.st_mode)),'bytes':0,'sha256':None}
 if k!='DIRECTORY':d.update(bytes=len(p.read_bytes()),sha256=sha(p),mtimeNs=str(s.st_mtime_ns))
 if k=='SYMLINK':d['linkTarget']=os.readlink(p)
 return d
assert os.statvfs(R).f_bavail*os.statvfs(R).f_frsize>=20*2**30
base='evidence/beta06/generation17/qa-preservation-before17.json'; rows=previous(base)
refs=[base,'evidence/beta06/generation17/qa-history-inventory01.json','evidence/beta06/generation17/root-handoff-manifest01.json']
h=read(refs[1]); rows.update(h['entries'])
for n,v in read(refs[2])['files'].items():rows[n]={'sha256':v['sha256'],'bytes':v['bytes']}
for n in refs:rows[n]={'sha256':sha(R/n)}
reuse=['pilot/mapping51/planner.mjs','pilot/mapping51/readiness.mjs','pilot/mapping51/kml.py','pilot/mapping51/common.mjs','pilot/mapping51/fixtures.mjs','app/core/survey.mjs','pilot/mission55/geo.mjs']
for n in reuse:rows.setdefault(n,{'sha256':sha(R/n)})
now={};fail=[]
for n,v in rows.items():
 try:
  a=identity(R/n)
  for k in ['kind','mode','bytes','sha256','linkTarget','mtimeNs']:
   if k in v and (k!='mtimeNs' or v.get('kind')!='DIRECTORY') and a.get(k)!=v[k]:fail.append(n+':'+k)
  now[n]=a
 except Exception as e:fail.append(n+':'+str(e))
assert not fail, '\n'.join(fail[:20])
path=E/(sys.argv[2] if len(sys.argv)>2 else ('preservation-before.json' if sys.argv[1]=='before' else 'preservation-after.json'))
result={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS','originalProtectedCount':len(previous(base)),'historyEntries':len(h['entries']),'checkedUnion':len(now),'bytes':sum(v['bytes'] for v in now.values()),'references':{n:sha(R/n) for n in refs},'reuse':{n:sha(R/n) for n in reuse},'freeBytes':os.statvfs(R).f_bavail*os.statvfs(R).f_frsize,'scope':'No continuous-presence claim; preexisting Git missing paths outside baseline not restored.'}
if sys.argv[1]=='before':result['snapshot']=now
else:
 before=read('evidence/workbench01/preservation-before.json')
 for n,v in before['snapshot'].items():
  assert now[n]==v,n
 result['beforeSha256']=sha(E/'preservation-before.json')
with path.open('x') as f:json.dump(result,f,separators=(',',':'))
print(json.dumps({k:v for k,v in result.items() if k!='snapshot'}))
