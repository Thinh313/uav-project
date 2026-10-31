"""Root-only exact-image metadata probe. No AP, clockprobe, socket or subprocess."""
import argparse,copy,hashlib,json,os,pathlib,socket,subprocess,sys,time
from importlib import import_module
NS='planning.betaintegrated01.cockpit05-metaval15'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--fixture',required=True);ap.add_argument('--old-baseline',action='store_true');args=ap.parse_args();folder=pathlib.Path(args.fixture);started=time.monotonic_ns();attempted=[]
 def prohibited(*a,**kw):attempted.append(repr(a)[:256]);raise AssertionError('METADATA_PROBE_PROCESS_OR_SOCKET_PROHIBITED')
 subprocess.Popen=prohibited;socket.socket=prohibited;socket.create_connection=prohibited
 source=pathlib.Path(__file__).resolve().parents[3];fixtureRaw=(folder/'fixture.json').read_bytes();assert len(fixtureRaw)<=131072;fixtureMeta=json.loads(fixtureRaw);assert fixtureMeta.get('format')=='aeris-metaval15-linux-fixture'and type(fixtureMeta.get('version'))is int and fixtureMeta['version']==1
 for name,h in fixtureMeta['fixturePins'].items():
  p=folder/name;assert not pathlib.Path(name).is_absolute()and '..'not in pathlib.Path(name).parts and p.is_file()and not p.is_symlink()and hashlib.sha256(p.read_bytes()).hexdigest()==h
 for name,h in fixtureMeta['sourcePins'].items():
  p=source/name;assert not pathlib.Path(name).is_absolute()and '..'not in pathlib.Path(name).parts and p.is_file()and not p.is_symlink()and hashlib.sha256(p.read_bytes()).hexdigest()==h
 cfg=json.loads((folder/('old-run-config.json'if args.old_baseline else'run-config.json')).read_bytes());cases=[]
 if args.old_baseline:
  try:import_module('planning.betaintegrated01.cockpit05-clockterm14.adapter.ap_supervisor').validate_pre_popen(cfg,candidate=source/'runtime/betaintegrated01/dist',control=source/'pilot/betaintegrated01/cockpit04/profiles',state=folder/'old-state',out=folder/'raw');out={'status':'BASELINE_UNEXPECTED_ACCEPTANCE'}
  except Exception as e:out={'status':'BASELINE_ORIGINAL_IMPORT_FAILURE_REPRODUCED'if isinstance(e,ModuleNotFoundError)and'_sim32_kernel'in str(e)else'BASELINE_OTHER_FAILURE','error':type(e).__name__+':'+str(e)}
 else:
  importStartedNs=time.monotonic_ns();I=import_module(NS+'.native_identity');A=import_module(NS+'.adapter.ap_supervisor');K=import_module(NS+'.adapter.cold');ap_imports=[n for n in sys.modules if n.startswith(NS+'.flight')or n.startswith('pilot.betaintegrated01.runtime.physics')or'.oracles'in n or'.geography'in n];assert not ap_imports,ap_imports;C=import_module(NS+'.flight.contract');importsEndedNs=time.monotonic_ns()
  def check(name,fn,accept):
   failure=None;caseStartedNs=time.monotonic_ns()
   try:value=fn();actual=True
   except Exception as e:actual=False;failure=type(e).__name__+':'+str(e)
   caseEndedNs=time.monotonic_ns();cases.append({'case':name,'accepted':actual,'expected':accept,'error':failure,'startedNs':caseStartedNs,'endedNs':caseEndedNs,'elapsedNs':caseEndedNs-caseStartedNs});assert actual is accept,(name,failure)
   return value if actual else None
  check('shared_native_identity',lambda:I.validate_native_selection(cfg),True);check('flight_contract_same_metadata_identity',lambda:C.validate_native_selection(cfg),True)
  admitted=check('actual_AP_pre_popen_no_effects',lambda:A.validate_pre_popen(cfg,candidate=source/'runtime/betaintegrated01/dist',control=source/'pilot/betaintegrated01/cockpit04/profiles',state=folder/'state',out=folder/'raw'),True)
  launch={**{k:cfg[k]for k in('run','epoch','boot','APSHA256','parameterSHA256')},'stateBinding':admitted['stateBinding'],'command':admitted['command']};raw=json.dumps(launch,separators=(',',':')).encode();assert len(raw)<=16384
  with(folder/'raw/ap-supervisor-launch.json').open('xb')as f:f.write(raw)
  check('cold_same_source_state',lambda:K.verify_observer_capture(folder/'raw',folder/'state',cfg),True)
  mutations=[('wrong_AP',lambda v:v.__setitem__('APSHA256','0'*64)),('wrong_clockprobe',lambda v:v.__setitem__('clockprobeSHA256','0'*64)),('wrong_client',lambda v:v['externalNativeClientSelection'].__setitem__('package','foreign')),('bool_client_version',lambda v:v['externalNativeClientSelection'].__setitem__('version',True)),('missing_client',lambda v:v.pop('externalNativeClientSelection')),('wrong_protocol',lambda v:v['externalNativeClientSelection'].__setitem__('terminalProtocolSHA256','0'*64)),('wrong_host',lambda v:v['externalRecordingPolicy'].__setitem__('amendmentSHA256','0'*64)),('wrong_cadence',lambda v:v['externalObserverRecordingPolicy']['amendment'].__setitem__('fileSHA256','0'*64)),('typed_cap',lambda v:v.__setitem__('capMs',500.0)),('speedup',lambda v:v.__setitem__('requestedSpeedup',2))]
  for name,mutate in mutations:
   bad=copy.deepcopy(cfg);mutate(bad);check(name,lambda bad=bad:A.validate_pre_popen(bad,candidate=source/'runtime/betaintegrated01/dist',control=source/'pilot/betaintegrated01/cockpit04/profiles',state=folder/'state',out=folder/'raw'),False)
  prohibited_modules=[n for n in sys.modules if n.startswith('pilot.betaintegrated01.runtime.physics')or '.oracles' in n or '.geography'in n or n.endswith('._sim32_kernel')or n.startswith('planning.betaintegrated01.cockpit05-clockterm14.flight')]
  assert not prohibited_modules,prohibited_modules
  out={'status':'PASS_EXACT_DOMAIN_METADATA_ONLY_NOT_AP_FLIGHT','cases':cases,'metadataImportsStartedNs':importStartedNs,'metadataImportsEndedNs':importsEndedNs,'metadataImportsElapsedNs':importsEndedNs-importStartedNs,'forbiddenImportModules':prohibited_modules,'APValidatorImportedFlightOrPhysicsModules':ap_imports,'explicitMetadataFlightContractImportedSeparately':True,'sourceSHA256':I.policy().source_binding(),'configSHA256':hashlib.sha256((folder/'run-config.json').read_bytes()).hexdigest(),'nativeBuildReceiptSHA256':I.EXPECTED_BUILD_RECEIPT_SHA256,'hostPolicySHA256':cfg['externalRecordingPolicy']['amendmentSHA256']}
 out.update(startedNs=started,endedNs=time.monotonic_ns(),prohibitedEffectAttempts=attempted,APOrClockprobeStarted=False,networkOrSocketCreated=False,python=sys.version,platform={'sysPlatform':sys.platform,'uname':list(os.uname())if hasattr(os,'uname')else None},machine=os.uname().machine,probeSHA256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),fixture=str(folder),fixtureManifestSHA256=hashlib.sha256(fixtureRaw).hexdigest(),boundedFixtureBytes=sum(p.stat().st_size for p in folder.rglob('*')if p.is_file()),oldSourceEdited=False)
 assert not attempted and out['boundedFixtureBytes']<=262144;print(json.dumps(out,separators=(',',':')),flush=True)
if __name__=='__main__':main()
