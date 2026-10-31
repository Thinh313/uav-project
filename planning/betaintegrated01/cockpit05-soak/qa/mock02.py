"""Small independent adapter mocks; no files copied, services or simulated30mPASS."""
from pathlib import Path
import copy,hashlib,json,importlib.util,sys,ast
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R));p=Path(__file__).with_name('actual_combined_cold.py');spec=importlib.util.spec_from_file_location('cold05',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
old=json.loads((R/'evidence/betaintegrated01-cockpit05-native/android/restart-recovery.json').read_text());initial={line.split('  ',1)[1]:line.split('  ',1)[0]for line in old['afterSHA256Map'].splitlines()};prior=old['state'];current=copy.deepcopy(prior);current['workspace']['draft']['revision']=6
rows=[]
def run(name,mut=None,reject=False):
 i=copy.deepcopy(initial);a=copy.deepcopy(prior);f=copy.deepcopy(initial);b=copy.deepcopy(current)
 if mut:mut(i,a,f,b)
 try:v=m.initial_workspace_preserved(i,a,f,b);passed=not reject
 except(AssertionError,KeyError,TypeError,ValueError):passed=reject
 rows.append({'id':name,'pass':passed})
run('actualAccepted8baselineToSyntheticR6_noRuntimeClaim')
run('lostHistoricalFile',lambda i,a,f,b:f.pop(next(iter(f))),True)
run('changedHistoricalByteSHA',lambda i,a,f,b:f.update({next(iter(f)):'0'*64}),True)
run('wrongSelectedRevision5',lambda i,a,f,b:b['workspace']['draft'].update(revision=5),True)
run('inventedMOCKNativeAnchor',lambda i,a,f,b:b['workspace']['reviews'][0].update(nativeTerminalSHA256='a'*64),True)
run('promotedMOCKCompletion',lambda i,a,f,b:b['workspace']['reviews'][0].update(completionClaim=True),True)
run('removedMOCKSummary',lambda i,a,f,b:b['workspace']['reviews'].pop(),True)
run('restoredAuthority',lambda i,a,f,b:b['workspace'].update(authorityRestorable=True),True)
run('oldMOCKAlreadyPromoted',lambda i,a,f,b:a['workspace']['reviews'][0].update(actualImages=1),True)
assert all(x['pass']for x in rows)
source=p.read_text();ast.parse(source);assert 'cockpit04.revision02' in source and 'm1cockpit04.qa.native_authority02' in source and "E=R/'evidence/betaintegrated01-cockpit05-soak'"in source
oldpins=json.loads((R/'evidence/betaintegrated01-m1cockpit04/qa/FINAL-MOCK-QA.json').read_text())['sourcePins'];assert all(hashlib.sha256((R/path).read_bytes()).hexdigest()==s for path,s in oldpins.items())
result={'status':'PASS_BOUNDED_ADAPTER_MOCK_ACTUAL_NOT_RUN','tests':rows,'frozenPriorQAComponentsSHA256':oldpins,'newCLI_SHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'oldAccepted8BaselineSHA256':hashlib.sha256((R/'evidence/betaintegrated01-cockpit05-native/android/restart-recovery.json').read_bytes()).hexdigest(),'scope':'In-memory preservation negativecases using acceptedoldworkspace shapes; syntheticr6 isnotactualsaveor30min evidence. Originalsixclock/CRC/authority/fullframe components frozen reused; newcompletecaseCLI notexecuted.','servicesStarted':0,'wholeBetaAccepted':False,'actualThirtyMinuteAccepted':False}
O=R/'evidence/betaintegrated01-cockpit05-soak/qa/mock02.json';O.open('x').write(json.dumps(result,indent=2)+'\n');print(result['status'],len(rows))
