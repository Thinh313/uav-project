"""Independent full-wiring read-only/import mocks. No actual processes, sockets or ADB."""
from pathlib import Path
from importlib import import_module
from unittest.mock import patch
import hashlib,json,sys,subprocess,socket,threading,ast,os
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[5];sys.path.insert(0,str(R));H='planning.betaintegrated01.cockpit05-entry10.full';D=R/'planning/betaintegrated01/cockpit05-entry10/full';E=R/'evidence/betaintegrated01-cockpit05-entry10-flight/qa';tests=[]
def ok(n,v):assert v,n;tests.append({'id':n,'pass':True})
def denied(*a,**k):raise AssertionError('QA_NO_PROCESS_OR_SOCKET')
modules={}
with patch.object(subprocess,'run',denied),patch.object(subprocess,'Popen',denied),patch.object(socket,'socket',denied),patch.object(threading.Thread,'start',denied):
 for name in ['contract','resources','android_guardian','metadata','receiver05','capture_external','make_confirmation','actual_combined_cold','actual_controller','setup_ui']:
  modules[name]=import_module(H+'.'+name)
 ok('All10ImportsNoExecution',True)
 for p in D.glob('*.py'):ast.parse(p.read_text())
 contract=modules['contract'];budget=contract.task_budget(13*2**30);ok('Fullbudget13GiBRefusedNoHard20',budget['admitted']is False and budget['entryBytes']==10*2**30 and budget['requiredFreeBytes']==20178322048)
 cfg=contract.build_config(R,'nominal','cockpit05-entry10-combined-01','epoch','boot',R,'case',maximum_seconds=1960);ok('ConfigExplicitEntry10PhysicalSourceSame',cfg['externalRecordingPolicy']['amendment']['diskGuardPolicy']['entryBytes']==10*2**30 and cfg['requestedSpeedup']==1 and cfg['capMs']==500)
 raw=modules['actual_combined_cold'];newor=import_module('planning.betaintegrated01.cockpit05-entry10.runtime.oracles');oldcombined=import_module('planning.betaintegrated01.m1cockpit04.qa.combined_oracle');oldauth=import_module('planning.betaintegrated01.m1cockpit04.qa.native_authority02')
 ok('ColdUsesStrictNewReceiver',raw.verify_case_long is newor.verify_case_long)
 ok('SixClockAndAuthorityAcceptedFunctionsSameObjects',all(getattr(raw,n)is getattr(oldcombined,n)for n in ['assisted_window','cleanup_witness','qualify_facts','raw_clock_model_window'])and raw.audit is oldauth.audit)
 source=(D/'actual_controller.py').read_text();ok('ControllerExplicitBackendBeforeHostAPBudget',"planning.betaintegrated01.cockpit05-entry10.runtime.backend"in source and 'HOST_WHOLE_BUDGET_ENTRY10_IMMEDIATELY_BEFORE_POPEN'in source and 'AP_WHOLE_BUDGET_ENTRY10_IMMEDIATELY_BEFORE_POPEN'in source and 'min(host_span,guest_span,AP_span)>=1802'in source and '20*2**30'not in source)
 guardian=(D/'android_guardian.py').read_text();ok('GuardianFullInputsAndWholeBudgetBothPrime',guardian.count('contract.verify_full_inputs()')==2 and guardian.count("policy.task_budget(__import__('shutil').disk_usage(R).free)['admitted']")==2 and "scope='ANDROID_SITL_TEST'"in guardian and 'maximumSeconds=5400'in guardian)
 setup=modules['setup_ui'];ok('FullUIHelper5400ScopeBudgetPreservation',setup.E==R/'evidence/betaintegrated01-cockpit05-entry10-flight' and setup.META_CAP==64*2**20 and '5400'in(D/'setup_ui.py').read_text()and 'admission.get(\'fullBudget\''in(D/'setup_ui.py').read_text())
 ok('ResourcesNewGuardExportBound',modules['resources'].DiskGuard is import_module('planning.betaintegrated01.cockpit05-entry10.host.admission').DiskGuard and "'long':168"in(D/'resources.py').read_text()and '192*MIB'in(D/'resources.py').read_text())
# Exactmetadata exclusions tested on tiny ownfixtures, no raw corpus copies.
root=E/'metadata-fixture02';root.mkdir();included=[];excluded=[]
for name,skip in [('actual-combined01/raw/a',True),('actual-combined01/AP-state/a',True),('actual-combined01/control/native-private.tar',True),('actual-combined01/control/other.tar',False),('actual-combined02/raw/a',False),('emulator01/console.txt',False),('host/receipt.json',False)]:
 p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'MOCK');(excluded if skip else included).append(p)
ok('MetadataOnlyExactApprovedExclusions',modules['metadata'].allocated_metadata(root)==sum(p.stat().st_blocks*512 for p in included))
pins={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in D.glob('*.py')};result={'status':'PASS_FULL_ENTRY10_WIRING_IMPORT_SOURCE_MOCK_NOT_RUNTIME','tests':tests,'sourcePins':pins,'scope':'Newcontroller/guardian/resources/coldwrapper code/import/puremetadata only. Frozenphysicalalgorithms andsixclock/authority functions reusedexact; no complete actualraw case executed.','externalProcessOrADBOrSocketCalls':0,'APEmulatorStarts':0,'actualThirtyMinuteAccepted':False,'wholeBetaAccepted':False};(E/'static02.json').open('x').write(json.dumps(result,indent=2)+'\n');print(result['status'],len(tests))
