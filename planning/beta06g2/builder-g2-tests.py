"""Pure ground-clock/admission and managed-host orchestration mocks. No real runtime."""
from pathlib import Path
import hashlib,importlib.util,json,sys,tempfile,types,unittest,copy,os
from unittest.mock import patch
P=Path(__file__).parent;R=P.parents[1];E=R/'evidence/beta06/generation02'
def load(name,file):
 s=importlib.util.spec_from_file_location(name,P/file);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
cmod=load('g2_ctl_more','qa-root-controller.py');ground=load('g2_ground_more','qa-ground-soak.py')
class Clock:
 def __init__(self):self.t=100.
 def __call__(self):return self.t
 def pause(self,n):self.t+=n

def sample():
 o={'foreground':True,'run':None,'documentId':'doc','clientId':'client','clientEpoch':2,'clientInstance':'instance','configId':'config','modelSha256':'model','planSha256':'plan','seq':1,'observedAtClientMonoMs':10,'lifecycleDiagnostics':{'format':'aeris-beta06g2-lifecycle-diagnostic/1','desiredForeground':True,'documentHidden':False,'nativeForeground':True,'localSessionActive':True,'clientEpoch':2,'counts':{'started':1,'acknowledged':1,'failed':0,'deadline':0}},'mediaReadiness':{'active':True,'clockStatus':'CALIBRATED_BOUNDS','clockDegraded':False,'previewReady':True,'frameAgeMs':10,'clockSessionId':'viewer-one','clockMappingSampledBrowserMs':0,'clockMappingValidUntilBrowserMs':60000}};state={'flight':{'run':None,'authority':None},'client':{'active':True,'id':'client','epoch':2,'instance':'instance','ageMs':10},'payloadLeaseObservation':{'leaseCount':0}};return{'ok':True,'ageMs':0,'observation':o},state

def clock_rows():
 rows=[];head='0'*64;lines=[]
 def add(kind,data,t):
  nonlocal head
  base={'seq':len(rows)+1,'hostMonoMs':t,'kind':kind,'data':data,'previousSha256':head};b=json.dumps(base,separators=(',',':'));head=hashlib.sha256(b.encode()).hexdigest();row={**base,'sha256':head};rows.append(row);lines.append(json.dumps(row,separators=(',',':'))+'\n')
 def event(role,kind,t,reason='PERIODIC_30S'):
  identity={'run':'viewer-one'if role=='viewer'else'publisher-one','boot':'serverboot'if role=='viewer'else'independent-source-boot','configId':'viewer-clock-1'if role=='viewer'else'config','feed':'browser-viewer'if role=='viewer'else'rgb','profileId':'profile'};m={'lowerMs':100,'upperMs':110,'sampledBrowserMs':t,'validUntilBrowserMs':t+60000,'roundtripMs':10};return{'serverBoot':'serverboot','role':role,'event':{'kind':kind,'reason':reason,'atBrowserMs':t,'session':identity,'mapping':m}}
 add('BROWSER_CLOCK_EVENT',event('viewer','CALIBRATION_APPLIED',0,'INITIAL'),0);add('BROWSER_CLOCK_EVENT',event('publisher','CALIBRATION_APPLIED',0,'INITIAL'),1)
 identity={'run':'publisher-one','boot':'independent-source-boot','configId':'config','feed':'rgb','profileId':'profile','viewerId':'viewer-id'};add('SOURCE_CONFIGURED',{'serverBoot':'serverboot','session':identity},2)
 for t in [30000,60000]:
  e=event('publisher','CALIBRATION_APPLIED',t);add('SOURCE_MAPPING_APPLIED',{'serverBoot':'serverboot','configId':'config','sourceClock':e['event']['mapping']},t);add('BROWSER_CLOCK_EVENT',e,t+1);add('BROWSER_CLOCK_EVENT',event('viewer','CALIBRATION_APPLIED',t),t+2)
 return rows,''.join(lines).encode(),''.join(lines[:3]).encode()
class Tests(unittest.TestCase):
 def test_sample_all_bindings_and_zero_new_failure(self):
  v,s=sample();first=ground.sample_decision(v,s);baseline={'counts':first['counts'],'clockSessionId':first['clockSessionId']};ground.sample_decision(v,s,first['binding'],baseline)
  for path,value in [('mediaReadiness.clockSessionId','viewer-other'),('mediaReadiness.clockStatus','UNKNOWN'),('mediaReadiness.frameAgeMs',1001),('lifecycleDiagnostics.counts.failed',1),('clientEpoch',3)]:
   bad=copy.deepcopy(v);obj=bad['observation'];parts=path.split('.')
   for key in parts[:-1]:obj=obj[key]
   obj[parts[-1]]=value
   with self.assertRaises(AssertionError):ground.sample_decision(bad,s,first['binding'],baseline)
 def test_clock_renewal_exact_periodic_mapping_and_role(self):
  rows,_,_=clock_rows();self.assertEqual({k:len(v)for k,v in ground.renewals(rows,3,'viewer-one','config','serverboot').items()},{'viewer':2,'publisher':2})
  for change in ['wrongboot','initial-only','source-unbound','unknown-viewer']:
   bad=copy.deepcopy(rows)
   if change=='wrongboot':bad[-1]['data']['serverBoot']='other'
   if change=='initial-only':bad[-1]['data']['event']['reason']='INITIAL'
   if change=='source-unbound':bad[3]['data']['sourceClock']={**bad[3]['data']['sourceClock'],'upperMs':111}
   if change=='unknown-viewer':bad[-1]['data']['event']['session']['run']='viewer-other'
   with self.assertRaises(AssertionError):ground.renewals(bad,3,'viewer-one','config','serverboot')
 def test_exact_clock_chain_tamper_prefix_and_75s_collection(self):
  rows,full,initial=clock_rows();clock=Clock();clock.t=0
  with tempfile.TemporaryDirectory(prefix='builder-ground-',dir=E)as tmp:
   base=Path(tmp);p=base/'clock.jsonl';p.write_bytes(initial)
   def observation():
    v,_=sample();t=clock.t*1000;v['observation']['observedAtClientMonoMs']=t;v['observation']['mediaReadiness']['clockMappingSampledBrowserMs']=(int(t)//30000)*30000;v['observation']['mediaReadiness']['clockMappingValidUntilBrowserMs']=(int(t)//30000)*30000+60000;return v
   def pause(n):clock.pause(n);p.write_bytes(full if clock.t>=60 else initial)
   ui=types.SimpleNamespace(observation=observation,q=types.SimpleNamespace(state=lambda:sample()[1]))
   with patch.object(ground,'E',base):
    report=ground.collect('ground',p,clock=clock,pause=pause,ui=ui);self.assertGreaterEqual(report['observedPythonSpanS'],75);self.assertEqual(len(report['samples']),151);ground.journal_rows(p);p.write_bytes(full.replace(b'PERIODIC_30S',b'PERIODIC_31S'))
    with self.assertRaisesRegex(AssertionError,'BODY_SHA'):ground.journal_rows(p)
 def test_ground_late_sample_refused_no_late_admission(self):
  rows,full,initial=clock_rows();clock=Clock();clock.t=0
  with tempfile.TemporaryDirectory(prefix='builder-ground-late-',dir=E)as tmp:
   base=Path(tmp);p=base/'clock.jsonl';p.write_bytes(full)
   def observation():clock.t=81;return sample()[0]
   with patch.object(ground,'E',base):
    with self.assertRaisesRegex(AssertionError,'LATE_RESPONSE'):ground.collect('late',p,clock=clock,pause=clock.pause,ui=types.SimpleNamespace(observation=observation,q=types.SimpleNamespace(state=lambda:sample()[1])))
 def test_managed_host_two_processes_one_anchor_direct_child_and_remaining(self):
  clock=Clock();calls=[]
  class Thread:
   def __init__(self,*a,**kw):pass
   def start(self):pass
  class Socket:
   def __enter__(self):return self
   def __exit__(self,*a):pass
   def bind(self,*a):pass
  class Proc:
   def __init__(self,out):self.pid=700+len(calls);self.returncode=None;self.out=out
   def poll(self):return self.returncode
   def terminate(self):self.returncode=0;(self.out/'app-closure.json').write_text(json.dumps({'reason':'EXPLICIT_STOP','payloadEvidenceFailure':None}))
   def wait(self,**k):return self.returncode
  with tempfile.TemporaryDirectory(prefix='builder-managed-host-',dir=E)as tmp:
   base=Path(tmp);(base/'workspace01').mkdir()
   def popen(args,**kw):
    self.assertEqual(args[0],'node');self.assertEqual(int(kw['env']['BETA06_ROOT_CONTROLLER_PID']),os.getpid());out=Path(args[2]);out.mkdir();calls.append((args,kw));return Proc(out)
   ui=types.SimpleNamespace(q=types.SimpleNamespace(state=lambda:{'flight':{'run':None,'authority':None,'busy':False},'payloadLeaseObservation':{'leaseCount':0}}),observation=lambda:{'observation':{'mediaReadiness':{'active':False}}})
   with patch.object(cmod,'E',base),patch.object(cmod.threading,'Thread',Thread),patch.object(cmod.subprocess,'Popen',side_effect=popen),patch.object(cmod.shutil,'disk_usage',return_value=types.SimpleNamespace(free=40*2**30)),patch.object(cmod.time,'sleep',side_effect=clock.pause),patch.object(cmod.socket,'socket',return_value=Socket()):
    c=cmod.Controller('02',boot_reader=lambda:'host',clock=clock,ui=ui);c.start_host({'commandId':'host1','sourceAndViewerStoppedAndInspected':True});anchor=c.host_anchor;self.assertEqual(anchor,130.);c.restart_authorization={'nominalReport':'FAKE','faultReport':'FAKE'};original_module=cmod.module
    def module(name,file):
     return types.SimpleNamespace(authorize=lambda*a,**kw:c.restart_authorization)if file=='qa-restart-proof.py'else original_module(name,file)
    with patch.object(cmod,'module',side_effect=module):c.stop_host({'sourceAndViewerStoppedAndInspected':True});c.start_host({'commandId':'host2','sourceAndViewerStoppedAndInspected':True});self.assertEqual(c.host_anchor,anchor);self.assertEqual(Path(calls[1][0][2]).name,'host-app02-restart');self.assertLess(int(calls[1][1]['env']['BETA06_PARENT_HOST_REMAINING_MS']),int(calls[0][1]['env']['BETA06_PARENT_HOST_REMAINING_MS']));c.stop_host({'sourceAndViewerStoppedAndInspected':True})
    with self.assertRaisesRegex(AssertionError,'TWO_HOST'):c.start_host({'commandId':'host3','sourceAndViewerStoppedAndInspected':True})
    c.close()
 def test_persistence_switch_resets_only_emu_no_host_window(self):
  clock=Clock()
  with tempfile.TemporaryDirectory(prefix='builder-boot03-',dir=E)as tmp:
   base=Path(tmp);(base/'android-closure02.json').write_text('{}')
   with patch.object(cmod,'E',base):
    c=cmod.Controller('02',boot_reader=lambda:'host',clock=clock);c.host_anchor=90.;c.runtime=types.SimpleNamespace(poll=lambda:0);c.launch=lambda q:{'proof':'MOCK_NO_LAUNCH'};c.persistence_boot({});self.assertEqual(c.host_anchor,90.);self.assertEqual(c.attempt,'03');self.assertTrue(c.persistence_only);self.assertIsNone(c.guard.snapshot()['emulatorBeforeLaunchPythonMonoS'])
    with self.assertRaisesRegex(AssertionError,'PERSISTENCE_BOOT03'):c.action({'target':'field-arm','commandId':'forbidden'})
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests));report={'scope':'BUILDER_PURE_G2_MOCK_NO_RUNTIME','pass':result.wasSuccessful(),'tests':result.testsRun,'failures':[(str(t),e)for t,e in result.failures+result.errors]};(E/'builder-g2-tests05.json').open('x').write(json.dumps(report,indent=2)+'\n');sys.exit(0 if result.wasSuccessful()else 1)
