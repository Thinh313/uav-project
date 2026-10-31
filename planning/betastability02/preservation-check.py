from pathlib import Path
import json,hashlib,os,stat,sys,datetime
R=Path(__file__).resolve().parents[2];E=R/'evidence/betastability02'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def identity(p):
 if not p.exists()and not p.is_symlink():return{'kind':'MISSING'}
 s=p.lstat();kind='SYMLINK'if p.is_symlink()else'DIRECTORY'if p.is_dir()else'REGULAR_FILE';v={'kind':kind,'mode':oct(stat.S_IMODE(s.st_mode)),'bytes':0,'sha256':None}
 if kind=='REGULAR_FILE':v.update(bytes=s.st_size,sha256=sha(p),mtimeNs=str(s.st_mtime_ns))
 if kind=='SYMLINK':
  v['linkTarget']=os.readlink(p)
  if p.is_file():v.update(targetBytes=p.stat().st_size,sha256=sha(p))
 return v
legacyPath=R/'evidence/coach01/preservation-missionbeta01-after.json';legacy=json.loads(legacyPath.read_text());legacyDrift=[]
for n,v in legacy['observed'].items():
 actual=identity(R/n)
 if actual!=v:legacyDrift.append({'path':n,'expected':v,'observed':actual})
prePath=R/'evidence/missionbeta01/handoff-final01.json';pre=json.loads(prePath.read_text());preDrift=[]
for n,v in pre['inventory'].items():
 p=R/n
 if v.get('kind')=='REGULAR_FILE':
  if not p.is_file()or p.is_symlink()or p.stat().st_size!=v['bytes']or sha(p)!=v['sha256']:preDrift.append(n)
 elif v.get('kind')=='SYMLINK':
  if not p.is_symlink()or os.readlink(p)!=v.get('linkTarget'):preDrift.append(n)
pinPath=E/'source-pins06.json';pins=json.loads(pinPath.read_text());pinDrift=[n for n,h in pins['files'].items()if not(R/n).is_file()or sha(R/n)!=h]
rev=E/'source-revisions/pins05';p05=json.loads((E/'source-pins05.json').read_text());own05={n:h for n,h in p05['files'].items()if n.startswith(('pilot/betastability02/','native/betastability02/'))};revisionDrift=[n for n,h in own05.items()if not(rev/n).is_file()or sha(rev/n)!=h]
q={'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS'if not(legacyDrift or preDrift or pinDrift or revisionDrift)else'FAIL','legacyReferenceSha256':sha(legacyPath),'legacyObservedIdentities':len(legacy['observed']),'preexistingMissing':len(legacy['entryMissing']),'legacyDrift':legacyDrift,'predecessorSealSha256':sha(prePath),'predecessorInventoryEntries':len(pre['inventory']),'predecessorDrift':preDrift,'sourcePinsSha256':sha(pinPath),'sourceFiles':len(pins['files']),'sourceDrift':pinDrift,'abandoned05ExactSuccessorByteCopies':len(own05),'revision05Drift':revisionDrift,'continuousPresenceClaim':False,'ENDUREAcceptanceClaim':False,'restorationAttempted':False}
out=E/('preservation-'+sys.argv[1]+'.json');out.open('x').write(json.dumps(q,indent=2)+'\n');print({k:v for k,v in q.items()if not k.endswith('Drift')});assert q['status']=='PASS','PRESERVATION_DRIFT_RETAINED'
