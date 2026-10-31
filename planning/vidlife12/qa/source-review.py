"""Independent selected source/cap review. Root owns execution and admission.
No production imports, no actor creation, no candidate/source writes.
"""
from pathlib import Path
import json,hashlib,ast,stat,sys,re,os
R=Path(__file__).resolve().parents[3];E=R/'evidence/vidlife12/qa';P=R/'planning/vidlife12';H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
iso=json.loads((P/'isolation-before-patches.json').read_bytes());assert iso['copiedRuntimeFiles']==117 and len(iso['receipts'])==126
changes=[]
for row in iso['receipts']:
 originalSHA=row.get('sha256',row.get('originalSHA256'));assert isinstance(originalSHA,str)and len(originalSHA)==64
 old=R/row['original'];new=R/row['selected'];assert old.is_file() and new.is_file() and not old.is_symlink() and not new.is_symlink();assert H(old)==originalSHA,'original source changed';assert(old.stat().st_dev,old.stat().st_ino)!=(new.stat().st_dev,new.stat().st_ino),'mutable shared inode'
 if H(new)!=originalSHA:changes.append(row['selected'])
allowedRuntime={'assets/pipeline-writer-pins.json','assets/product-input-closure.json','candidate.py','inventory.py','preview10.py','product_runtime.py','public_ui_workload.py'}
base=P/'runtime/source/aeris_runtime';oldBase=R/iso['frozenCandidate']/'source/aeris_runtime'
for new in changes:
 if new.startswith('planning/vidlife12/runtime/source/aeris_runtime/'):assert new.split('aeris_runtime/',1)[1]in allowedRuntime,new
pin=json.loads((base/'assets/pipeline-writer-pins.json').read_bytes());oldpin=json.loads((oldBase/'assets/pipeline-writer-pins.json').read_bytes());graph=json.loads((base/'assets/product-input-closure.json').read_bytes())
for k in['envelope','owners','healthContract','metadataBoundary','frozenLeafSHA256']:assert pin[k]==oldpin[k],k+' changed'
assert len(pin['sites'])==len(oldpin['sites'])==200
semantic=lambda rows:sorted(json.dumps({k:v for k,v in x.items()if k!='line'},sort_keys=True)for x in rows)
assert semantic(oldpin['sites'])==semantic(pin['sites'])
def original_writer_ast(root,row):
 source=(root.parent/row['module']).read_text();tree=ast.parse(source);matches=[]
 for node in ast.walk(tree):
  if isinstance(node,ast.Call)and node.lineno==row['line']and(getattr(node.func,'attr',None)or getattr(node.func,'id',''))==row['call']:
   snippet=ast.get_source_segment(source,node)or''
   if hashlib.sha256(snippet.encode()).hexdigest()==row['siteSHA256']:matches.append(ast.dump(node,include_attributes=False))
 assert len(matches)==1,('writer AST exact site',row)
 return matches[0]
oldAST=sorted((x['module'],x['function'],x['call'],original_writer_ast(oldBase,x))for x in oldpin['sites'])
newAST=sorted((x['module'],x['function'],x['call'],original_writer_ast(base,x))for x in pin['sites'])
assert oldAST==newAST,'writer statement AST changed'
assert pin['envelope']['totalFutureBytes']==60686336 and len(pin['owners'])==14 and pin['envelope']['shutdownReserveBytes']==1048576 and pin['envelope']['ledgerReserveBytes']==131072
actualSourceFiles=[p for p in base.rglob('*')if p.is_file()and'__pycache__'not in p.parts]
assert len(actualSourceFiles)==117 and len(pin['sourceSHA256'])+1==117 and len(graph['pins'])==154 and graph==pin['productInputClosure'] and graph['dynamicDataModulesAllowed']is False and graph['claimsActualAcceptance']is False
sys.dont_write_bytecode=True;os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path.insert(0,str(base.parent))
import aeris_runtime.pipeline_contract as selected_contract
assert Path(selected_contract.__file__).resolve()==base/'pipeline_contract.py','fresh selected contract namespace required'
canonicalContract=selected_contract.require_closed_contract();assert canonicalContract['sourceFiles']==117 and canonicalContract['sites']==200 and canonicalContract['owners']==14 and canonicalContract['futureBytes']==60686336 and canonicalContract['metadataBoundaryClosed']is True
for name,sha in pin['sourceSHA256'].items():assert H(base.parent/name)==sha,('runtime source pin',name)
for name,sha in graph['pins'].items():assert H(R/name)==sha,('product pin',name)
for old,new in iso['mapping'].items():
 assert new in graph['pins'] or new.endswith('verified-loader.mjs'),new
 if old in graph['moduleInputs']:raise AssertionError('replaced executable old module remains selected:'+old)
for name in['assets/resource-policy.json','assets/observer-intervals.txt','metadata_budget.py','pipeline_contract.py','safety.py','admission.py']:
 f=base/name
 if f.exists():assert H(f)==H(oldBase/name),name+' guard changed'
oldWire=R/'planning/betasim-integrated01/runtime/root-wire-media09c.mjs';newWire=P/'runtime/root-wire-media09c.mjs';old=oldWire.read_text();new=newWire.read_text()
for prefix in['  this.watch=setInterval',' async sendManualInput(',' inputGuard(']:
 lines=[x for x in old.splitlines()if x.startswith(prefix)]
 assert len(lines)==1,prefix
 assert lines[0]in new,prefix+' guard/IO method changed'
assert "param2:intervalUs"in new and 'ROOT_TX_INTENT_FSYNC'in new and 'ROOT_RX_ORIGINAL_RECEIPT_AGE_1500MS'in new and 'ROOT_HARD_HEARTBEAT_3000MS'in new
assert 'CAP=8*MIB' in(base/'candidate.py').read_text()
roots=['evidence/runtime-transport15/candidates','evidence/runtime-transport15-atomic-prep/candidates','evidence/betasim-integrated01/candidates','evidence/hosthealth-ipc10/candidates','evidence/hostdiag11/candidates','evidence/vidlife12/candidates'];seen=set();allocated=0;rootCounts={}
for rel in roots:
 root=R/rel
 if not root.exists():
  assert rel=='evidence/vidlife12/candidates';rootCounts[rel]=0;continue
 assert root.is_dir(),rel
 count=0
 for f in[root,*root.rglob('*')]:
  s=f.lstat();assert not stat.S_ISLNK(s.st_mode);assert stat.S_ISDIR(s.st_mode)or stat.S_ISREG(s.st_mode);key=(s.st_dev,s.st_ino);count+=1
  if key not in seen:seen.add(key);allocated+=s.st_blocks*512
 rootCounts[rel]=count
assert allocated<=8*2**20,allocated
mockName=sys.argv[1]if len(sys.argv)>1 else'ADVERSARIAL01.json';outName=sys.argv[2]if len(sys.argv)>2 else'SOURCE-REVIEW01.json'
assert re.fullmatch(r'ADVERSARIAL[0-9]+\.json',mockName)and re.fullmatch(r'SOURCE-REVIEW[0-9]+\.json',outName)
nativeReceipt=R/'evidence/betasim-integrated01/product/native-application09-build01.json';assert H(nativeReceipt)=='e3585254a05626ff10deeab86359a92a43f15828b213fd77dcd70e00e6ba48b0'
native=json.loads(nativeReceipt.read_bytes());assert native['sha256']=='8bc0a7c612c010f77e3e8c66fa6126d1d6992821eafa4f88c31a598bc188b1e1'and H(R/native['apk'])==native['sha256']and H(R/native['inputArchive'])==native['inputArchiveSHA256']and native['productionSigning']is False
qa=E/mockName;v=json.loads(qa.read_bytes());assert v['status']=='PASS_SELECTED_METHOD_MOCK_ONLY_NOT_ANDROID_SITL'and v['actualActors']is False
for row in v['source']:assert H(R/row['path'])==row['sha256'],'mock-selected source drift'
report={'format':'aeris-vidlife12-independent-source-review','status':'PASS_SOURCE_MOCK_GRAPH_CAPS_NOT_ACTUAL_ANDROID_SITL','oldSourceHashesVerified':126,'newRuntimeSources':117,'productPins':154,'changedSelectedFiles':changes,'cumulativeAllocatedArtifactUnionBytes':allocated,'artifactCapBytes':8*2**20,'artifactRootsAndEntryCounts':rootCounts,'guardsUnchanged':['original100msHostHealth','250msclock/input/scene','200msUIlease','1500msflight','3000msheartbeat','speedup1/catchup500ms','fsyncbeforephysicalTX/sensor','allframepolicy','64MiBmetadata/14owners/60686336futurereserve'],'actorsStarted':False,'sourceMutated':False,'mockRef':{'path':str(qa.relative_to(R)),'sha256':H(qa)},'priorFullPreservation':{'path':'evidence/hostdiag11/qa/FINAL-PRESERVATION01.json','sha256':H(R/'evidence/hostdiag11/qa/FINAL-PRESERVATION01.json'),'currentFullOld467Plus270Recheck':'Root final preservation command required; not inferred from this reference'},'canonicalSelectedWriterContract':canonicalContract,'canonicalSelectedModuleOrigin':str(Path(selected_contract.__file__).relative_to(R)),'nativeBuildReceipt':{'path':str(nativeReceipt.relative_to(R)),'sha256':H(nativeReceipt),'APKReusedSHA256':native['sha256'],'nativeSourceSHA256':native['sourceSHA256'],'APKInputsSHA256':native['inputArchiveSHA256'],'newBuildPerformed':False},'actualPayloadFileCount':len(actualSourceFiles),'sourcePinsExcludeOwnPinFile':True,'selectedPinsSHA256':H(base/'assets/pipeline-writer-pins.json'),'selectedGraphSHA256':H(base/'assets/product-input-closure.json')}
out=E/outName;assert not out.exists();out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'artifactUnionBytes':allocated,'changedSelectedFiles':len(changes)}))
