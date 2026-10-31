from pathlib import Path
import json,hashlib,os,stat,sys,datetime
R=Path(__file__).resolve().parents[2];E=R/'evidence/betastability02'
import re
if len(sys.argv)!=2 or not re.fullmatch('[a-zA-Z0-9-]{1,48}',sys.argv[1]):raise SystemExit('Usage: preservation-final-check.py <unique-tag>')
tag=sys.argv[1]
if(R/'.local/betastability02/active').exists():raise SystemExit('NOT_RUN_RUNTIME_ACTIVE; no expensive preservation while owned runtime is open')
for launch in(E/'launches').glob('*/launch.json'):
 closure=launch.with_name('closure.json')
 if not closure.is_file()or any(c.get('exit')is None for c in json.loads(closure.read_text()).get('children',[])):raise SystemExit('NOT_RUN_RUNTIME_CLOSURE_UNCONFIRMED:'+str(launch))

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
pinPath=E/'source-pins07.json';pins=json.loads(pinPath.read_text());pinDrift=[n for n,h in pins['files'].items()if not(R/n).is_file()or(R/n).is_symlink()or sha(R/n)!=h]
revisionResults={};revisionDrift=[]
for version in ['05','06']:
 rev=E/('source-revisions/pins'+version);oldPins=json.loads((E/('source-pins'+version+'.json')).read_text());own={n:h for n,h in oldPins['files'].items()if n.startswith(('pilot/betastability02/','native/betastability02/'))};drift=[n for n,h in own.items()if not(rev/n).is_file()or(rev/n).is_symlink()or sha(rev/n)!=h];revisionResults[version]={'expectedSuccessorByteCopies':len(own),'drift':drift,'status':'PASS'if not drift else'FAIL'};revisionDrift.extend({'version':version,'path':n}for n in drift)
q={'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS'if not(legacyDrift or preDrift or pinDrift or revisionDrift)else'FAIL','legacyReferenceSha256':sha(legacyPath),'legacyObservedIdentities':len(legacy['observed']),'preexistingMissing':len(legacy['entryMissing']),'legacyDrift':legacyDrift,'predecessorSealSha256':sha(prePath),'predecessorInventoryEntries':len(pre['inventory']),'predecessorDrift':preDrift,'sourcePinsSha256':sha(pinPath),'sourceFiles':len(pins['files']),'sourceDrift':pinDrift,'exactRetainedRevisionChecks':revisionResults,'revisionDrift':revisionDrift,'continuousPresenceClaim':False,'endureObservedIdentities':sum(n.startswith('evidence/endure')for n in legacy['observed']),'endureDrift':[v for v in legacyDrift if v['path'].startswith('evidence/endure')],'ENDUREAcceptanceClaim':False,'restorationAttempted':False}
out=E/('preservation-final-'+tag+'.json');out.open('x').write(json.dumps(q,indent=2)+'\n');print({k:v for k,v in q.items()if not k.endswith('Drift')});assert q['status']=='PASS','PRESERVATION_DRIFT_RETAINED'
