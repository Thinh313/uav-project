"""Independent actual G3 Capture/Runner failure tests, only local pipes/fake Popen."""
from pathlib import Path
import importlib.util,json,hashlib,datetime,tempfile,os,sys
R=Path(__file__).resolve().parents[2];source=R/'pilot/beta06g3/flight/runtime.py';s=importlib.util.spec_from_file_location('independent_g3_capture',source);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);rows=[]

def fake(stdout=b'',stderr=b'',code=0,spawn_failure=False):
 def popen(*a,**kw):
  if spawn_failure:raise OSError('MOCK_CREATE_SPAWN_FAILURE')
  class Proc:
   def __init__(self):
    self.code=code
    for name,data in [('stdout',stdout),('stderr',stderr)]:
     rd,wr=os.pipe();os.write(wr,data);os.close(wr);setattr(self,name,os.fdopen(rd,'rb',buffering=0))
   def poll(self):return self.code
   def terminate(self):self.code=-15
   def kill(self):self.code=-9
   def wait(self,timeout):return self.code
  return Proc()
 return popen

def test(name,fn):
 try:fn();rows.append({'name':name,'status':'PASS'})
 except BaseException as e:rows.append({'name':name,'status':'FAIL','error':str(e)})

def command_case(root,label,stdout,stderr,code,expected,spawn_failure=False):
 original=m.Capture
 m.Capture=lambda argv,base,budgets:original(argv,base,budgets,popen=fake(stdout,stderr,code,spawn_failure))
 try:
  runner=m.Runner(root)
  try:runner.command(['MOCK_DOCKER','create'],label)
  except (OSError,RuntimeError):assert expected=='FAIL'
  else:assert expected=='PASS'
 finally:m.Capture=original
 receipt=json.loads((root/(label+'-result.json')).read_text());assert receipt['argv']==['MOCK_DOCKER','create']and receipt['fsynced']is True
 for stream,data in [('stdout',stdout),('stderr',stderr)]:
  b=(root/(label+'-'+stream+'.bin')).read_bytes();assert b==data and receipt['streams'][stream]['sha256']==hashlib.sha256(b).hexdigest();assert receipt['streams'][stream]['retainedBytes']==len(data)
 assert receipt['returncode']==(None if spawn_failure else code)
 return receipt

with tempfile.TemporaryDirectory(prefix='qa-g3-capture-',dir=R/'evidence/beta06/generation03')as tmp:
 root=Path(tmp)
 test('create_failure125_retains_stdout_stderr_returncode_fsync_digest',lambda:command_case(root,'create125',b'partial cid\n',b'OCI failed permission\n',125,'FAIL'))
 test('early_exit255_retains_exact_stderr_and_status',lambda:command_case(root,'exit255',b'',b'exec /aeris/arducopter: permission denied\n',255,'FAIL'))
 test('successful_command_keeps_both_streams',lambda:command_case(root,'success',b'a'*64+b'\n',b'warning\n',0,'PASS'))
 test('Popen_failure_retains_empty_streams_and_null_returncode',lambda:command_case(root,'spawnfail',b'',b'',0,'FAIL',True))
 def overflow():
  c=m.Capture(['MOCK_DOCKER','start','--attach','a'*64],root/'overflow',{'stdout':m.Budget(128),'stderr':m.Budget(128)},popen=fake(b'x'*1024,b'failure\n',255))
  try:
   while not c.complete():c.pump(0)
  except RuntimeError as e:assert str(e)=='CAPTURE_OVERFLOW'
  else:raise AssertionError('OVERFLOW_NOT_REJECTED')
  result=c.finish();b=(root/'overflow-stdout.bin').read_bytes();assert b==b'x'*128;assert result['error']=='CAPTURE_OVERFLOW';assert result['streams']['stdout']['observedBytes']==1024;assert result['streams']['stdout']['retainedBytes']==128;assert result['streams']['stdout']['overflow'];assert result['streams']['stdout']['sha256']==hashlib.sha256(b).hexdigest()
 test('overflow_keeps_bounded_prefix_observed_count_and_fails_loud',overflow)
 def aggregate():
  budgets={'stdout':m.Budget(150),'stderr':m.Budget(150)}
  for n in range(2):
   c=m.Capture(['MOCK_CAPTURE',str(n)],root/('aggregate'+str(n)),budgets,popen=fake(b'a'*100))
   try:
    while not c.complete():c.pump(0)
   except RuntimeError:assert n==1
   result=c.finish()
  assert budgets['stdout'].retained==150 and budgets['stdout'].observed==200;assert result['error']=='CAPTURE_OVERFLOW'
 test('shared_stream_budget_cannot_reset_on_reboot_or_recovery',aggregate)
 def qualifies():
  original=R/'evidence/sim32-instrument01/direct-uncorrected-source/arducopter';prepared=R/'.local/beta06g3/arducopter'
  try:m.qualify(original)
  except ValueError as e:assert '0755'in str(e)
  else:raise AssertionError('IDENTICAL0644_ACCEPTED')
  x=m.qualify(prepared);assert x['sha256']==m.BINARY and x['mode']=='0755'and x['descriptorBound']is True
 test('real_descriptor_qualification_refuses0644_accepts0755_no_execution',qualifies)
report={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_INDEPENDENT_ACTUAL_CAPTURE_FAKE_PROCESS_ONLY'if all(x['status']=='PASS'for x in rows)else'FAIL','sources':{str(source.relative_to(R)):hashlib.sha256(source.read_bytes()).hexdigest()},'rows':rows,'scope':'Actual Capture+Runner.command with local OS pipes and fake process objects; actual durable prefix files and receipt digests verified. No Docker, ADB, browser, listener, emulator, artifact exec or build. Qualify metadata is structural only, no AP boot/cause claim. Scratch directory removed by TemporaryDirectory.'}
out=R/'evidence/beta06/generation03/qa-launcher-capture05.json'
with out.open('x')as f:json.dump(report,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
print(json.dumps({'status':report['status'],'groups':len(rows),'failures':[r for r in rows if r['status']=='FAIL']}));assert report['status'].startswith('PASS')
