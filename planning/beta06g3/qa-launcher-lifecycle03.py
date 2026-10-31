"""Independent scenarios around actual run(); shares Builder fake transport schema only."""
from pathlib import Path
import importlib.util,tempfile,json,datetime,hashlib,os,sys
from unittest.mock import patch
R=Path(__file__).resolve().parents[2];spec=importlib.util.spec_from_file_location('shared_g3_fixture',R/'pilot/beta06g3/test_runtime.py');fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture);m=fixture.m;CID=fixture.CID;RID=fixture.RID;rows=[]
class Runner(fixture.FakeRunner):
 def command(self,argv,label,**kw):
  if self.mode=='metadataoverflow' and label=='running-inspect':
   self.meta.retained=self.meta.limit;raise RuntimeError('CAPTURE_OVERFLOW_METADATA_INDEPENDENT')
  if self.mode=='metadataoverflow' and label=='closure-before':
   self.closure_before_failed=True;raise RuntimeError('CAPTURE_OVERFLOW_CLOSURE_INSPECT_INDEPENDENT')
  if self.mode=='unowned' and label in ['created-inspect','closure-before','terminal-inspect']:
   self.calls.append((label,argv));return json.dumps([{**self.info(),'Name':'/unrelated-container'}])
  return super().command(argv,label,**kw)
 def capture(self,argv,label,kind='meta'):
  c=super().capture(argv,label,kind)
  if label=='attach' and self.mode=='events-overflow':
   for x in self.background:x.failure='CAPTURE_OVERFLOW_EVENTS'
  return c

def exercise(mode,stop=False,clock=None,parent=None):
 with tempfile.TemporaryDirectory(prefix='qa-g3-lifecycle-',dir=R/'evidence/beta06/generation03')as tmp:
  root=Path(tmp);out=root/'evidence/beta06/generation03/flight/runs'/RID;out.mkdir(parents=True);pins=root/'evidence/beta06/generation03/flight-pins.json';pins.write_text('{"files":{}}');(out/'source-pins.json').write_bytes(pins.read_bytes());(out/'request.json').write_text(json.dumps({'run':RID,'mode':'sitl'}));(out/'admission.json').write_text(json.dumps({'durationMs':30001,'samples':[{'freeBytes':35*2**30}for _ in range(31)]}))
  if stop:(out/'stop-request.json').write_text('{}')
  holder=[]
  def factory(diag):
   r=Runner(diag,mode);r.root=root;r.closure_meta=m.Budget(64*1024);r.closure_control=m.Budget(32*1024);holder.append(r);return r
  originals={sig:__import__('signal').getsignal(sig)for sig in [__import__('signal').SIGTERM,__import__('signal').SIGINT]}
  try:
   from contextlib import ExitStack
   with ExitStack()as stack:
    stack.enter_context(patch.object(m,'qualify',return_value={'mode':'0755'}));stack.enter_context(patch.object(m.shutil,'disk_usage',return_value=type('Free',(),{'free':35*2**30})()));stack.enter_context(patch.object(m.time,'sleep',return_value=None))
    if clock:stack.enter_context(patch.object(m.time,'monotonic',side_effect=clock))
    if parent:stack.enter_context(patch.object(m.os,'getppid',side_effect=parent))
    rc=m.run(RID,root=root,runner_factory=factory)
  finally:
   for sig,handler in originals.items():__import__('signal').signal(sig,handler)
  closure=json.loads((out/'closure.json').read_text());calls=holder[0].calls;intent=json.loads((out/'diagnostics/intent.json').read_text())if(out/'diagnostics/intent.json').exists()else{}
  return rc,closure,calls,holder[0].starts,intent

def test(name,fn):
 try:fn();rows.append({'name':name,'status':'PASS'})
 except BaseException as e:rows.append({'name':name,'status':'FAIL','error':str(e)})
def case(mode,expectstop=True):
 rc,c,calls,starts,intent=exercise(mode);assert rc==1;assert c['error'];assert starts<=1;assert not any('rm'in argv or 'prune'in argv for _,argv in calls)
 if expectstop:assert c['stopped']and any(label=='closure-stop'and argv[-1]==CID for label,argv in calls)
 return c,calls,intent

def createfail():
 rc,c,calls,n,_=exercise('createerror');assert rc==1 and n==0 and c['containerId']is None;assert not any(l in ['attach','reboot-attach','closure-stop']for l,_ in calls)
def early():
 rc,c,calls,n,i=exercise('early255');assert rc==1 and n==1;assert '255'in c['error'];assert c['terminalState']['ExitCode']==255 and c['terminalState']['Error']=='permission denied';assert c['containerRetained']and c['stateRetained'];assert any(l=='wait'for l,_ in calls)
def missing():
 rc,c,calls,n,_=exercise('missinginspect');assert rc==1 and n==0;assert c['error']and not c['stopped'];assert not any(l=='closure-stop'for l,_ in calls)
def unowned():
 rc,c,calls,n,_=exercise('unowned');assert rc==1 and n==0;assert not c['ownedIdentityValidated'];assert not any(l=='closure-stop'for l,_ in calls)
def parent():
 rc,c,calls,n,_=exercise('normal',parent=[123,456]);assert rc==1 and 'PARENT_LOST'in c['error']and c['stopped'];assert any(l=='closure-stop'and a[-1]==CID for l,a in calls)
def deadline():
 values=iter(range(0,100000,600));rc,c,calls,n,_=exercise('normal',clock=lambda:next(values));assert rc==1 and 'DEADLINE'in c['error']and c['stopped'];assert n==1

def since():
 rc,c,calls,n,intent=exercise('normal',stop=True);assert rc==0 and n==1 and c['stopped'];events=next(a for l,a in calls if l=='events');assert '--since'in events;since=events[events.index('--since')+1];assert intent.get('eventsSince')==since or intent.get('eventSince')==since;assert events[events.index('--filter')+1]=='container='+CID
for name,fn in [('create_failure_never_starts_or_stops_unknown_container',createfail),('255_early_exit_retains_state_error_exit_wait_no_retry',early),('missing_inspect_is_unknown_and_refuses_start',missing),('wrong_owned_name_never_stopped',unowned),('attach_overflow_still_stops_exact_owned_CID',lambda:case('overflow')),('events_overflow_still_stops_exact_owned_CID',lambda:case('events-overflow')),('metadata_and_closureinspect_overflow_still_stops_prior_bound_CID',lambda:case('metadataoverflow')),('actual_parent_loss_closes_owned_CID',parent),('time_loss_exhausts_original_deadline_without_retry',deadline),('single_start_events_lowerbound_intent_bound_no_delete',since)]:test(name,fn)
report={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_INDEPENDENT_RUN_LIFECYCLE_FAKE_ONLY'if all(x['status']=='PASS'for x in rows)else'FAIL','rows':rows,'sources':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [R/'pilot/beta06g3/flight/runtime.py',R/'pilot/beta06g3/test_runtime.py']},'scope':'Actual run() with shared Builder FakeRunner state/argv schema, independent new overflow/ownership assertions and scenarios. Root/pins/qualification fixtures are synthetic, no command/binary/Docker/ADB/browser/emulator/listener executes. Actual Capture durable-file behavior is covered separately with independent local pipe fakes. Scratch fixtures removed.'}
out=R/'evidence/beta06/generation03/qa-launcher-lifecycle05.json'
with out.open('x')as f:json.dump(report,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
print(json.dumps({'status':report['status'],'groups':len(rows),'failed':[x for x in rows if x['status']=='FAIL']}));assert report['status'].startswith('PASS')
