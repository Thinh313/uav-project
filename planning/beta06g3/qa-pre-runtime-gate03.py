"""Independent final metadata/source/mock gate. Never performs actual runtime."""
from pathlib import Path
import json,hashlib,os,stat,datetime,difflib,shutil,ast
R=Path(__file__).resolve().parents[2];E=R/'evidence/beta06/generation03'
def read(p):return json.loads((R/p).read_text())
def sha(p):
 h=hashlib.sha256()
 with (R/p).open('rb')as f:
  while b:=f.read(1024*1024):h.update(b)
 return h.hexdigest()
def meta(p):
 q=R/p;s=q.lstat();v={'kind':'SYMLINK'if q.is_symlink()else'REGULAR_FILE','mode':oct(stat.S_IMODE(s.st_mode))}
 if q.is_symlink():v['linkTarget']=os.readlink(q)
 if q.is_file():v.update(bytes=q.stat().st_size,sha256=sha(p))
 return v
errors=[];baseline=read('evidence/beta06/generation03/qa-preservation-before03.json')
for p,v in baseline['snapshot'].items():
 try:
  if meta(p)!=v:errors.append({'path':p,'problem':'HISTORICAL_PRESERVATION_DRIFT'})
 except OSError as e:errors.append({'path':p,'error':str(e)})
pinpath='evidence/beta06/generation03/flight-pins.json';freezePath='evidence/beta06/generation03/builder-source-freeze01.json';helperPath='evidence/beta06/generation03/native-helper-freeze01.json';pins=read(pinpath);freeze=read(freezePath);helpers=read(helperPath)
assert sha(pinpath)=='91242c0a8c7011c05465c61493e516fb16cdca5438f9d06dbeb639e2ac98cbce'
assert sha(freezePath)=='160ad6a5f7c04e130f2ff1a566cc1e9d953ec7cac059c4c80cd8d9024c7e677b'
assert sha(helperPath)=='90693e27884ecfb986c5cd973fe032f11ccc708722315890f4748f88cf33683b'
for p,h in pins['files'].items():
 if sha(p)!=h:errors.append({'path':p,'problem':'G3_MANIFEST_DRIFT'})
for p,h in helpers['files'].items():
 if sha(p)!=h:errors.append({'path':p,'problem':'HELPER_FREEZE_DRIFT'})
for group in [freeze['files'],freeze['stage']['inventory']]:
 for v in group:
  if sha(v['path'])!=v['sha256']or(R/v['path']).stat().st_size!=v['bytes']:errors.append({'path':v['path'],'problem':'SOURCE_OR_STAGE_DRIFT'})
assert len(pins['files'])==385 and len(helpers['files'])==24 and len(freeze['files'])==30 and len(freeze['stage']['inventory'])==132
assert pins['helperFreeze']=={'path':helperPath,'sha256':sha(helperPath)}
assert freeze['manifest']['sha256']==sha(pinpath)
assert pins['previousManifestSha256']==sha('evidence/beta06/generation02/flight-pins.json')
assert pins['budget']['maxNewSITLRequests']==4 and pins['budget']['refuseNewOrdinal']==5 and pins['budget']['hostDeadlineSeconds']==1800 and pins['budget']['APDeadlineSeconds']==540
assert [len(pins[k])for k in ['priorSITLRequests','priorBetaSITLRequests','priorGeneration02SITLRequests']]==[11,1,1]
assert not list((E/'flight/runs').iterdir()),'ACTUAL_G3_REQUEST_BEFORE_GATE'
assert not any(E.glob('android-attempt*.json'))and not any(E.glob('root-controller*.jsonl'))and not (E/'host-app03').exists(),'ACTUAL_G3_RUNTIME_BEFORE_GATE'
lineage=read('evidence/beta06/generation03/workspace-copy01.json');actualWorkspace={str(p.relative_to(R))for p in (E/'workspace01').rglob('*')if p.is_file()};assert actualWorkspace=={v['copy']for v in lineage['files']}
for v in lineage['files']:
 assert sha(v['source'])==sha(v['copy'])==v['sha256']and(R/v['source']).stat().st_size==(R/v['copy']).stat().st_size==v['bytes']
assert len(lineage['files'])==17 and sum(v['bytes']for v in lineage['files'])==798359 and lineage['inheritedEvidenceDoesNotCountAsGeneration03Execution']
reports={'qa-host-window04.json':10,'qa-restart-proof-mock04.json':13,'qa-controller-negative04.json':7,'qa-launcher-capture05.json':7,'qa-launcher-lifecycle05.json':10,'qa-qualified-profile03.json':19,'qa-request-cap04.json':11,'qa-ui-emitter03.json':3,'qa-ui-ground-contract03.json':1};testReports={}
for name,groups in reports.items():
 p='evidence/beta06/generation03/'+name;x=read(p);assert x['status'].startswith('PASS'),name
 for n,h in x.get('sources',{}).items():assert sha(n)==h,(name,n)
 if 'source'in x:assert sha(x['source']['path'])==x['source']['sha256']
 for n,v in x.get('input',{}).items():
  if n=='path':assert sha(v)==x['input']['sha256']
 testReports[name]={'sha256':sha(p),'groups':groups,'classification':'MOCK_OR_SOURCE_ONLY','status':x['status']}
# Exact source algorithm preservation, allowing only declared namespaces/profile fences.
exactReuse={}
for name in ['bootstrap.js','ui.mjs','ui-observation.mjs','lifecycle-diagnostics.mjs']:
 a='pilot/beta06g2/'+name;b='pilot/beta06g3/'+name;assert (R/a).read_bytes()==(R/b).read_bytes();exactReuse[b]={'baseline':a,'sha256':sha(b),'semantics':'LITERAL_BYTE_EXACT_G2_OBSERVATIONAL_WIRE_CONTRACT'}
for name in ['qa-raw-flight.mjs','qa-cut-replay.mjs','qa-reboot-replay.mjs','qa-overlap-replay.mjs','qa-restart-proof.py','qa-media-replay.py','qa-native-replay.py']:
 a=(R/'planning/beta06g2'/name).read_text().replace('beta06g2','beta06g3').replace('generation02','generation03');b=(R/'planning/beta06g3'/name).read_text();assert a==b,name
 exactReuse['planning/beta06g3/'+name]={'baseline':'planning/beta06g2/'+name,'sha256':sha('planning/beta06g3/'+name),'semantics':'ONLY_GENERATION_NAMESPACE_CHANGED;SHARED_CANONICAL_ALGORITHMS_RETAINED'}
assert "canonicalVerifyFlightFiles}from'../../../field02/flight/handoff-raw.mjs'"in(R/'pilot/beta06g3/flight/qualified/verify-profile.mjs').read_text()
for p in (R/'planning/beta06g3').glob('*.py'):ast.parse(p.read_text())
for p in (R/'pilot/beta06g3').rglob('*.py'):ast.parse(p.read_text())
# Bound final artifacts/resources; runtime must independently re-admit all disk/current UI limits.
aggregate=sum(p.stat().st_size for p in (R/'evidence/beta06').rglob('*')if p.is_file());free=shutil.disk_usage(R).free;assert aggregate<200*2**20 and free>=29*2**30
runtime='pilot/beta06g3/flight/runtime.py';runtimeSource=(R/runtime).read_text();assert 'check_output'not in runtimeSource and "runner.background=[];runner.closing=True"in runtimeSource and 'self.meta=Budget(160*1024);self.closure_meta=Budget(64*1024);self.closure_control=Budget(32*1024)'in runtimeSource
assert "'--log-driver','json-file','--log-opt','max-size=2m','--log-opt','max-file=2'"in runtimeSource and "'--since',event_since"in runtimeSource
out={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_INDEPENDENT_FROZEN_SOURCE_METADATA_MOCK_GATE_ROOT_ADMISSION_ONLY'if not errors else'FAIL','classification':'SOURCE_AND_MOCK_NOT_ACTUAL_ACCEPTANCE','preservation':{'uniqueSnapshotPaths':len(baseline['snapshot']),'groups':baseline['groups'],'differences':errors,'historicalRequestCounts':{k:len(v)for k,v in baseline['historicalRequests'].items()},'noPoolingHistoricalSuccess':True,'originalArchiveAndExecutablePreserved':True},'frozen':{'manifest':{'path':pinpath,'sha256':sha(pinpath),'files':385},'sourceFreeze':{'path':freezePath,'sha256':sha(freezePath),'productionFiles':30,'stageFiles':132},'nativeHelperFreeze':{'path':helperPath,'sha256':sha(helperPath),'files':24}},'sourceReview':{'exactReuse':exactReuse,'qualifier':'Descriptor-bound nofollow regular7172336/0755/SHA/ELF64AARCH64 immediatelyprecreate, original0644refused','launcher':'exclusivecreate;exactCID/name/run/task;singleattach plus exactlyoneexplicitrebootstop/start;eventsSinceboundbeforecreate;boundedprefixstreams2MiBeach,events256KiB,metadata160+64+32KiB;fsyncfilesandreceipts;parent/deadline/overflowfailclosed;ownedCIDonlystop;retainedcontainers/state/logbudgets;UNKNOWNinspectneverreadiness','captureFailuresResolved':['Failedbackgroundcapturecouldsuppressclosure:clearbackgroundbeforeclosure','Exhaustedruntimemetadatacouldsuppressstop:reservedclosurebudgetsandpriorboundCIDownership','Eventssubscriptionrace:precreateintentbound--sincelowerbound','Malformedpriorrequestscouldescapequota:failclosedcounterbeforeUUID/mkdir/write'],'strictVerifier':'Canonicalfield02CRC/semantic/mission/home/takeoffverifierretained;qualifiedG3metadatafenceadded;shareddecoderexplicitlydisclosed','nativeController':'persistentPythonanchors;bounded8192protocol;consumedlaunches;originalhost/emulatorabsolutedeadlines;N1F1restartN2F2;Connect100s;noautomaticretry;boot05persistenceonly;native34/19/13baselineand3remaining'},'tests':{'independentSelectedGroups':sum(reports.values()),'reports':testReports,'offlineImmutableUtilities':'test_launch_contract10/10 +test_prepare_executable10/10 independentlyran; retainedreportdescribesstructuralonly','builderRuntimeTestsIndependentlyReran':{'groups':13,'pass':13,'classification':'BUILDER_DESIGNED_FAKE_TESTS_NOT_NEW_INDEPENDENT_SCENARIOS'},'limitations':['Lifecycle fake schemas partly shared from Builder, independent assertions/failureinjections separately recorded.','Source and mocks do not prove actual Docker compatibility,255historicalcause,APboot,flight,video,payload,nativeprovideracceptance or crashdurability.','Actual emitted snapshot tested inVM/inprocessrequesthandlers, no listener/browser or75srealinterval.']},'dataFork':{'files':17,'bytes':798359,'exactSourceCopySHA':True,'inheritedEvidenceCountsAsNewExecution':False},'resources':{'aggregateBetaEvidenceBytes':aggregate,'earlyLimitBytes':200*2**20,'totalLimitBytes':256*2**20,'freeBytesNow':free,'runtimeStableAdmissionStillRequired':True},'runtimeState':{'newActualAPRequests':0,'newAndroidAttempts':0,'newActualHostProcesses':0,'nativeHistoricalPickerPending':13,'remainingLifetimePickerOperations':3,'actualAcceptance':'NOT_CHECKED'},'requirements':{'sourceMetadataAndMockGate':'PASS','actualN1F1ManagedRestartN2F2':'NOT_CHECKED','actualVideoPayloadAnd75sRenewals':'NOT_CHECKED','actualOptionalNativeSAF':'NOT_CHECKED','allMandatoryBetaGates':'NOT_READY'},'disposition':'READY_FOR_ROOT_FRESH_FINITE_ADMISSION_ONLY. BETA06_NOT_READY until actual mandatorygates met. Root alone mayperformactualruntime within authorized4requests/one30minhostwindow; failed/uncertainactualscenario ends campaign. Require fresh independent acceptedN1/N2 replay before followingfault; oldsuccess neverpooled.','scope':'IndependentQA only newhelpers/reports; no productionedits,actualDocker/ADB/browser/emulator/listener,binaryexec,build/sign/install or existingartifactwrites. Tiny localQAfixtures automaticallyremoved; no scratchproject/dependencyinstall.'}
assert not errors
p=E/'qa-pre-runtime-gate03.json'
with p.open('x')as f:json.dump(out,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
fd=os.open(p.parent,os.O_RDONLY|os.O_DIRECTORY)
try:os.fsync(fd)
finally:os.close(fd)
print(json.dumps({'status':out['status'],'snapshotPaths':len(baseline['snapshot']),'pins':len(pins['files']),'helperFiles':len(helpers['files']),'selectedGroups':sum(reports.values()),'aggregateBytes':aggregate,'gateSHA256':sha(p.relative_to(R))}))
