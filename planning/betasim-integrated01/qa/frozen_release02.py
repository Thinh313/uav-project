"""Read-only immutable candidate and old-byte preservation; no actor/admission."""
from pathlib import Path
import os,sys,json,hashlib,stat,time,datetime
repo=Path(__file__).resolve().parents[3];os.chdir(repo);os.environ['AERIS_REPOSITORY_ROOT']=str(repo);sys.path[:0]=[str(repo/'planning/betasim-integrated01/runtime/source'),str(repo)]
from aeris_runtime.candidate import load,allocated_artifact_union
from aeris_runtime.pipeline_contract import require_closed_contract
from aeris_runtime.product_inputs import validate
E=repo/'evidence/betasim-integrated01';candidate='4ce68ada8ca0abb57d4fd11e6b5907f620623442ef7ce701a3fa4f76551737c8';root=E/'candidates'/candidate;H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();start=time.monotonic_ns();manifest=load(root,candidate);gate=json.loads((E/'qa/RUNTIME-SOURCE-GATE03.json').read_text());assert manifest['qaGateSHA256']==H(E/'qa/RUNTIME-SOURCE-GATE03.json');assert manifest['sourceSHA256']==gate['sourceSHA256'];assert manifest['productSourceSHA256']==gate['productSourceSHA256'];assert manifest['native']['buildReceiptSHA256']==gate['nativeBuildReceiptSHA256'];assert manifest['native']['APK_SHA256']=='77c65876eecb6d4fbc68a113bf682fa416c4272b3ed1de71f803c63df58d1b21';contract=require_closed_contract();validate();print('candidate load and source/native gate exact PASS',flush=True)
ns={};prefix=(repo/'evidence/runtime-pipeline06/root-preservation01.py').read_text().split('\nwith(outroot/')[0];exec(compile(prefix,'readonly-legacy-preservation','exec'),ns);old=ns['result'];assert old['status']=='PASS_CURRENT_BYTES_MODES_AND_LEGACY_MTIME',old['status'];print('legacy preservation PASS',flush=True)
entry=json.loads((E/'qa/preservation-entry01.json').read_text());digest=ns['sha'];r15=repo/'evidence/runtime-transport15';oldr15=json.loads((r15/'reports/handoff-final01.json').read_text());bad=[]
for row in oldr15['rows']:
 p=r15/row[0]
 if not p.is_file():bad.append([row[0],'MISSING']);continue
 s=p.stat();actual=[row[0],s.st_size,oct(stat.S_IMODE(s.st_mode)),digest(p)]
 if actual!=row:bad.append([row[0],actual])
assert not bad,bad
atomic=repo/'evidence/runtime-transport15-atomic-prep';atomicbad=[]
for row in entry['atomicCurrentEntryBaseline']['rows']:
 p=atomic/row[0]
 if row[1]=='symlink':
  actual=[row[0],'symlink',os.readlink(p),oct(stat.S_IMODE(p.lstat().st_mode))]if p.is_symlink()else[row[0],'MISSING_OR_NOT_LINK']
 else:
  if not p.is_file():actual=[row[0],'MISSING']
  else:
   s=p.stat();actual=[row[0],s.st_size,oct(stat.S_IMODE(s.st_mode)),digest(p)]
 if actual!=row:atomicbad.append([row[0],actual])
assert not atomicbad,atomicbad
freeze=json.loads((E/'runtime/freeze02.json').read_text());fr=json.loads(freeze['originalStdout']);origins=[]
for x in fr['immutableReuseLinks']:
 p=repo/x['origin'];s=p.stat();assert stat.S_IMODE(s.st_mode)==0o444 and digest(p)==x['sha256']
 origins.append({'path':x['origin'],'sha256':x['sha256'],'mode':stat.S_IMODE(s.st_mode),'linkCount':s.st_nlink})
allocated=allocated_artifact_union(E/'candidates');assert allocated<=8*2**20;assert allocated==fr['allocatedUniqueBytes']
report={'format':'aeris-independent-frozen-betasim-candidate-preservation','version':1,'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_READONLY_CANDIDATE_AND_OLD_BYTE_PRESERVATION_NOT_ADMISSION_OR_RUNTIME','candidateSHA256':candidate,'gateSHA256':manifest['qaGateSHA256'],'nativeAPK_SHA256':manifest['native']['APK_SHA256'],'sourceFiles':len(manifest['sourceSHA256']),'productFiles':len(manifest['productSourceSHA256']),'sourceWriterContract':contract,'allocatedArtifactUnionBytes':allocated,'artifactCapBytes':8*2**20,'legacyPreservation':old,'oldR15':{'entries':len(oldr15['rows']),'drift':bad},'atomicTaskEntryBaseline':{'entries':len(entry['atomicCurrentEntryBaseline']['rows']),'drift':atomicbad,'historicalAcceptance':False},'checkedReadonlyOrigins':origins,'preexistingMissingNotRestored':old['preexistingMissingSeparate'],'actualActorsStarted':False,'actualFlightOrENDUREAcceptance':False,'noOldLedgerOrHistoryRewritten':True,'elapsedNs':time.monotonic_ns()-start}
out=E/'qa/FROZEN-CANDIDATE-REVIEW02.json';assert not out.exists();out.write_text(json.dumps(report,separators=(',',':'))+'\n');print(json.dumps({'status':report['status'],'path':str(out),'sha256':H(out),'allocated':allocated,'elapsedSeconds':report['elapsedNs']/1e9}))
