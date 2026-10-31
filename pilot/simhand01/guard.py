from pathlib import Path
import json,datetime,hashlib,os,time,shutil
R=Path(__file__).resolve().parents[2];E=R/'evidence/simhand01'
def budget():
 original=E/'budget.json';supplied=os.environ.get('AERIS_SIMHAND_BUDGET_PATH')
 if original.exists():
  assert os.environ.get('AERIS_SIMHAND_RECIPIENT')!='1' and (not supplied or Path(supplied).resolve()==original.resolve()),'WORKSPACE_BUDGET_CANNOT_BE_OVERRIDDEN'
  return json.loads(original.read_text())
 assert os.environ.get('AERIS_SIMHAND_RECIPIENT')=='1' and supplied,'RECIPIENT_BUDGET_REQUIRED'
 bp=Path(supplied).resolve();assert bp.is_relative_to(E/'session-budgets'),'RECIPIENT_BUDGET_SCOPE'
 raw=(R/'bundle-manifest.json').read_bytes();digest=hashlib.sha256(raw).hexdigest();assert (R/'bundle-manifest.sha256').read_text().strip()==digest,'MANIFEST_SHA'
 m=json.loads(raw);assert m['format']=='aeris-simhand01-bundle' and m['version']==1
 for n,v in m['files'].items():
  p=(R/n).resolve();assert p.is_relative_to(R) and not p.is_symlink() and p.is_file() and p.stat().st_size==v['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==v['sha256'],('BUNDLE_FILE',n)
 b=json.loads(bp.read_text());assert b['sourceManifestSHA']==digest and b['maxEvidenceBytes']==2*2**30 and b['admissionGiB']==20 and b['floorGiB']==10 and b['reserveMiB']==256 and b['maxAPSessions']<=6,'RECIPIENT_POLICY'
 assert (datetime.datetime.fromisoformat(b['runtimeStopUTC'])-datetime.datetime.fromisoformat(b['anchorUTC'])).total_seconds()<=5400
 return b
def verify_sources():
 q=json.loads((E/'source-baseline01.json').read_text())
 for n,h in q['files'].items():assert hashlib.sha256((R/n).read_bytes()).hexdigest()==h,('DEPENDENCY_DRIFT',n)
def admit_ap(rid):
 b=budget();stop=datetime.datetime.fromisoformat(b['runtimeStopUTC']).timestamp();assert time.time()<stop,'TASK_RUNTIME_DEADLINE'
 verify_sources();ledger=E/'ap-admissions.jsonl';used=ledger.read_text().splitlines()if ledger.exists()else[];assert len(used)<b['maxAPSessions'],'AP_SESSION_BUDGET'
 samples=[]
 for i in range(31):
  assert time.time()<stop,'TASK_RUNTIME_DEADLINE';free=shutil.disk_usage(R).free;assert free>=20*2**30,'ADMISSION20';samples.append((time.monotonic(),free))
  if i<30:time.sleep(1)
 decline=max(0,samples[0][1]-samples[-1][1]);assert decline<=256*2**20,'ADMISSION_TREND'
 speed=decline/max(.001,samples[-1][0]-samples[0][0]);assert samples[-1][1]-15*speed>10*2**30+256*2**20,'FLOOR_FORECAST'
 own=sum(p.stat().st_size for p in E.rglob('*')if p.is_file());assert own+512*2**20<b['maxEvidenceBytes'],'EVIDENCE_RESERVE'
 fd=os.open(ledger,os.O_WRONLY|os.O_CREAT|os.O_APPEND,0o600)
 try:os.write(fd,(json.dumps({'run':rid,'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'samples':samples,'ownBytes':own,'reserveBytes':512*2**20,'noAutomaticRetry':True})+'\n').encode());os.fsync(fd)
 finally:os.close(fd)
