"""Actual SHA-pinned client/config through real pre-Popen and cold state validators. No processes."""
from pathlib import Path
from importlib import import_module
import json,hashlib,copy,shutil
R=Path(__file__).resolve().parents[3];H='planning.betaintegrated01.cockpit05-clockterm14.flight';C=import_module(H+'.contract');A=import_module(C.OBSERVER+'.ap_supervisor');S=import_module(C.OBSERVER+'.state_binding');K=import_module(C.OBSERVER+'.cold');E=R/C.EVIDENCE/'host';T=E/'selection-scratch01'
def main():
 T.mkdir(exist_ok=False);cases=[]
 def check(name,fn,expected=True):
  error=None
  try:fn();accepted=True
  except Exception as e:accepted=False;error=type(e).__name__+':'+str(e)
  cases.append(dict(case=name,accepted=accepted,expected=expected,error=error));assert accepted is expected,(name,error)
 try:
  for seconds in(180,1960):
   root=T/str(seconds);root.mkdir();state=root/'state';out=root/'raw';out.mkdir();S.prepare_fresh_case_state(R,state,'unit-'+str(seconds))
   cfg=C.build_config(R,'nominal','clockterm14-unit-'+str(seconds),'epoch','boot',out,'unit-'+str(seconds),maximum_seconds=seconds)
   raw=json.dumps(cfg,separators=(',',':')).encode();cfg=json.loads(raw)
   check('actual_native_selection_'+str(seconds),lambda:C.validate_native_selection(cfg))
   admitted=A.validate_pre_popen(cfg,candidate=R/'runtime/betaintegrated01/dist',control=R/'pilot/betaintegrated01/cockpit04/profiles',state=state,out=out)
   launch={**{k:cfg[k]for k in('run','epoch','boot','APSHA256','parameterSHA256')},'stateBinding':admitted['stateBinding'],'command':admitted['command']}
   (out/'ap-supervisor-launch.json').write_text(json.dumps(launch))
   check('real_supervisor_state_to_cold_'+str(seconds),lambda:K.verify_observer_capture(out,state,cfg))
   assert json.dumps(cfg,separators=(',',':')).encode()==raw
   for name,fn in [('wrong_client',lambda v:v['externalNativeClientSelection'].__setitem__('package','vn.rtr.aeris.cockpitio10')),('typed_cap',lambda v:v.__setitem__('capMs',500.0)),('wrong_host_top',lambda v:v['externalRecordingPolicy'].__setitem__('amendmentSHA256','0'*64))]:
    bad=copy.deepcopy(cfg);fn(bad);check(name+'_'+str(seconds),lambda bad=bad:C.validate_native_selection(bad),False)
   bad=copy.deepcopy(cfg);bad['externalObserverRecordingPolicy']['amendment']['fileSHA256']='0'*64
   check('wrong_cadence_'+str(seconds),lambda:S.validate_state(bad,state,out),False)
  modules=[]
  for p in sorted(Path(C.__file__).parent.glob('*.py')):import_module(H+'.'+p.stem);modules.append(p.stem)
  result=dict(status='PASS_ACTUAL_SELECTED_NATIVE_CONFIG_SUPERVISOR_COLD_MOCK',cases=cases,inputs=len(C.build_receipt()['sourcePins']),allInertImports=len(modules),selectedBuildReceiptSHA256=C.EXPECTED_BUILD_RECEIPT_SHA256,APK_SHA256=C.APK_SHA256,sourceSHA256=C.SOURCE_SHA256,protocolSHA256=C.native_selection()['cancellationProtocolSHA256'],inputAdmissionProtocolSHA256=C.native_selection()['inputAdmissionProtocolSHA256'],sourceSHA256Map=C.selected_sources(),provenance='REAL_SOURCE_VALIDATION_REAL_CACHED_AP_ARTIFACT_HASHES_SYNTHETIC_CASE_STATE_AND_LAUNCH_RECEIPT_NO_POPEN',actualRuntime=False,deviceCommands=False,actualGuardPrime=False,frozenModulesPatched=False,rawConfigUnchanged=True,scratchRemoved=True)
  (E/'selection-unit01.json').open('x').write(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(status=result['status'],cases=len(cases),imports=len(modules))))
 finally:shutil.rmtree(T)
if __name__=='__main__':main()
