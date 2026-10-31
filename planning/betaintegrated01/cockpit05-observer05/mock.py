"""Small pure file/state/cold contract tests. No AP/device/socket process starts."""
from pathlib import Path
from importlib import import_module
from copy import deepcopy
import json,hashlib,shutil,ast
R=Path(__file__).resolve().parents[3];H='planning.betaintegrated01.cockpit05-observer05';P=import_module(H+'.policy');S=import_module(H+'.state_binding');C=import_module(H+'.cold');E=R/'evidence/betaintegrated01-cockpit05-observer05/host/mock01'
def main():
 E.mkdir(parents=True,exist_ok=False);scratch=E/'scratch';scratch.mkdir();out=scratch/'raw';out.mkdir();state=scratch/'state';cfg=P.build_config(R,'nominal','observer-mock','epoch','boot',out,'observer-mock',maximum_seconds=180);result=[]
 def test(name,fn):
  try:result.append({'case':name,'pass':True,'detail':fn()})
  except Exception as e:result.append({'case':name,'pass':False,'error':repr(e)})
 def refused(fn):
  try:fn()
  except Exception as e:return type(e).__name__+':'+str(e)
  raise AssertionError('badinputaccepted')
 def positive():
  prepared=S.prepare_fresh_case_state(R,state,cfg['caseID']);binding=S.validate_state(cfg,state,out);launch={**{k:cfg[k]for k in('run','epoch','boot','APSHA256','parameterSHA256')},'stateBinding':binding,'command':['/candidate/arducopter-m1-stagepipe-03','--serial0=tcp:5760:nowait','--serial1=tcp:5762:nowait','--serial2=tcp:5763:nowait','--speedup','1']};(out/'ap-supervisor-launch.json').write_text(json.dumps(launch));assert C.verify_observer_capture(out,state,cfg)['passiveApplicationTXBytesPolicy']==0
  assert cfg['externalRecordingPolicy']==P.OLD.amendment();profile=json.loads((R/cfg['referenceProfile']).read_text());assert all(cfg[k]==v for k,v in profile.items());return {'fileSHA256':prepared['intervalsSHA256'],'amendmentSHA256':P.amendment()['amendmentSHA256'],'physicalProfileFieldsUnchanged':len(profile),'oldClockOwnerAmendmentExact':True}
 test('selected AP binary feature and fresh state/launch/cold binding',positive)
 def malformed():
  answers={}
  for label,change in [('boolchannel',lambda a:a['amendment'].__setitem__('channel',True)),('wrongchannel',lambda a:a['amendment'].__setitem__('channel',0)),('wronghash',lambda a:a['amendment'].__setitem__('fileSHA256','0'*64)),('traversal',lambda a:a['amendment'].__setitem__('stateRelativePath','../message-intervals-chan1.txt')),('wrongunits',lambda a:a['amendment']['intervalsMs'].__setitem__('0',200000))]:
   v=deepcopy(cfg);change(v['externalObserverRecordingPolicy']);answers[label]=refused(lambda:P.validate_observer_policy(v))
  return answers
 test('typed config wrong channel/hash/path/microsecond interpretation rejected',malformed)
 def state_fault():
  p=state/'message-intervals-chan1.txt';p.write_bytes(b'0 1000\n245 250\n242 1000\n');a=refused(lambda:S.validate_state(cfg,state,out));b=refused(lambda:C.verify_observer_capture(out,state,cfg));p.write_bytes(P.INTERVAL_BYTES)
  extra=state/'message-intervals-chan0.txt';extra.write_bytes(b'0 1\n');c=refused(lambda:S.validate_state(cfg,state,out));d=refused(lambda:C.verify_observer_capture(out,state,cfg));extra.unlink();return [a,b,c,d]
 test('actual state hash and undeclared extra channel fail before launch and cold',state_fault)
 def launch_fault():
  p=out/'ap-supervisor-launch.json';raw=p.read_bytes();v=json.loads(raw);v['command'][2]='--serial1=tcp:5763:nowait';p.write_text(json.dumps(v));a=refused(lambda:C.verify_observer_capture(out,state,cfg));p.write_bytes(raw)
  v=json.loads(raw);v['stateBinding']['externalObserverRecordingPolicy']['amendmentSHA256']='0'*64;p.write_text(json.dumps(v));b=refused(lambda:C.verify_observer_capture(out,state,cfg));p.write_bytes(raw);return [a,b]
 test('cold mismatched serial mapping and launch amendment reject',launch_fault)
 def source_diff():
  old=(R/'planning/betaintegrated01/cockpit05-clockowner02/runtime/ap_supervisor.py').read_text();new=(Path(__file__).parent/'ap_supervisor.py').read_text();assert new.replace('from .state_binding import validate_state','from pilot.betaintegrated01.control01.state_binding import validate_state')==old
  return 'Supervisor process/drain/clock/command/timeouts exact; only explicit validator import changed'
 test('supervisor source delta minimal exact',source_diff)
 def stretched():
  # Deterministic simulator-time schedule only; not injected actual/raw evidence.
  wall_per_sim=1.743415292;failure_at=1.704379042
  before=max(t*wall_per_sim for t in[0]if t*wall_per_sim<=failure_at);assert failure_at-before>1.5
  after=max(t*.2*wall_per_sim for t in range(6)if t*.2*wall_per_sim<=failure_at);assert failure_at-after<1.5
  return {'syntheticOnly':True,'wallPerSim':wall_per_sim,'oldAgeSeconds':failure_at-before,'newAgeSeconds':failure_at-after,'freshnessThresholdUnchangedSeconds':1.5,'doesNotQualifyOldActual':True}
 test('same measured virtual-time stretch cadence margin without threshold change',stretched)
 removed=sum(p.stat().st_size for p in scratch.rglob('*')if p.is_file());shutil.rmtree(scratch);v={'status':'PASS'if all(x['pass']for x in result)else'FAIL','cases':result,'APBuildLaunchAndroidOrServices':False,'actualCadenceNotObserved':True,'scratchRemoved':True,'removedBytes':removed};(E/'results.json').open('x').write(json.dumps(v,indent=2)+'\n');print(json.dumps(v,indent=2));assert v['status']=='PASS'
if __name__=='__main__':main()
