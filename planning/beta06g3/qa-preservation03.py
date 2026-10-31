"""Independent read-only historical integrity and new immutable snapshot."""
from pathlib import Path
import hashlib,json,os,stat,datetime,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 h=hashlib.sha256()
 with (R/p).open('rb') as f:
  while b:=f.read(1024*1024):h.update(b)
 return h.hexdigest()
def rd(p):return json.loads((R/p).read_text())
def meta(p):
 q=R/p;s=q.lstat();v={'kind':'SYMLINK'if q.is_symlink()else'REGULAR_FILE','mode':oct(stat.S_IMODE(s.st_mode))}
 if q.is_symlink():v['linkTarget']=os.readlink(q)
 if q.is_file():v.update(bytes=q.stat().st_size,sha256=sha(p))
 return v
P=R/'evidence/beta06/generation03';P.mkdir(exist_ok=True)
if len(sys.argv)>1:
 x=rd('evidence/beta06/generation03/qa-preservation-before03.json');diff=[]
 for p,v in x['snapshot'].items():
  try:
   a=meta(p)
   if a!=v:diff.append({'path':p,'expected':v,'actual':a})
  except OSError as e:diff.append({'path':p,'error':str(e)})
 out={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_PRESERVATION'if not diff else'FAIL_PRESERVATION','paths':len(x['snapshot']),'differences':diff}
 dest=P/sys.argv[1];dest.open('x').write(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k!='differences'}));assert not diff;sys.exit()
base=rd('evidence/beta06/qa-preservation-before01.json');g2=rd('evidence/beta06/generation02/flight-pins.json');freeze=rd('evidence/beta06/generation02/builder-source-freeze01.json');ready=rd('evidence/beta06/generation02/builder-source-ready02.json');g1=rd('evidence/beta06/generation02/qa-preservation-before01.json')
groups=dict(base['historicalGroups']);groups.update(G2Pins=g2['files'],G1Pins=g1['original265Pins']['files'],G2Source={v['path']:v['sha256']for v in freeze['files']},Stage={v['path']:v['sha256']for v in freeze['stage']['inventory']},Helpers={p:v['sha256']for p,v in ready['files'].items()},OldField={p:v['sha256']for p,v in base['entireImmutableField02']['files'].items()if 'sha256'in v},G1Evidence={p:v['sha256']for p,v in g1['generation01Evidence'].items()})
errors=[];paths=set()
for name,files in groups.items():
 for p,wanted in files.items():
  paths.add(p)
  try:
   if sha(p)!=wanted:errors.append({'group':name,'path':p,'expected':wanted,'actual':sha(p)})
  except OSError as e:errors.append({'group':name,'path':p,'error':str(e)})
for root in ['evidence/beta06','pilot/beta06g2','planning/beta06g2']:
 for q in (R/root).rglob('*'):
  if q.is_file()and '/generation03/'not in str(q):paths.add(str(q.relative_to(R)))
for p in ['pilot/beta06g3/launch_contract.py','pilot/beta06g3/test_launch_contract.py','pilot/beta06g3/prepare_executable.py','pilot/beta06g3/test_prepare_executable.py','planning/beta06g3/LAUNCH-DIAGNOSTIC-TIP.md','planning/beta06g3/BUILDER-ARTIFACT-VERIFY02.json','planning/beta06g3/DECISION-OFFLINE-EXECUTABLE-ARTIFACT.md','planning/beta06g3/qa-offline-artifact02.json','planning/beta06g3/BUILDER-OFFLINE-VERIFY01.json','evidence/sim32-instrument01/direct-uncorrected-source/arducopter','.local/beta06g3/arducopter']:
 paths.add(p)
snapshot={p:meta(p)for p in sorted(paths)}
requests={}
for label,root in [('legacy','evidence/field02/flight/runs'),('G1','evidence/beta06/flight/runs'),('G2','evidence/beta06/generation02/flight/runs')]:
 requests[label]=[{'path':str(p.relative_to(R)),'sha256':sha(p.relative_to(R))}for p in sorted((R/root).glob('*/request.json'))if rd(p.relative_to(R)).get('mode')=='sitl']
out={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_INDEPENDENT_BASELINE'if not errors else'FAIL_BASELINE','groups':{n:len(v)for n,v in groups.items()},'uniquePaths':len(snapshot),'snapshot':snapshot,'historicalRequests':requests,'differences':errors,'scope':'SOURCE_AND_METADATA_ONLY_NO_RUNTIME; exact SHA/bytes/modes and literal symlink targets where present; historical SHA verifier follows retained baseline semantics; no boot/telemetry acceptance'}
(P/'qa-preservation-before03.json').open('x').write(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k!='snapshot'}));assert not errors
