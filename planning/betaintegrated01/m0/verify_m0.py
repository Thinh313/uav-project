"""Contractor validates M0 input handoff; no product import, build or runtime."""
from pathlib import Path
import json,hashlib,datetime,os,stat,subprocess,shutil,ast
R=Path(__file__).resolve().parents[3];P=R/'planning/betaintegrated01/m0';E=R/'evidence/betaintegrated01-m0'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
entry=json.loads((E/'entry01.json').read_text());assert datetime.datetime.now(datetime.timezone.utc).timestamp()-entry['startEpoch']<entry['analysisWallBudgetSeconds']
campaignPath=R/'planning/beta-campaign01/campaign.json';assert sha(campaignPath)==entry['campaignSHA256']
C=json.loads(campaignPath.read_text());F=json.loads((P/'qualification-contract01.json').read_text());assert F['requiredRequirementIDs']==[r['id']for r in C['requirements']]and F['metricMethods']==C['metrics']and F['caseDesigns']==C['cases']
assert sha(E/'heldout-seeds01.json')==F['nominalCorpus']['seedCommitment']['sha256'];assert len(json.loads((E/'heldout-seeds01.json').read_text()))==18
V=json.loads((P/'dependencies/native98-virtual-input-closure.json').read_text());assert V['javaInputCount']==47 and V['virtualAssetCount']==104 and not V['unresolvedDirectStaticImportsOrResources']and V['runtimeAPKAccepted']is False and V['fullBetaRunnableClosureAccepted']is False and not V['selectedPythonBuildRuntimeLaunchers']
checked=[]
for v in V['javaInputs']+list(V['virtualAssetMap'].values()):
 n=v.get('inputPath',v['path']);binding=V['exactBindingsForMissingAssets'].get(v['path'])
 if binding:n=binding['inputPath']
 p=R/n;assert p.is_file()and len(p.read_bytes())==v['bytes']and sha(p)==v['sha256'],('SELECTED_INPUT_DRIFT',n);checked.append(n)
D=json.loads((P/'dependencies/projection-and-unresolved-disposition.json').read_text());assert D['unresolvedOriginalCount']==37 and len(D['dispositions'])==37 and not D['actualUnresolvedInputs']
profile=json.loads((P/'target-profile01.json').read_text());assert not profile['Android']['bootedNow']and profile['selectedIntegrationArchitecture']['APCandidateSHA256']is None and profile['selectedIntegrationArchitecture']['unknownHashBlocksActualLaunch']
assert all(profile['Android'][k]is None for k in ['WebViewVersion','GPUActualRenderer','codecActualBackend'])
for v in profile['artifactFiles'].values():assert v['status']=='PRESENT_COLD_HASHED'and sha(Path(v['path']))==v['sha256'],('PREREQUISITE_DRIFT',v['path'])
rec=json.loads((E/'recorder/cold-analysis02.json').read_text());assert rec['runtimeStarted']is False and rec['nativeOrAPBuildPerformed']is False and rec['sourceMutated']is False
assert len(rec['sizing'])==4 and all(not v['admissibleWithCurrent128MiBAPTrace']for v in rec['sizing'])
for n,v in rec['sourcePins'].items():
 # The analyzer carries either direct SHA strings or hash/size identities.
 expected=v if isinstance(v,str)else v['sha256'];assert sha(R/n)==expected,('RECORDER_SOURCE_DRIFT',n)
legacyPath=R/'evidence/coach01/preservation-missionbeta01-after.json';legacy=json.loads(legacyPath.read_text());drift=[]
def identity(p):
 if not p.exists()and not p.is_symlink():return {'kind':'MISSING'}
 s=p.lstat();kind='SYMLINK'if p.is_symlink()else'DIRECTORY'if p.is_dir()else'REGULAR_FILE';v={'kind':kind,'mode':oct(stat.S_IMODE(s.st_mode)),'bytes':0,'sha256':None}
 if kind=='REGULAR_FILE':v.update(bytes=s.st_size,sha256=sha(p),mtimeNs=str(s.st_mtime_ns))
 if kind=='SYMLINK':
  v['linkTarget']=os.readlink(p)
  if p.is_file():v.update(targetBytes=p.stat().st_size,sha256=sha(p))
 return v
for n,v in legacy['observed'].items():
 if identity(R/n)!=v:drift.append(n)
seal=json.loads((R/'evidence/simstability03/handoff-final01.json').read_text());sealDrift=[n for n,v in seal['inventory'].items()if not(R/n).is_file()or(R/n).stat().st_size!=v['bytes']or sha(R/n)!=v['sha256']]
assert not drift and not sealDrift,('OLD_INPUT_DRIFT',drift,sealDrift)
status=subprocess.check_output(['git','status','--porcelain=v1'],cwd=R).decode().splitlines();tracked=[s for s in status if not s.startswith('?? ')];assert len(tracked)==97 and all(s.startswith(' D ')for s in tracked)
for p in P.rglob('*.py'):ast.parse(p.read_text(),filename=str(p))
files=list(P.rglob('*'))+list((R/'evidence/betaintegrated01-m0').rglob('*'));outBytes=sum(p.stat().st_size for p in files if p.is_file());assert outBytes<16*2**20
deliverables=[{'id':'D01','outcome':'Source-backed module/call-route/owner decision','status':'PASS_M0_DESIGN','evidence':'architecture/decisions01.json + architecture/REPORT.md + DECISIONS.md'}, {'id':'D02','outcome':'Cold profile16prereqs,2baselineAPbindings,candidate/live-probe gates','status':'PASS_M0_PROFILE_NOT_LIVE','evidence':'target-profile01.json; independent root-profile QA'}, {'id':'D03','outcome':'Exact source intake6missingassets,151Java/assets,0static unresolved','status':'PASS_M0_SOURCE_BINDING','evidence':'dependencies/native98-virtual-input-closure.json; no frozen restoration'}, {'id':'D04','outcome':'Actual recorder94 cause,clock/buffer/quota/native limits and4duration sizing','status':'PASS_COLD_ANALYSIS','evidence':'recorder/M1-DESIGN.md and cold-analysis02.json'}, {'id':'D05','outcome':'28MUST/13metric/48cases +18seed commitment','status':'PASS_FROZEN_TARGETS_NOT_PRODUCT_ACCEPTANCE','evidence':'qualification-contract01.json'}, {'id':'D06','outcome':'M1mock and actual-entry scopes,budgets,stop rules','status':'PASS_HANDOFF_CONTRACT','evidence':'../TIP-M1-MOCK.md'}, {'id':'D07','outcome':'Input SHA/source closure classification/preservation/limits verified','status':'PASS_M0_INPUT_CONSISTENCY_NOT_EXECUTABLE_RELEASE','evidence':'verification-final01.json'}]
q={'format':'aeris-beta-integrated01-m0-contractor-verification','version':1,'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'M0_SOURCE_HANDOFF_READY_FOR_M1_MOCK','M0Complete':True,'M1Complete':False,'betaReady':False,'deliverables':deliverables,'counts':{'deliverables':7,'boundJavaAssets':len(checked),'staticAssetImports':len(V['staticAssetEdges']),'originalMissingAssetBindings':len(V['exactBindingsForMissingAssets']),'coldPrerequisiteFiles':len(profile['artifactFiles']),'MUST':28,'metrics':13,'caseDesigns':48,'seededNominals':18},'runtimeExecutableClosure':'NOT_CREATED_NOT_ACCEPTED; M1 actual launch blocked until materialized/pinned','knownInputScope':'Source input map complete for Native98 adaptation; broad references/projections classified; not final beta APK closure','independentReviewScope':'Separate agent reviewed root cold profile only. Architecture/dependency/recorder builders self-reviewed; Contractor checked outputs/hashes. No human runtime review.','preservation':{'legacyIdentities':len(legacy['observed']),'preexistingMissing':len(legacy['entryMissing']),'legacyDrift':drift,'priorTaskSealEntries':len(seal['inventory']),'priorTaskSealDrift':sealDrift,'trackedMissing97Unchanged':True,'originalMissingPathRestored':False,'ENDUREAcceptanceClaim':False},'analysisNewOutputBytes':outBytes,'entryFreeBytes':entry['entryFreeBytes'],'finalFreeBytes':shutil.disk_usage(R).free,'M0RuntimeLaunches':0,'M0BuildInstallSign':0,'limits':['Cold target API/image is not actual running Android/WebView/GPU/codec','Native provider/session/manual integration and operatorB arbiter not implemented','New AP recorder artifact notbuilt; actual launch blocked','Whole beta still NOT_READY; no actual/HIL/field/hardware claims'],'elapsedSeconds':datetime.datetime.now(datetime.timezone.utc).timestamp()-entry['startEpoch']}
(E/'verification-final01.json').open('x').write(json.dumps(q,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:q[k]for k in ['status','M0Complete','M1Complete','betaReady','counts','elapsedSeconds']},indent=2))
