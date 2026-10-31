"""Small source-bound composed boundary mock. Never starts services, sockets or AP."""
from pathlib import Path
from importlib import import_module
from unittest.mock import patch
import ast,copy,hashlib,json,shutil,sys
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R));H='planning.betaintegrated01.cockpit05-observer11'
P=import_module(H+'.runtime.policy');S=import_module(H+'.adapter.state_binding');AP=import_module(H+'.adapter.ap_supervisor');C=import_module(H+'.adapter.cold')
E=R/'evidence/betaintegrated01-cockpit05-observer11/host';scratch=E/'adapter-mock-scratch01'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run():
 scratch.mkdir(exist_ok=False);raw=scratch/'raw';raw.mkdir();state=scratch/'state';results=[]
 def record(name,fn,expected=True):
  try:value=fn();ok=expected;error=None
  except Exception as e:ok=not expected;error=type(e).__name__+':'+str(e)
  results.append(dict(case=name,pass_=ok,error=error));assert ok,(name,error)
 try:
  cfg=P.build_config(R,'nominal','observer11-synthetic-01','synthetic-epoch','synthetic-boot',raw,'synthetic-case',maximum_seconds=180)
  S.prepare_fresh_case_state(R,state,cfg['caseID']);config=scratch/'config.json';config.write_text(json.dumps(cfg));wireBefore=sha(config)
  def pre(v):return AP.validate_pre_popen(v,candidate=R/'runtime/betaintegrated01/dist',control=R/'pilot/betaintegrated01/cockpit04/profiles',state=state,out=raw)
  admitted=pre(cfg);record('actual_generated_config_real_pre_popen_state',lambda:pre(json.loads(config.read_bytes())))
  # Executable main reaches the pipe boundary only after real selected admission; no pipe/log/process is created.
  calls=[];original=AP.validate_pre_popen
  def admit_actual(v):calls.append('admit');return original(v,candidate=R/'runtime/betaintegrated01/dist',control=R/'pilot/betaintegrated01/cockpit04/profiles',state=state,out=raw)
  def stop_pipe():calls.append('pipe-after-admission');raise RuntimeError('SYNTHETIC_STOP_BEFORE_PIPE_NO_AP')
  with patch.object(AP,'validate_pre_popen',admit_actual),patch.object(AP,'StageDrainer',lambda *a,**kw:calls.append('drainer-after-admission')),patch.object(AP.os,'pipe',stop_pipe),patch.object(AP.subprocess,'Popen',side_effect=AssertionError('NO_PROCESS_ALLOWED')),patch.object(sys,'argv',['supervisor','--config',str(config)]):
   try:AP.main()
   except RuntimeError as e:assert str(e)=='SYNTHETIC_STOP_BEFORE_PIPE_NO_AP'
  record('actual_main_admission_before_all_recording_pipe_popen',lambda:None if calls==['admit','drainer-after-admission','pipe-after-admission']else(_ for _ in()).throw(AssertionError(calls)))
  # Same unchanged exact config now used by cold, with a clearly synthetic launch receipt.
  command=admitted['command'];command[0]='/candidate/arducopter-m1-stagepipe-03'
  launch={k:cfg[k]for k in('run','epoch','boot','APSHA256','parameterSHA256')};launch.update(stateBinding=admitted['stateBinding'],command=command)
  (raw/'ap-supervisor-launch.json').write_text(json.dumps(launch))
  record('same_config_cold_state',lambda:C.verify_observer_capture(raw,state,json.loads(config.read_bytes())))
  for name,mut in [('wrong_top_hash',lambda v:v['externalRecordingPolicy'].update(amendmentSHA256='0'*64)),('wrong_source',lambda v:v['externalRecordingPolicy']['amendment']['sourceSHA256'].update({next(iter(v['externalRecordingPolicy']['amendment']['sourceSHA256'])):'0'*64})),('wrong_channel',lambda v:v['externalObserverRecordingPolicy']['amendment'].update(channel=2)),('typed_speedup_bool',lambda v:v.update(requestedSpeedup=True)),('typed_load',lambda v:v.update(load=True)),('wrong_parameter',lambda v:v['parameterSHA256'].update({'control.parm':'0'*64})),('foreign_case',lambda v:v.update(caseID='foreign'))]:
   v=copy.deepcopy(cfg);mut(v);record(name,lambda v=v:pre(v),False)
  known=json.loads((R/'evidence/betaintegrated01-cockpit05-compact10/actual-short01/raw/run-config.json').read_bytes());record('old_actual_failed_config_not_promoted',lambda:pre(known),False)
  (state/'message-intervals-chan2.txt').write_text('0 200\n');record('undeclared_channel_file',lambda:pre(cfg),False);(state/'message-intervals-chan2.txt').unlink()
  expected=AP.validate_state;call=[]
  def denied(v,*a,**kw):call.append('state-admit');return expected(v,*a,**kw)
  bad=copy.deepcopy(cfg);bad['requestedSpeedup']=True;config.write_text(json.dumps(bad))
  with patch.object(AP,'validate_pre_popen',admit_actual),patch.object(AP,'StageDrainer',side_effect=AssertionError('MUST_NOT_RECORD')),patch.object(AP.os,'pipe',side_effect=AssertionError('MUST_NOT_PIPE')),patch.object(AP.subprocess,'Popen',side_effect=AssertionError('MUST_NOT_PROCESS')),patch.object(sys,'argv',['supervisor','--config',str(config)]):record('bad_config_actual_main_refuses_before_any_sideeffect',AP.main,False)
  config.write_text(json.dumps(cfg));assert sha(config)==wireBefore
  record('actual_cfg_bytes_never_rewritten_for_old_policy',lambda:None if sha(config)==wireBefore else(_ for _ in()).throw(AssertionError('changed')))
  assert len(P.source_binding())==204
  result=dict(status='PASS_COMPOSED_GENERATED_CONFIG_PRE_POPEN_STATE_AND_COLD_MOCK',cases=results,caseCount=len(results),sameConfigSHA256=wireBefore,sourceClosure=204,actualAPStarted=False,actualGuardPrime=False,fixtureType='LOCAL_REAL_FILES_WITH_SYNTHETIC_RUN_STATE_LAUNCH_AND_DENIED_PROCESS_BOUNDARY',sourceSHA256={str(p.relative_to(R)):sha(p)for p in sorted((R/'planning/betaintegrated01/cockpit05-observer11').glob('adapter/*.py'))})
  (E/'adapter-mock01.json').open('x').write(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(status=result['status'],cases=len(results))))
 finally:shutil.rmtree(scratch)
if __name__=='__main__':run()
