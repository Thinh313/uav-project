from pathlib import Path
import json,hashlib,stat,os,sys,datetime,shutil,subprocess
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check():
 refs={};observed={};gaps={};totals={}
 files=['evidence/workbench01/preservation-before.json','evidence/workbench02/handoff-java01.json','evidence/betaworkbench03/handoff-final01.json','evidence/betaworkbench04/handoff-final01.json','evidence/betaworkbench05/handoff-final01.json']
 for f in files:
  p=R/f
  if not p.exists():continue
  refs[f]=sha(p);d=json.loads(p.read_text());inv=d.get('snapshot',d.get('inventory',{}));totals[f]=len(inv)
  for n,v in inv.items():
   p=R/n
   if not p.exists()and not p.is_symlink():observed[n]={'kind':'MISSING'};gaps[n]={'expected':v,'state':'MISSING_AT_COACH01_ENTRY'};continue
   s=p.lstat();kind='SYMLINK'if p.is_symlink()else'DIRECTORY'if p.is_dir()else'REGULAR_FILE';a={'kind':kind,'mode':oct(stat.S_IMODE(s.st_mode)),'bytes':0,'sha256':None}
   if kind=='REGULAR_FILE':a.update(bytes=s.st_size,sha256=sha(p),mtimeNs=str(s.st_mtime_ns))
   if kind=='SYMLINK':
    a['linkTarget']=os.readlink(p)
    if p.is_file():a.update(targetBytes=p.stat().st_size,sha256=sha(p))
   if v.get('sha256')and a['sha256']!=v['sha256']:raise Exception('PROTECTED_CONTENT_DRIFT '+n)
   observed[n]=a
 status=subprocess.run(['git','status','--porcelain','--untracked-files=no'],cwd=R,capture_output=True,text=True,check=True).stdout
 return {'status':'UNCHANGED_PRESENT_BYTES_WITH_PREEXISTING_PATH_GAPS','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'overlappingInventories':totals,'references':refs,'observed':observed,'entryMissing':gaps,'trackedStatus':status,'continuousPresenceClaim':False,'restorationAttempted':False,'freeBytes':shutil.disk_usage(R).free}
d=check();phase=sys.argv[1]
if phase!='before':
 b=json.loads((R/'evidence/coach01/preservation-before.json').read_text());assert all(b[k]==d[k]for k in ['references','observed','entryMissing','trackedStatus']),'PRESERVATION_CHANGED_SINCE_ENTRY'
(R/('evidence/coach01/preservation-'+phase+'.json')).open('x').write(json.dumps(d,indent=2)+'\n');print(json.dumps({k:v for k,v in d.items()if k not in ['observed','entryMissing','trackedStatus']}));print('uniqueMissingAtEntry',len(d['entryMissing']))
