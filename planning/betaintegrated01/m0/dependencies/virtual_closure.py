"""Static virtual Native98 input closure and disposition; no product execution."""
from pathlib import Path
import json,hashlib,ast,re,datetime,subprocess
R=Path(__file__).resolve().parents[4];P=R/'planning/betaintegrated01/m0/dependencies';E=R/'evidence/betaintegrated01-m0/dependencies';N=R/'native/native98';A=N/'assets';J=N/'src/vn/rtr/aeris/native98'
sha=lambda b:hashlib.sha256(b).hexdigest()
pin=lambda p:{'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}
audit=json.loads((E/'source-reference-union01.json').read_text());receipt=json.loads((R/'evidence/native98/build02.json').read_text());intake=audit['intake'][0];body=R/intake['intakePath'];assert sha(body.read_bytes())=='b881e15a33e92634ded232fc25b43693e558b662a36dd82571300899d261da7d'
missingNames=['native/native98/assets/direct95/vendor/pilot/apstream40/definitions.mjs','native/native98/assets/workflow/preflight/definitions.mjs']
bindings={n:{'inputPath':intake['intakePath'],'expectedSHA256':receipt['sourceFiles'][n],'bindingKind':'EXACT_GIT_INTAKE_FOR_MISSING_HISTORICAL_PROJECTION'}for n in missingNames}
assert all(v['expectedSHA256']==intake['sha256']for v in bindings.values())
resourceIntake=[]
for dest,origin in [
 ('native/native98/assets/assets/camera-concept.png','native/cockpit85/assets/assets/camera-concept.png'),
 *[('native/native98/assets/fonts/Barlow-'+w+'.ttf','pilot/visual56/assets/fonts/Barlow-'+w+'.ttf')for w in ['Bold','Medium','SemiBold']]]:
 expected=receipt['sourceFiles'][dest];b=subprocess.check_output(['git','show',audit['sourceCommit']+':'+origin],cwd=R);assert sha(b)==expected
 ip=P/'intake'/origin;ip.parent.mkdir(parents=True,exist_ok=True);ip.open('xb').write(b)
 row={'originalMissingPath':dest,'originGitPath':origin,'gitCommit':audit['sourceCommit'],'gitBlob':subprocess.check_output(['git','rev-parse',audit['sourceCommit']+':'+origin],cwd=R).decode().strip(),'inputPath':str(ip.relative_to(R)),'bytes':len(b),'sha256':expected,'originalPathRestored':False};resourceIntake.append(row);bindings[dest]={'inputPath':row['inputPath'],'expectedSHA256':expected,'bindingKind':'EXACT_GIT_INTAKE_FOR_MISSING_HISTORICAL_ASSET'};missingNames.append(dest)
(E/'resource-intake01.json').open('x').write(json.dumps({'exactResourceIntake':resourceIntake,'definitionSourceIntake':intake,'totalActualCopiedBytes':intake['bytes']+sum(v['bytes']for v in resourceIntake),'oldPathsRestored':False},indent=2)+'\n')
files={}
for p in sorted(A.rglob('*')):
 if p.is_file():files[str(p.relative_to(R))]={**pin(p),'bindingKind':'PRESENT_STATIC_ASSET','selectedForM1SourceAdaptation':True}
for n,b in bindings.items():files[n]={'path':n,'bytes':(R/b['inputPath']).stat().st_size,'sha256':b['expectedSHA256'],**b,'selectedForM1SourceAdaptation':True}
java=[]
tree=ast.parse((N/'build.py').read_text());lists=[]
for n in ast.walk(tree):
 if isinstance(n,ast.List)and len(n.elts)>10 and all(isinstance(e,ast.Constant)and isinstance(e.value,str)and e.value.endswith('.java')for e in n.elts):lists.append([e.value for e in n.elts])
assert len(lists)==1;apkJava=set(lists[0]);assert all((J/n).is_file()for n in apkJava)
for p in sorted(J.glob('*.java')):java.append({**pin(p),'historicalBuildRole':'EXPLICIT_APK_JAVA_LIST'if p.name in apkJava else'HOST_TEST_OR_UNSELECTED_JAVA_SOURCE','selectedForExecution':False,'androidImport':bool(re.search(r'\bandroid\.',p.read_text()))})
manifest=pin(N/'AndroidManifest.xml')
edges=[];unresolved=[];routeRefs=[]
def resolve(src,literal,line,kind):
 if not literal or literal.startswith(('#','data:','http:','https:','javascript:')):return
 if literal.startswith('/')or'${'in literal:
  routeRefs.append({'from':src,'line':line,'literal':literal,'kind':kind,'status':'EXPLICIT_ROUTER_OR_RUNTIME_CONTEXT_REQUIRED_NOT_ASSET_FILE'});return
 path=(R/src).parent/literal
 try:target=str(path.resolve().relative_to(R))
 except ValueError:unresolved.append({'from':src,'line':line,'literal':literal,'status':'ESCAPES_CHECKOUT'});return
 if (R/target).is_dir():
  edges.append({'from':src,'line':line,'target':target,'kind':kind,'status':'DIRECTORY_ANCHOR_NOT_EXECUTABLE'});return
 if target not in files:
  unresolved.append({'from':src,'line':line,'literal':literal,'target':target,'status':'NOT_IN_VIRTUAL_NATIVE_ASSET_MAP'});return
 edges.append({'from':src,'line':line,'target':target,'kind':kind,'status':'BOUND_EXACT_BYTES'})
esm=re.compile(r"\b(?:import|export)\s+(?:[^;\n]*?\bfrom\s*)?(['\"])(\.[^'\"]+)\1")
newurl=re.compile(r"new\s+URL\(\s*(['\"])(\.[^'\"]+)\1\s*,\s*import\.meta\.url")
for n,v in files.items():
 if Path(n).suffix not in ['.mjs','.js','.html','.css']:continue
 p=R/v.get('inputPath',n);text=p.read_text()
 if Path(n).suffix in ['.mjs','.js']:
  for pattern,kind in [(esm,'DIRECT_STATIC_ESM'),(newurl,'STATIC_IMPORT_META_URL')]:
   for m in pattern.finditer(text):resolve(n,m[2],text.count('\n',0,m.start())+1,kind)
 if Path(n).suffix=='.html':
  for m in re.finditer(r"(?:src|href)\s*=\s*(['\"])([^'\"]*)\1",text):resolve(n,m[2],text.count('\n',0,m.start())+1,'HTML_STATIC_RESOURCE')
 if Path(n).suffix=='.css':
  for m in re.finditer(r"url\(\s*['\"]?([^)'\"]+)['\"]?\s*\)",text):resolve(n,m[1],text.count('\n',0,m.start())+1,'CSS_STATIC_RESOURCE')
assert not unresolved,unresolved
q={'format':'aeris-beta-m0-virtual-native-source-input-closure','version':1,'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'STATIC_NATIVE_SOURCE_INPUTS_BOUND_FOR_ADAPTATION_NOT_EXECUTABLE_RELEASE','sourceCommit':audit['sourceCommit'],'historicalBuildRecipe':pin(N/'build.py'),'historicalBuildRecipeExecuted':False,'selectedManifest':manifest,'javaInputs':java,'javaInputCount':len(java),'explicitHistoricalAPKJavaCount':len(apkJava),'virtualAssetMap':files,'virtualAssetCount':len(files),'exactBindingsForMissingAssets':bindings,'staticAssetEdges':edges,'unresolvedDirectStaticImportsOrResources':unresolved,'runtimeRouteReferences':routeRefs,'OperationGateDisposition':'No OperationGate.java exists in Native98. The actual gates are NativeSend98/WireGate95/UnifiedCore98 and FileGate91; MissionBeta OperationGate belongs to different companion shell. Do not invent or mix the classes.','generatedBuildInput':{'name':'BuildInfo90.java','historicalRecipe':'Build sourceId from explicit source/assets hashes; write constants class during new isolated build','notMaterializedNow':True},'selectedPythonBuildRuntimeLaunchers':[],'knownPlatformRestrictions':['ShellActivity requires ranchu and observed owned AP identity','DirectTransport95 opens10.0.2.2:5937 and rejects reopening sameActivity','JS socket.mjs expects127.0.0.1:5937 logicalendpoint','Existing provider is internalquad/AP011627d4…, not SIMSTABILITY03 externalphysics/APf2be1f34…'],'runtimeAPKAccepted':False,'fullBetaRunnableClosureAccepted':False,'nextStep':'M1 materializes versioned explicit provider, lifecycle and build manifest; do not run historical build/exec projections blindly.'}
(P/'native98-virtual-input-closure.json').open('x').write(json.dumps(q,indent=2)+'\n');(E/'native98-virtual-input-closure01.json').open('x').write(json.dumps(q,indent=2)+'\n')
# Bind each original union issue, with conservative directory anchors separated from missing executable code.
routeMap={'clock-lifecycle.mjs':'pilot/clockvideo05/media/clock-lifecycle.mjs','network-bootstrap.mjs':'pilot/clockvideo05/media/network-bootstrap.mjs','client.mjs':'pilot/clockvideo05/media/client.mjs','relay-core.mjs':'media/big02/relay-core.mjs'}
dispositions=[]
for u in audit['unresolvedOrGeneratedSelections']:
 d=dict(u);target=u['path'];name=Path(target).name
 if target in bindings:d.update(disposition='BOUND_VIRTUAL_MISSING_NATIVE_ASSET',binding=bindings[target])
 elif u['status']=='DIRECTORY_SELECTION_REQUIRES_MANIFEST_NOT_EXPANDED':d.update(disposition='ROOT_OR_OUTPUT_DIRECTORY_ANCHOR_NOT_A_MISSING_MODULE',executionSelection='NOT_SELECTED')
 elif name in routeMap and u['from'].startswith(('pilot/missionbeta01/','pilot/betavideo03/')):
  p=R/routeMap[name];assert p.is_file();d.update(disposition='HTTP_ASSET_ROUTER_BINDING_NOT_NEIGHBOR_FILE',binding=pin(p),recipeEvidence=['pilot/beta06g5/media/server.mjs:83-86','pilot/betavideo03/media-projection.mjs:31','pilot/missionbeta01/media-projection.mjs:15'],materializationNeeded='New media module graph must make these explicit imports/resources; existing source is browser-served, not Node-importable in place')
 elif target=='snapshots/simstability03/pilot/simtrain53/authority.mjs':
  p=R/'pilot/simtrain53/authority.mjs';assert p.is_file();d.update(disposition='VIRTUAL_OVERLAY_INHERITS_ORIGINAL_LOGICAL_PATH',binding=pin(p),materializationNeeded='Resolve imports at logical pilot/simhand01 location; snapshot directory is archival overlay, not runnable module root')
 else:d.update(disposition='ACTUAL_UNRESOLVED_INPUT_REQUIRES_M1_REPAIR',executionSelection='BLOCKED')
 dispositions.append(d)
assert len(dispositions)==37
recipes=[
 {'id':'PR01','recipe':'Native98 APK source generation','inputs':[pin(N/'build.py'),manifest],'behavior':'Directory sourceId scan + explicit Java list + copyassets; generated BuildInfo90.java + Android toolchain; no projection recipe run','requiredM1Action':'Replace historical output/evidence/signing paths with explicit new manifest and injected provider; preserve v26 API compatibility gate; no old buildCLI'},
 {'id':'PR02','recipe':'Workbench UI projection','inputs':[pin(R/'pilot/workbench02/project-ui.mjs'),pin(R/'pilot/workbench01/ui.mjs'),pin(R/'evidence/workbench01/handoff-manifest.json')],'behavior':'Pinned asset text edits, count/inverse assertions, projected modules/HTML; not executed here','requiredM1Action':'Materialize standalone versioned UI/domain modules; keep one Fly owner and native transport delegate'},
 {'id':'PR03','recipe':'MissionBeta/BetaVideo UI projection','inputs':[pin(R/'pilot/missionbeta01/ui-projection.mjs'),pin(R/'pilot/betavideo03/ui-projection.mjs')],'behavior':'Composes Workbench projection and injects BetaWorkbench host session control','requiredM1Action':'Do not include host flight writer; adapt mission/media/review domain behind native flight service'},
 {'id':'PR04','recipe':'Media server runtime projection','inputs':[pin(R/'pilot/betavideo03/media-projection.mjs'),pin(R/'pilot/beta06g5/media/server.mjs'),pin(R/'evidence/beta06/generation17/flight-pins01.json')],'behavior':'Rewrites historical media server roots/importURLs/routes and imports data:text/javascript code at runtime','requiredM1Action':'Extract explicit new media host modules and literal HTTP asset map from pinned source; no opaque data import in selected release'},
 {'id':'PR05','recipe':'MissionBeta runtime exec','inputs':[pin(R/'pilot/missionbeta01/runtime.py'),pin(R/'pilot/beta06g17/flight/runtime.py'),pin(R/'evidence/missionbeta01/source-pins07.json')],'behavior':'Rewrites frozenG17 source string and exec(compiles) it with new output guards','requiredM1Action':'Excluded as beta executor; implement/pin new explicit simulator provider launcher/context if preserving algorithm'},
 {'id':'PR06','recipe':'SIMSTABILITY03 archival overlay','inputs':[pin(R/'snapshots/simstability03/overlay.json'),pin(R/'snapshots/simstability03/source-bundle-manifest.json')],'behavior':'9changed files; inherits unchanged original source/resources. Includes independent host TrainingLink flight authority','requiredM1Action':'Port manual/lifecycle/recorder algorithms into native-owner architecture; host TrainingLink cannot remain second live writer'}]
disp={'status':'ALL37_UNION_ISSUES_DISPOSITIONED_NOT_RUNTIME_ACCEPTANCE','unresolvedOriginalCount':len(dispositions),'dispositions':dispositions,'actualUnresolvedInputs':[d for d in dispositions if d['disposition']=='ACTUAL_UNRESOLVED_INPUT_REQUIRES_M1_REPAIR'],'projectionRecipes':recipes,'sourceOfCounts':'source-reference-union01.json; directory anchors were not missing executable modules'}
(P/'projection-and-unresolved-disposition.json').open('x').write(json.dumps(disp,indent=2)+'\n');(E/'projection-and-unresolved-disposition01.json').open('x').write(json.dumps(disp,indent=2)+'\n')
# Narrow pure-Java source input closure for mock adaptation. No compile, JVM, native or socket execution.
classMap={p.stem:p for p in J.glob('*.java')};pending=['NativeSend98','UnifiedCore98','RawJournal95'];selected={}
while pending:
 name=pending.pop()
 if name in selected:continue
 p=classMap[name];text=p.read_text();assert not re.search(r'\bandroid\.',text),('ANDROID_DEP_IN_MOCK_CLOSURE',name);selected[name]=pin(p)
 for other in classMap:
  if other!=name and re.search(r'\b'+re.escape(other)+r'\b',text):pending.append(other)
mock={'status':'PURE_JAVA_SOURCE_REFERENCE_CLOSURE_FOR_M1_MOCKS_NO_EXECUTION','inputs':list(selected.values()),'classCount':len(selected),'method':'Conservative same-package class token references, all resolved and no android import; stdlib/JDK external','systemPrerequisite':'Pinned JDK --release8 from root config; no compile done here','notIncluded':['DirectTransport95 Socket/Android activity','historical Python launcher or buildCLI','AP/native binary','private keys','competing host GCS writer'],'mockOrBuildExecuted':False,'furtherM1Work':'New provider/state/clock/recorder tests must be implemented against explicit seams; unchanged source presence is not test PASS'}
(P/'m1-mock-java-inputs.json').open('x').write(json.dumps(mock,indent=2)+'\n');(E/'m1-mock-java-inputs01.json').open('x').write(json.dumps(mock,indent=2)+'\n')
assert all(not(R/n).exists()for n in missingNames)
verification={'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'M0_SOURCE_INPUT_BINDINGS_VERIFIED_NOT_RUNTIME_CLOSURE','nativeJavaSourceInputs':len(java),'explicitHistoricalAPKJavaInputs':len(apkJava),'virtualStaticAssets':len(files),'directStaticResourceEdges':len(edges),'directStaticUnresolved':len(unresolved),'boundMissingNativeDefinitions':2,'boundMissingNativeAssets':len(bindings),'oneGitIntakeBytes':body.stat().st_size,'unionIssuesDispositioned':len(dispositions),'actualUnresolvedFromUnion':len(disp['actualUnresolvedInputs']),'projectionRecipes':len(recipes),'mockJavaSourceInputCount':len(selected),'oldSourceOrEvidenceModified':False,'historicalOriginalMissingPathsRestored':False,'productCodeImportedOrExecuted':False,'builds':0,'runtimeLaunches':0,'fullBetaRunnableClosureAccepted':False}
(E/'verification01.json').open('x').write(json.dumps(verification,indent=2)+'\n');print(json.dumps(verification,indent=2))
