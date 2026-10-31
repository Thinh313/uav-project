"""Seal own artifacts after closure. Exclude only manifest and its verifier receipt."""
from pathlib import Path
import hashlib,json,os,stat,datetime,time,shutil
R=Path(__file__).resolve().parents[2];E=R/'evidence/betastability02'
assert not(R/'.local/betastability02/active').exists()
manifest=E/'handoff-final07.json';verification=E/'handoff-verification07.json'
assert not manifest.exists()and not verification.exists()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def identity(p):
 s=p.lstat()
 if p.is_symlink():return {'kind':'SYMLINK','linkTarget':os.readlink(p)}
 assert stat.S_ISREG(s.st_mode),str(p)
 return {'kind':'REGULAR_FILE','bytes':s.st_size,'sha256':sha(p)}
inventory={}
for folder in ['pilot/betastability02','native/betastability02','planning/betastability02','evidence/betastability02']:
 for p in sorted((R/folder).rglob('*')):
  if any(n in {'.build','.swift-cache','__pycache__'}for n in p.parts):continue
  if p in [manifest,verification]or(p.is_dir()and not p.is_symlink()):continue
  inventory[str(p.relative_to(R))]=identity(p)
for n in ['delivery/COMPLETION-BETA-STABILITY02.md','delivery/COMPLETION-BETA-STABILITY02.html']:inventory[n]=identity(R/n)
q={'format':'aeris-betastability02-handoff','version':1,'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'NOT_READY','inventory':inventory,'scope':'ISOLATED_SUCCESSOR_FILES_FAILED_RUNS_MOCK_FIXTURES_AND_COMPLETION_REPORTS','sourcePins07Sha256':sha(E/'source-pins07.json'),'excludedSelfReferences':[str(manifest.relative_to(R)),str(verification.relative_to(R))],'acceptanceSha256':sha(E/'acceptance.json'),'oldEvidenceRewritten':False,'releaseSelected':False,'productionSigned':False,'frozenPreservation':'preservation-final-preseal07.json','noSelfHashClaim':True}
encoded=(json.dumps(q,ensure_ascii=False,indent=2)+'\n').encode();fd=os.open(manifest,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
try:
 offset=0
 while offset<len(encoded):
  written=os.write(fd,memoryview(encoded)[offset:]);assert written>0,'SEAL_SHORT_WRITE';offset+=written
 os.fsync(fd)
finally:os.close(fd)
fd=os.open(E,os.O_RDONLY)
try:os.fsync(fd)
finally:os.close(fd)
drift=[n for n,v in inventory.items()if not(R/n).exists()or identity(R/n)!=v]
assert not drift,drift
v={'status':'PASS_SEAL_BYTES_RECHECKED_NOT_PRODUCT_ACCEPTANCE','manifestSha256':sha(manifest),'manifestBytes':manifest.stat().st_size,'inventoryEntries':len(inventory),'inventoryRegularBytes':sum(x.get('bytes',0)for x in inventory.values()),'drift':drift,'freeBytes':shutil.disk_usage(R).free,'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat()}
with verification.open('x')as f:json.dump(v,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
print(json.dumps(v,indent=2))
