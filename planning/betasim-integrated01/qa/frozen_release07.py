"""Read-only immutable candidate and old-byte preservation; no actor/admission."""
from pathlib import Path
import os,sys,json,hashlib,stat,time,datetime
repo=Path(__file__).resolve().parents[3];os.chdir(repo);os.environ['AERIS_REPOSITORY_ROOT']=str(repo);sys.path[:0]=[str(repo/'planning/betasim-integrated01/runtime/source'),str(repo)]
from aeris_runtime.candidate import load,allocated_artifact_union
from aeris_runtime.pipeline_contract import require_closed_contract
from aeris_runtime.product_inputs import validate
E=repo/'evidence/betasim-integrated01';candidate='949a1086ab71d57f218e9834237d2a2bea914a5f9338d228bcc8c3947416c309';root=E/'candidates'/candidate;H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();start=time.monotonic_ns();manifest=load(root,candidate);gate=json.loads((E/'qa/RUNTIME-SOURCE-GATE08.json').read_text());assert manifest['qaGateSHA256']==H(E/'qa/RUNTIME-SOURCE-GATE08.json');assert manifest['sourceSHA256']==gate['sourceSHA256'];assert manifest['productSourceSHA256']==gate['productSourceSHA256'];assert manifest['native']['buildReceiptSHA256']==gate['nativeBuildReceiptSHA256'];assert manifest['native']['APK_SHA256']=='8bc0a7c612c010f77e3e8c66fa6126d1d6992821eafa4f88c31a598bc188b1e1';contract=require_closed_contract();validate();print('candidate load and source/native gate exact PASS',flush=True)
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
freeze=json.loads((E/'runtime/freeze07.json').read_text());fr=json.loads(freeze['originalStdout']if'originalStdout'in freeze else freeze['stdout']);origins=[]
for x in fr['immutableReuseLinks']:
 p=repo/x['origin'];s=p.stat();assert stat.S_IMODE(s.st_mode)==0o444 and digest(p)==x['sha256']
 origins.append({'path':x['origin'],'sha256':x['sha256'],'mode':stat.S_IMODE(s.st_mode),'linkCount':s.st_nlink})
allocated=allocated_artifact_union(E/'candidates');assert allocated<=8*2**20;assert allocated==fr['allocatedUniqueBytes']
old_loads=[]
for oldid in ['c9d43b1768b89614701d0dfd9334f5e7fd940eda4aa6c49c386c975607553ef4','710491d0e838fbcc0915732b36ba086078eeee75d3aefca2d828c493d64b8049','ee9171fa205d37460db30cd112dd3096106e11c7522f573de1c4527b7362301d','549c9877a9eb5eda413b43ea2ac29e7377942e03cfcf9621df38622e9d293c89','924d3c6e658f1a89243827f578c9f7d25d1cab79439585a5df843c2a1412b6b4','4ce68ada8ca0abb57d4fd11e6b5907f620623442ef7ce701a3fa4f76551737c8']:
 previous=load(E/'candidates'/oldid,oldid);old_loads.append({'candidateSHA256':oldid,'artifactCapBytes':previous['artifactCapBytes'],'fullReadonlyLoad':'PASS'})
postmortem=json.loads((E/'runtime/R02-POSTMORTEM-EVENTREF05.json').read_text());oldrunrefs=[]
for row in postmortem['originalEvidence']:
 p=repo/row['path'];assert p.is_file()and p.stat().st_size==row['bytes']and H(p)==row['sha256'];oldrunrefs.append(row)
oldruns={}
for scope in ['r01','r02','r03','r04','r05','r06']:
 rows=[]
 for p in sorted((E/scope).rglob('*')):
  if p.is_file():rows.append({'path':str(p.relative_to(E/scope)),'bytes':p.stat().st_size,'sha256':H(p),'mode':stat.S_IMODE(p.stat().st_mode)})
 oldruns[scope]={'rows':rows,'baselineTime':'CURRENT_POST_R06_PRE_RELEASE07_NOT_HISTORICAL_CONTINUITY'}
prior_runs=json.loads((E/'qa/FROZEN-CANDIDATE-REVIEW06.json').read_text())['oldRunColdEntryBaselines'];run_comparisons={}
for scope,expected in prior_runs.items():
 assert oldruns[scope]['rows']==expected['rows'],'OLD_CLOSED_RUN_CHANGED:'+scope
 run_comparisons[scope]={'fullPriorBaselineRows':len(expected['rows']),'drift':[]}
for name in ['runtime/R03-RUNTIME-UI06-POSTMORTEM.json','product/R03-CAUSE-UI06.json']:
 post=json.loads((E/name).read_text())
 refs=post.get('originalEvidence',post.get('actualOriginalEvidence',[]))
 if type(refs)is list:
  for row in refs:
   if type(row)is dict and 'path'in row and'sha256'in row:
    file=repo/row['path'];assert H(file)==row['sha256'];oldrunrefs.append(row)
gatechecks={}
for n,h in {1:'ee58d82886546173cb392657a74c1d39b3d0d29525c9dc20804f9095169e1968',2:'4daec6c1df44344e70b957c46f8d056d10e6187095862526a88981f54a585785',3:'fb90ce23e8cdec65de095ad71cd783f4324c93884af1b8895255f93f59854163',4:'2947676bb758f4e2abc2034d6bccbaf456e7d44502305369f24309501109a251',5:'742edc2f955095035836cac8535eaa49423326522b6e0d4a9bff0f0d9d378060',6:'8de90dd90cb3c20799b68ed16acfe6856d0f3cdd002a635f70562dfc86a311cb',7:'0ee8172019795847319fa3df015598ec7498813ed1d8b42b86c55e78d807c29e',8:'045e7c4062c3df46261c944f1c87e19717f243c72921cb09baec3319007138a1'}.items():
 file=E/('qa/RUNTIME-SOURCE-GATE%02d.json'%n);assert H(file)==h;gatechecks[str(file.relative_to(repo))]=h
r04refs=[]
for name,key in [('runtime/R04-PREFLIGHT-CAUSE07.json','allOriginalTransportFiles'),('product/r04-nav-cause07.json','originalReports')]:
 diagnostic=json.loads((E/name).read_text())
 for ref in diagnostic[key]:
  file=repo/ref['path'];assert file.is_file()and file.stat().st_size==ref['bytes']and H(file)==ref['sha256'];r04refs.append(ref)
r05report=json.loads((E/'qa/ACTUAL-R05-CAUSE01.json').read_text())
for ref in r05report['originalEvidence']:
 p=repo/ref['path'];assert p.stat().st_size==ref['bytes']and H(p)==ref['sha256']
r06report=json.loads((E/'qa/ACTUAL-R06-CAUSE01.json').read_text());assert oldruns['r06']['rows']==r06report['originalRowsBaseline'],'R06_ALL316_BASELINE_CHANGED';run_comparisons['r06']={'fullPriorBaselineRows':len(r06report['originalRowsBaseline']),'drift':[]};print('R01 through R06 all original baselines PASS',flush=True)
report={'r05IndependentOriginalRefs':r05report['originalEvidence'],'r06All316IndependentBaselineSHA256':H(E/'qa/ACTUAL-R06-CAUSE01.json'),'selectedNativeApplication':'vn.rtr.aeris.betasim09','engineeringShortOnly':True,'format':'aeris-independent-frozen-betasim-candidate-preservation','version':1,'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_READONLY_CANDIDATE_AND_OLD_BYTE_PRESERVATION_NOT_ADMISSION_OR_RUNTIME','candidateSHA256':candidate,'gateSHA256':manifest['qaGateSHA256'],'nativeAPK_SHA256':manifest['native']['APK_SHA256'],'sourceFiles':len(manifest['sourceSHA256']),'productFiles':len(manifest['productSourceSHA256']),'sourceWriterContract':contract,'allocatedArtifactUnionBytes':allocated,'artifactCapBytes':8*2**20,'legacyPreservation':old,'oldCandidateFullLoads':old_loads,'r02OriginalPostmortemRefs':oldrunrefs,'oldRunColdEntryBaselines':oldruns,'priorClosedRunComparisons':run_comparisons,'r04AllSegmentsAndOriginalReportRefs':r04refs,'sourceGatesUnchanged':gatechecks,'oldR15':{'entries':len(oldr15['rows']),'drift':bad},'atomicTaskEntryBaseline':{'entries':len(entry['atomicCurrentEntryBaseline']['rows']),'drift':atomicbad,'historicalAcceptance':False},'checkedReadonlyOrigins':origins,'preexistingMissingNotRestored':old['preexistingMissingSeparate'],'actualActorsStarted':False,'actualFlightOrENDUREAcceptance':False,'noOldLedgerOrHistoryRewritten':True,'elapsedNs':time.monotonic_ns()-start}
out=E/'qa/FROZEN-CANDIDATE-REVIEW07.json';assert not out.exists();out.write_text(json.dumps(report,separators=(',',':'))+'\n');print(json.dumps({'status':report['status'],'path':str(out),'sha256':H(out),'allocated':allocated,'elapsedSeconds':report['elapsedNs']/1e9}))
