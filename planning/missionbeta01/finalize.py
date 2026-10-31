"""Seal local artifacts, never convert integrity PASS into product readiness."""
from pathlib import Path
import json,hashlib,os,re,datetime
R=Path(__file__).resolve().parents[2];E=R/'evidence/missionbeta01';sha=lambda b:hashlib.sha256(b).hexdigest()
a=json.loads((E/'acceptance01.json').read_text());assert a['status']=='NOT_READY'and a['fullyQualifiedNominals']==0 and a['video']['status']=='FAIL'and not a['video']['gates']['maximumGap'];assert a['video']['maximumConservativeGapMs']>250
pins=json.loads((E/'source-pins07.json').read_text())['files'];assert len(pins)==1008
for name,h in pins.items():assert sha((R/name).read_bytes())==h,name
before=json.loads((R/'evidence/coach01/preservation-missionbeta01-before.json').read_text());after=json.loads((R/'evidence/coach01/preservation-missionbeta01-after.json').read_text())
for k in ['observed','entryMissing','trackedStatus']:assert before[k]==after[k],k
assert len(after['entryMissing'])==165 and not (R/'.local/missionbeta01/active').exists()
report=R/'delivery/COMPLETION-MISSIONBETA01.md'
for target in re.findall(r'\]\(<([^>]+)>\)',report.read_text()):assert Path(target).is_file(),target
paths=[]
for folder in ['pilot/missionbeta01','native/missionbeta01','planning/missionbeta01','evidence/missionbeta01','delivery/mission-beta01']:
 paths += list((R/folder).rglob('*'))
paths.append(report);skip={'evidence/missionbeta01/handoff-final01.json','evidence/missionbeta01/handoff-verification01.json'};inventory={}
for p in sorted(set(paths)):
 name=str(p.relative_to(R))
 if name in skip or p.is_dir():continue
 if p.is_symlink():inventory[name]={'kind':'SYMLINK','linkTarget':os.readlink(p)}
 elif p.is_file():
  b=p.read_bytes();inventory[name]={'kind':'REGULAR_FILE','bytes':len(b),'sha256':sha(b)}
size=sum(v.get('bytes',0)for k,v in inventory.items()if k.startswith('evidence/missionbeta01/'));assert size<2*2**30
m={'format':'aeris-missionbeta01-handoff','version':1,'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'artifactIntegrity':'DIGEST_INVENTORY_NOT_SOURCE_AUTHENTICATION','milestoneReadiness':'NOT_READY','sourcePinsSha256':sha((E/'source-pins07.json').read_bytes()),'acceptanceSha256':sha((E/'acceptance01.json').read_bytes()),'completionSha256':sha(report.read_bytes()),'inventory':inventory,'scope':'FILES_PRESENT_AT_HANDOFF; FUTURE_NEW_RUNTIME_FILES_NOT_COVERED; EXISTING_SEALED_BYTES_MUST_NOT_CHANGE','production':False,'authorityRestorable':False}
p=E/'handoff-final01.json';p.open('x').write(json.dumps(m,ensure_ascii=False,indent=2)+'\n');check=json.loads(p.read_text())
for name,v in check['inventory'].items():
 q=R/name
 if v['kind']=='SYMLINK':assert q.is_symlink()and os.readlink(q)==v['linkTarget'],name
 else:assert q.is_file()and len(q.read_bytes())==v['bytes']and sha(q.read_bytes())==v['sha256'],name
v={'artifactIntegrity':'PASS','milestoneReadiness':'NOT_READY','handoffSha256':sha(p.read_bytes()),'inventoryEntries':len(inventory),'evidenceBytes':size,'sourcePinsVerified':1008,'legacyObservedIdentitiesUnchanged':17117,'preexistingMissingUnchanged':165,'noNewNominalAfterFailedGate':True,'production':False,'authorityRestorable':False};(E/'handoff-verification01.json').open('x').write(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
