"""Source/mock only. Fake Popen and Docker responses; no subprocess is executed."""
import importlib.util,os,json,tempfile,unittest,hashlib
from pathlib import Path
from unittest.mock import patch
R=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('g6runtime',R/'pilot/beta06g6/flight/runtime.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
CID='a'*64;RID='s'+'b'*20
class PipeProcess:
 def __init__(self,argv,**kw):
  self.held=[];self.code=255 if 'early255' in argv else 0
  for name,data in [('stdout',b'prefix-output'),('stderr',b'OCI permission denied')]:
   r,w=os.pipe();os.write(w,data);os.close(w);setattr(self,name,os.fdopen(r,'rb',buffering=0))
 def poll(self):return self.code
 def terminate(self):self.code=-15
 def kill(self):self.code=-9
 def wait(self,timeout):return self.code
class FakeCap:
 def __init__(self,runner,label,argv):
  self.runner=runner;self.label=label;self.argv=argv;self.finished=False;self.failure=None;self.proc=self;self.code=None if label in ['events','attach','reboot-attach'] else 0
  for stream in ['stdout','stderr']:(runner.out/(label+'-'+stream+'.bin')).write_bytes(b'')
  if label=='attach':
   if runner.mode=='early255':self.code=255
   elif runner.mode=='overflow':self.failure='CAPTURE_OVERFLOW'
   text=b'Waiting for connection\n' if runner.mode not in ['early255','overflow','deadline-ready','parent-ready'] else b'OCI permission denied\n'
   (runner.out/'attach-stdout.bin').write_bytes(text)
   if runner.mode not in ['early255','overflow','deadline-ready','parent-ready']:(runner.out/'attach-stderr.bin').write_bytes(b'SERIAL0 on TCP port 5760\n')
 def pump(self,t=0):
  if self.failure:raise RuntimeError(self.failure)
 def poll(self):return self.code
 def finish(self,terminate=False):
  self.finished=True;self.code=-15 if terminate else self.code
  m.put(self.runner.out/(self.label+'-result.json'),{'error':self.failure,'returncode':self.code})
  return {'error':self.failure}
class FakeRunner:
 def __init__(self,out,mode):
  self.out=out;self.mode=mode;self.calls=[];self.meta=m.Budget(m.META);self.event=m.Budget(m.META);self.attached={'stdout':m.Budget(m.STREAM),'stderr':m.Budget(m.STREAM)};self.background=[];self.running=False;self.starts=0
 def info(self):
  # actual fake root assigned by factory below
  return {'Id':CID,'Name':'/aeris-beta06g6-'+RID,'Image':m.IMAGE_ID,'Config':{'Labels':{'aeris.task':'beta06g6','aeris.run':RID},'Cmd':['/aeris/arducopter','--model','quad','--speedup','1','--home','10.854,106.807,10,0','--defaults','/aeris/copter.parm,/task/sitl.parm'],'Env':['AERIS_DIRECT_TRACE=0'],'Entrypoint':None},'HostConfig':{'LogConfig':{'Type':'json-file','Config':{'max-size':'2m','max-file':'2'}},'AutoRemove':False,'Privileged':False,'CapAdd':None,'NanoCpus':1000000000,'Memory':268435456,'CapDrop':['ALL'],'SecurityOpt':['no-new-privileges'],'NetworkMode':'bridge'},'Mounts':[{'Destination':'/aeris/arducopter','Source':str(self.root/'.local/beta06g3/arducopter'),'Type':'bind','RW':False}],'State':{'Running':self.running,'Pid':123 if self.running else 0,'StartedAt':'2026-10-22T08:00:00Z','ExitCode':255 if self.mode=='early255' else 0,'OOMKilled':False,'Error':'permission denied' if self.mode=='early255' else '', 'FinishedAt':'2026-10-22T08:00:01Z'},'SizeRw':1024}
 def command(self,argv,label,**kw):
  self.calls.append((label,argv))
  if self.background and any(c.failure for c in self.background):raise RuntimeError('BACKGROUND_SUPPRESSED_CLOSURE')
  text=''
  if label=='retained-ids':text=''
  elif label=='image':text=json.dumps([{'Id':m.IMAGE_ID,'Architecture':'arm64','Os':'linux','Config':{'Entrypoint':None,'Env':[]}}])
  elif label=='create':
   if self.mode=='createerror':
    (self.out/'create-stderr.bin').write_bytes(b'OCI create failed');m.put(self.out/'create-result.json',{'returncode':125});raise RuntimeError('COMMAND_FAILED:create')
   text=CID
  elif 'inspect' in label or label in ['closure-before','terminal-inspect'] or label.startswith('reboot-'):
   if self.mode=='missinginspect' and 'inspect' in label:raise RuntimeError('COMMAND_FAILED:'+label)
   text=json.dumps([self.info()])
  elif label.startswith('poll'):text=json.dumps(self.info()['State'])
  elif label.startswith('usage'):text='1024'
  elif label in ['closure-stop','reboot-stop']:self.running=False;text=CID
  elif label=='wait':text='255' if self.mode=='early255' else '0'
  (self.out/(label+'-stdout.bin')).write_text(text);m.put(self.out/(label+'-result.json'),{'returncode':0,'argv':argv});return text
 def capture(self,argv,label,kind='meta'):
  self.calls.append((label,argv))
  if label=='events' and self.mode=='capturefail':raise RuntimeError('SPAWN_OR_CAPTURE_FAILED')
  c=FakeCap(self,label,argv)
  if label in ['attach','reboot-attach']:self.starts+=1;self.running=self.mode!='early255'
  return c
 def tick(self):
  for c in self.background:c.pump()
class Tests(unittest.TestCase):
 def test_capture_255_durable(self):
  with tempfile.TemporaryDirectory(prefix='codex-tmp-g6-launch-20261022-',dir=R/'evidence/beta06/generation06') as d:
   c=m.Capture(['early255'],Path(d)/'x',{'stdout':m.Budget(100),'stderr':m.Budget(100)},popen=PipeProcess)
   while not c.complete():c.pump()
   r=c.finish();self.assertEqual(r['returncode'],255);self.assertTrue(r['fsynced']);self.assertEqual((Path(d)/'x-stderr.bin').read_bytes(),b'OCI permission denied')
 def test_overflow_prefix_observed(self):
  with tempfile.TemporaryDirectory(prefix='codex-tmp-g6-launch-20261022-',dir=R/'evidence/beta06/generation06') as d:
   c=m.Capture([],Path(d)/'x',{'stdout':m.Budget(4),'stderr':m.Budget(4)},popen=PipeProcess)
   with self.assertRaisesRegex(RuntimeError,'OVERFLOW'):c.pump()
   r=c.finish();self.assertTrue(any(x['overflow'] for x in r['streams'].values()));self.assertLessEqual(sum(x['retainedBytes'] for x in r['streams'].values()),8)
 def test_spawn_failure_receipt(self):
  with tempfile.TemporaryDirectory(prefix='codex-tmp-g6-launch-20261022-',dir=R/'evidence/beta06/generation06') as d:
   with self.assertRaises(OSError):m.Capture([],Path(d)/'x',{'stdout':m.Budget(4),'stderr':m.Budget(4)},popen=lambda *a,**kw:(_ for _ in ()).throw(OSError('denied')))
   self.assertIn('SPAWN_OR_CAPTURE_FAILED',json.loads((Path(d)/'x-result.json').read_text())['error'])
 def exercise(self,mode,stop=False,extra_patch=None):
  with tempfile.TemporaryDirectory(prefix='codex-tmp-g6-launch-20261022-',dir=R/'evidence/beta06/generation06') as d:
   root=Path(d);out=root/'evidence/beta06/generation06/flight/runs'/RID;out.mkdir(parents=True);pins=root/'evidence/beta06/generation06/flight-pins.json';pins.write_text('{"files":{}}');(out/'source-pins.json').write_bytes(pins.read_bytes());(out/'request.json').write_text(json.dumps({'run':RID,'mode':'sitl'}));(out/'admission.json').write_text(json.dumps({'durationMs':30001,'samples':[{'freeBytes':35*2**30} for _ in range(31)]}))
   if stop:(out/'stop-request.json').write_text('{}')
   holder=[]
   def factory(p):r=FakeRunner(p,mode);r.root=root;holder.append(r);return r
   with patch.object(m,'qualify',return_value={'mode':'0755'}),patch.object(m.shutil,'disk_usage',return_value=type('D',(),{'free':35*2**30})()),patch.object(m.time,'sleep',return_value=None):
    if extra_patch:
     with extra_patch:rc=m.run(RID,root=root,runner_factory=factory)
    else:rc=m.run(RID,root=root,runner_factory=factory)
   closure=json.loads((out/'closure.json').read_text());return rc,closure,holder[0].calls,holder[0].starts
 def test_early255_stop_wait_retained(self):
  rc,c,calls,starts=self.exercise('early255');self.assertEqual(rc,1);self.assertTrue(c['containerRetained']);self.assertEqual(starts,1);self.assertIn('255',c['error']);self.assertIn('wait',[x[0] for x in calls]);self.assertEqual(c['terminalState']['ExitCode'],255);self.assertTrue(any('--since' in a for _,a in calls))
 def test_create_error_closure(self):
  rc,c,calls,starts=self.exercise('createerror');self.assertEqual(rc,1);self.assertIsNone(c['containerId']);self.assertEqual(starts,0)
 def test_missinginspect_no_start(self):
  rc,c,calls,starts=self.exercise('missinginspect');self.assertEqual(rc,1);self.assertEqual(starts,0);self.assertIn('wait',[x[0] for x in calls])
 def test_capturefail_no_start(self):
  rc,c,calls,starts=self.exercise('capturefail');self.assertEqual(rc,1);self.assertEqual(starts,0);self.assertTrue(c['stopped'])
 def test_overflow_cannot_suppress_exact_stop(self):
  rc,c,calls,starts=self.exercise('overflow');self.assertEqual(rc,1);self.assertIn('closure-stop',[x[0] for x in calls]);self.assertTrue(c['stopped']);self.assertEqual([a[-1] for l,a in calls if l=='closure-stop'],[CID])
 def test_success_retained_single_start(self):
  rc,c,calls,starts=self.exercise('normal',stop=True);self.assertEqual(rc,0);self.assertEqual(starts,1);self.assertTrue(c['stopped']);self.assertFalse(any('rm' in a or 'prune' in a for _,a in calls))
 def test_parent_loss_stop(self):
  rc,c,calls,starts=self.exercise('normal',extra_patch=patch.object(m.os,'getppid',side_effect=[10,11]));self.assertEqual(rc,1);self.assertIn('PARENT_LOST',c['error']);self.assertTrue(c['stopped'])
 def test_deadline_stop(self):
  values=iter(range(0,100000,600))
  rc,c,calls,starts=self.exercise('normal',extra_patch=patch.object(m.time,'monotonic',side_effect=lambda:next(values)));self.assertEqual(rc,1);self.assertIn('DEADLINE',c['error']);self.assertTrue(c['stopped'])
 def test_four_retained_cap(self):
  row={'Id':CID,'Name':'/aeris-beta06g6-'+RID,'Config':{'Labels':{'aeris.task':'beta06g6','aeris.run':RID}},'State':{'Running':False},'SizeRw':0,'HostConfig':{'LogConfig':{'Type':'json-file','Config':{'max-size':'2m','max-file':'2'}}}}
  with self.assertRaisesRegex(ValueError,'FOUR'):m.inventory_guard([row]*4,RID)
  with self.assertRaisesRegex(ValueError,'DUPLICATE'):m.inventory_guard([row],RID)
 def test_exact_metadata_rejects_old_profile(self):
  r=FakeRunner(Path('/unused'),'normal');r.root=Path('/aeris');i=r.info();i['HostConfig']['AutoRemove']=True
  with self.assertRaisesRegex(ValueError,'RESOURCES'):m.identity(i,CID,RID,r.root/'.local/beta06g3/arducopter')
if __name__=='__main__':unittest.main()
