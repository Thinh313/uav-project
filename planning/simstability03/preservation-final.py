"""Cold read-only comparison; writes only this task's exclusive receipt."""
from pathlib import Path
import json,hashlib,os,stat,datetime,subprocess
R=Path(__file__).resolve().parents[2];E=R/'evidence/simstability03'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def identity(p):
 if not p.exists()and not p.is_symlink():return {'kind':'MISSING'}
 s=p.lstat();kind='SYMLINK'if p.is_symlink()else'DIRECTORY'if p.is_dir()else'REGULAR_FILE';v={'kind':kind,'mode':oct(stat.S_IMODE(s.st_mode)),'bytes':0,'sha256':None}
 if kind=='REGULAR_FILE':v.update(bytes=s.st_size,sha256=sha(p),mtimeNs=str(s.st_mtime_ns))
 if kind=='SYMLINK':
  v['linkTarget']=os.readlink(p)
  if p.is_file():v.update(targetBytes=p.stat().st_size,sha256=sha(p))
 return v
assert not subprocess.check_output(['docker','ps','--filter','label=aeris.task=simhand01','--format','{{.ID}}'],timeout=5).strip(),'ACTIVE_AP'
legacyPath=R/'evidence/coach01/preservation-missionbeta01-after.json';legacy=json.loads(legacyPath.read_text());drift=[]
for n,v in legacy['observed'].items():
 a=identity(R/n)
 if a!=v:drift.append({'path':n,'expected':v,'observed':a})
prePath=R/'evidence/simverify02/handoff-final01.json';pre=json.loads(prePath.read_text());preDrift=[]
for n,v in pre['inventory'].items():
 p=R/n
 if not p.is_file()or p.is_symlink()or p.stat().st_size!=v['bytes']or sha(p)!=v['sha256']:preDrift.append(n)
sources={}
for tag in ['01','02','03']:
 src=R/('.local/simstability03/receiver'+tag);pinPath=E/('source-pins'+tag+'.json');q=json.loads(pinPath.read_text());bad=[]
 for n,v in q['files'].items():
  p=src/n
  if not p.is_file()or p.is_symlink()or p.stat().st_size!=v['bytes']or sha(p)!=v['sha256']or stat.S_IMODE(p.stat().st_mode)!=v['mode']:bad.append(n)
 sources[tag]={'files':len(q['files']),'drift':bad,'pinSHA256':sha(pinPath)}
out={'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS'if not(drift or preDrift or any(v['drift']for v in sources.values()))else'FAIL','legacyObservedIdentities':len(legacy['observed']),'preexistingMissing':len(legacy['entryMissing']),'legacyReferenceSHA256':sha(legacyPath),'legacyDrift':drift,'predecessorEntries':len(pre['inventory']),'predecessorSealSHA256':sha(prePath),'predecessorDrift':preDrift,'receiverSourcePins':sources,'endureIdentities':sum(n.startswith('evidence/endure')for n in legacy['observed']),'endureDrift':[d for d in drift if d['path'].startswith('evidence/endure')],'continuousPresenceClaim':False,'ENDUREAcceptanceClaim':False,'restorationAttempted':False}
(E/'preservation-final01.json').open('x').write(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items()if k not in ['legacyDrift','predecessorDrift','receiverSourcePins']});assert out['status']=='PASS','DRIFT_RETAINED_NOT_RESTORED'
