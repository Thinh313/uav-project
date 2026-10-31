from pathlib import Path
import sys,json,hashlib,importlib.util,resource,time
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[6];sys.path.insert(0,str(R));Q=Path(__file__).parent;P=Q/'model_clock_prefix.py';spec=importlib.util.spec_from_file_location('prefixqa',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
B=R/'evidence/betaintegrated01-cockpit05-entry10-flight/actual-combined01';C=B/'control';D=B/'raw';O=R/'evidence/betaintegrated01-cockpit05-entry10-flight/qa/actual-prefix01';began=time.monotonic()
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
cfg=json.loads((D/'run-config.json').read_text());ap=json.loads((C/'container-control-stdout.txt').read_text().splitlines()[-1]);ctx=[cfg[k]for k in('run','epoch','boot')]
try:
 proof=m.verify_prefix(D,*ctx,expected_host_anchor=None,expected_stage_anchor=ap['terminalSHA256'],load=cfg['load'],wind=cfg['wind'],seed=cfg['seed']);N=proof['completeFrames'];coverage=0;group=None;kinds=[];tail=None;eventcount=0;legal=([10,11,12,13,14,20,21,24],[10,11,12,13,14,20,21,22,23,24])
 def finish(frame,k):
  global coverage,tail
  if frame<N:assert frame==coverage and k in legal;coverage+=1
  else:
   assert frame==N and k[:3]==[10,11,12];assert all(kind==(10 if i%2==0 else 11)for i,kind in enumerate(k[3:]));tail=dict(frame=frame,kinds=k,classification='FINAL_UNKNOWN_SEND_COMPUTED_INTENT_AP_SENSOR_ADVANCE_NOT_OBSERVED',groundOrFlightClaim=False)
 for p in sorted((D/'ap-stage').glob('stage-*.bin')):
  with p.open('rb')as f:
   f.readline(4097)
   while True:
    raw=f.read(m.EVENT.size)
    if not raw:break
    assert len(raw)==m.EVENT.size
    seq,frame,kind,tid,begin,end,arg,extra,result=m.EVENT.unpack(raw);eventcount+=1
    if group is not None and frame!=group:finish(group,kinds);kinds=[]
    group=frame;kinds.append(kind)
 if group is not None:finish(group,kinds)
 assert coverage==N and eventcount==proof['APstage']['events']
 proof.update(APCoveredCompletePrefixFrames=coverage,APRawEventsIterated=eventcount,APUnknownTail=tail,status='FAILED_CASE_INCOMPLETE_PREFIX_MODEL_CLOCK_AP_COVERAGE_VERIFIED',unknownTailComputedModelSteps=1,committedHostJournal=False,externallyAnchoredHostJournal=False,APForcedExitNeverGroundProof=True,actualThirtyMinuteAccepted=False,wholeBetaAccepted=False,caseRunConfigSHA256=sha(D/'run-config.json'),externalAPStdoutSHA256=sha(C/'container-control-stdout.txt'),derivedSourceSHA256=sha(P),durationSeconds=time.monotonic()-began,peakRSSBytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
 (O/'model-clock-AP.json').open('x').write(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:proof[k]for k in ['status','completeFrames','unknownTailComputedModelSteps','APRawEventsIterated','durationSeconds','peakRSSBytes']}))
except BaseException as e:
 (O/'model-clock-AP-failure.json').open('x').write(json.dumps({'error':repr(e),'elapsedSeconds':time.monotonic()-began,'status':'QA_COLD_FAILURE_NOT_PROMOTED','sourceSHA256':sha(P),'actual30minAccepted':False},indent=2)+'\n');raise
