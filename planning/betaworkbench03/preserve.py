from pathlib import Path
import json,hashlib,os,stat,shutil,sys,datetime
R=Path(__file__).resolve().parents[2];assert shutil.disk_usage(R).free>=20*2**30+256*2**20
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=R/'evidence/workbench01/preservation-before.json';rows=json.loads(old.read_text())['snapshot'];count=0
for n,v in rows.items():
 p=R/n;s=p.lstat();kind='SYMLINK'if p.is_symlink()else'DIRECTORY'if p.is_dir()else'REGULAR_FILE';a={'kind':kind,'mode':oct(stat.S_IMODE(s.st_mode)),'bytes':0,'sha256':None}
 if kind!='DIRECTORY':a.update(bytes=len(p.read_bytes()),sha256=sha(p),mtimeNs=str(s.st_mtime_ns))
 if kind=='SYMLINK':a['linkTarget']=os.readlink(p)
 assert a==v,n;count+=1
m=R/'evidence/workbench02/handoff-java01.json';wb=json.loads(m.read_text())['inventory']
for n,v in wb.items():
 p=R/n
 if v['kind']=='SYMLINK':assert p.is_symlink()and os.readlink(p)==v['target'],n
 else:assert p.is_file()and not p.is_symlink()and p.stat().st_size==v['bytes']and sha(p)==v['sha256'],n
out={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS','oldProtectedIdentities':count,'workbench02Inventory':len(wb),'referenceHashes':{str(old.relative_to(R)):sha(old),str(m.relative_to(R)):sha(m)},'continuousPresenceClaim':False,'freeBytes':shutil.disk_usage(R).free}
if sys.argv[1]!='before':assert json.loads((R/'evidence/betaworkbench03/preservation-before.json').read_text())['referenceHashes']==out['referenceHashes']
(R/('evidence/betaworkbench03/preservation-'+sys.argv[1]+'.json')).open('x').write(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
