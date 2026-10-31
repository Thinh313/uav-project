"""Independent source/mock corrective readiness and launcher injection review."""
from pathlib import Path
import importlib.util,sys,json,hashlib,datetime,tempfile,os,signal,ast
from unittest.mock import patch
from contextlib import ExitStack
R=Path(__file__).resolve().parents[2];E=R/'evidence/beta06/generation04';E.mkdir(exist_ok=True)
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
ready=load('independent_g4_readiness',R/'pilot/beta06g4/flight/readiness.py');m=load('independent_g4_runtime',R/'pilot/beta06g4/flight/runtime.py');fixture=load('independent_shared_g4_fixture',R/'planning/beta06g4/test_runtime_integration.py');CID=fixture.old.CID;RID=fixture.old.RID;rows=[]
A=R/'evidence/beta06/generation03/flight/runs/se15994472d0e479cbaa8/diagnostics';stdout=(A/'attach-stdout.bin').read_bytes();stderr=(A/'attach-stderr.bin').read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest()
def test(name,fn):
 try:fn();rows.append({'name':name,'status':'PASS'})
 except BaseException as e:rows.append({'name':name,'status':'FAIL','error':str(e)})
def observer():return ready.SerialReadiness('qa-current')
def feed(o,s,b):o.feed(s,b,attempt='qa-current')
def expect(fn):
 try:fn()
 except (ValueError,RuntimeError):return
 raise AssertionError('EXPECTED_FAIL_CLOSED')
def actual():
 assert len(stdout)==249 and len(stderr)==52 and sha(stdout)=='6f5fef9764e13e7484e4be40c812b3f652af844dc12b3059e460509af5db5f4b'and sha(stderr)=='ffe95324bf34cd63a9db2563464393511fa78ddd6436dfc41f5cc3b3320153d3';o=observer();feed(o,'stdout',stdout);feed(o,'stderr',stderr);assert not all(v in stdout for v in ready.MARKERS.values())and o.ready(alive=True);p=o.proof(alive=True)
 for name,data,stream in [('waiting',stdout,'stdout'),('serial0',stderr,'stderr')]:assert p['markers'][name]['stream']==stream and p['markers'][name]['offsetBytes']==data.index(ready.MARKERS[name])and p['streams'][stream]['retainedPrefixSha256']==sha(data)
def splits():
 # Every nonempty split of each marker, with the other marker supplied separately.
 for stream in ['stdout','stderr']:
  for name,marker in ready.MARKERS.items():
   other=next(v for k,v in ready.MARKERS.items()if k!=name)
   for n in range(1,len(marker)):
    o=observer();feed(o,stream,b'prefix'+marker[:n]);feed(o,stream,marker[n:]);feed(o,stream,b'\n'+other);assert o.ready(alive=True);assert o.proof(alive=True)['markers'][name]['offsetBytes']==6

def crossed():
 for name,marker in ready.MARKERS.items():
  other=next(v for k,v in ready.MARKERS.items()if k!=name)
  for n in range(1,len(marker)):
   o=observer();feed(o,'stdout',other+b'\n'+marker[:n]);feed(o,'stderr',marker[n:]);assert not o.ready(alive=True)
def reset():
 a=observer();feed(a,'stdout',ready.MARKERS['waiting']);b=ready.SerialReadiness('qa-new');b.feed('stderr',ready.MARKERS['serial0'],attempt='qa-new');assert not a.ready(alive=True)and not b.ready(alive=True);expect(lambda:b.feed('stdout',ready.MARKERS['waiting'],attempt='qa-current'));assert not b.ready(alive=True)
def death():
 o=observer();feed(o,'stdout',stdout);feed(o,'stderr',stderr)
 for alive in [False,None,1,'True']:expect(lambda:o.proof(alive=alive))
def bounds():
 o=observer();feed(o,'stdout',stdout);feed(o,'stderr',stderr)
 while o.counts['stdout']<ready.STREAM_BYTES:feed(o,'stdout',b'x'*min(ready.CHUNK_BYTES,ready.STREAM_BYTES-o.counts['stdout']))
 assert all(len(t)<=ready.TAIL_BYTES for t in o.tails.values());expect(lambda:feed(o,'stdout',b'x'));expect(lambda:o.proof(alive=True))
 o=observer();expect(lambda:feed(o,'stdout',b'x'*(ready.CHUNK_BYTES+1)));assert o.counts['stdout']==0

def chunkboundary():
 o=observer();marker=ready.MARKERS['waiting'];feed(o,'stdout',b'x'*(ready.CHUNK_BYTES-7)+marker[:7]);feed(o,'stdout',marker[7:]);feed(o,'stderr',ready.MARKERS['serial0']);p=o.proof(alive=True);assert p['markers']['waiting']['offsetBytes']==ready.CHUNK_BYTES-7
 # Marker proof remains anchored after its text is evicted from a bounded tail.
 for _ in range(10):feed(o,'stdout',b'z'*ready.CHUNK_BYTES)
 assert marker not in o.tails['stdout'];assert o.proof(alive=True)['markers']['waiting']==p['markers']['waiting']
for name,fn in [('actual_immutable249_52_oldfalse_newtrue_exactstreamoffsetSHA',actual),('same_stream_every_marker_split_position',splits),('cross_stream_every_fragment_split_never_invents_marker',crossed),('fresh_attempt_or_mismatch_cannot_pool_marker_fragments',reset),('dead_or_nonboolean_alive_never_accepts_complete_stale_text',death),('2MiB_overflow_latches_failure_64KiBchunks_tailsbounded',bounds),('64KiB_boundary_and_evictedtail_marker_provenance',chunkboundary)]:test(name,fn)

# Shared Builder fake Docker record schema; independent runtime failure injection/assertions.
class Runner(fixture.G4FakeRunner):
 def capture(self,argv,label,kind='meta'):
  c=super().capture(argv,label,kind)
  if label=='attach':
   (self.out/'attach-stdout.bin').write_bytes(stdout);(self.out/'attach-stderr.bin').write_bytes(stderr)
   if self.mode=='dead-with-complete-text':c.code=255;self.running=False
   if self.mode=='cross-stream':(self.out/'attach-stdout.bin').write_bytes(ready.MARKERS['waiting']+b'\nSERIAL0 on TCP port 57');(self.out/'attach-stderr.bin').write_bytes(b'60')
  return c
 def command(self,argv,label,**kw):
  if self.mode=='wrong-live-cid'and label=='running-inspect':
   self.calls.append((label,argv));return json.dumps([{**self.info(),'Id':'b'*64}])
  if self.mode=='dies-during-inspect'and label=='running-inspect':
   for c in self.background:
    if c.label=='attach':c.code=255
  return super().command(argv,label,**kw)

def exercise(mode,deadclock=False):
 with tempfile.TemporaryDirectory(prefix='qa-g4-correction-',dir=E)as tmp:
  root=Path(tmp);out=root/'evidence/beta06/generation04/flight/runs'/RID;out.mkdir(parents=True);pins=root/'evidence/beta06/generation04/flight-pins.json';pins.write_text('{"files":{}}');(out/'source-pins.json').write_bytes(pins.read_bytes());(out/'request.json').write_text(json.dumps({'run':RID,'mode':'sitl'}));(out/'admission.json').write_text(json.dumps({'durationMs':30001,'samples':[{'freeBytes':35*2**30}for _ in range(31)]}));(out/'stop-request.json').write_text('{}');held=[]
  def factory(diag):
   f=Runner(diag,mode);f.root=root;held.append(f);return f
  oldSignals={sig:signal.getsignal(sig)for sig in [signal.SIGTERM,signal.SIGINT]}
  try:
   with ExitStack()as patches:
    patches.enter_context(patch.object(m,'qualify',return_value={'mode':'0755'}));patches.enter_context(patch.object(m.shutil,'disk_usage',return_value=type('Disk',(),{'free':35*2**30})()));patches.enter_context(patch.object(m.time,'sleep',return_value=None))
    if deadclock:
     ticks=iter(range(0,100000,10));patches.enter_context(patch.object(m.time,'monotonic',side_effect=lambda:next(ticks)))
    rc=m.run(RID,root=root,runner_factory=factory)
  finally:
   for sig,handler in oldSignals.items():signal.signal(sig,handler)
  proof=json.loads((out/'guest-ready.json').read_text())if(out/'guest-ready.json').exists()else None;launch=json.loads((out/'launch.json').read_text())if(out/'launch.json').exists()else None;closure=json.loads((out/'closure.json').read_text());return rc,proof,launch,closure,held[0].calls,held[0].starts

def positive():
 rc,p,l,c,calls,n=exercise('normal');assert rc==0 and n==1 and c['stopped']and p['containerId']==l['containerId']==CID
 assert p['proof']['attempt']=='attach:'+CID and p['proof']['markers']['waiting']['stream']=='stdout'and p['proof']['markers']['serial0']['stream']=='stderr'
 for stream,data in [('stdout',stdout),('stderr',stderr)]:v=p['proof']['streams'][stream];assert v['retainedPrefixBytes']==len(data)and v['retainedPrefixSha256']==sha(data)and v['path']=='diagnostics/attach-'+stream+'.bin'and v['captureFsyncedBeforeRead']is True
 assert l['qualifiedProfile']=='beta06g4-native-arm64-exec-4.7.1'and l['labels']=={'aeris.task':'beta06g4','aeris.run':RID}and l['containerName']=='aeris-beta06g4-'+RID
 assert not any('rm'in argv or'prune'in argv for _,argv in calls)
def negative(mode,fragment=False):
 rc,p,l,c,calls,n=exercise(mode,fragment);assert rc==1 and p is None and l is None and n==1;assert c['containerId']==CID and c['containerRetained']and c['stopped'];assert any(label=='closure-stop'and argv[-1]==CID for label,argv in calls)or mode=='dead-with-complete-text'

def retained():
 f=Runner(Path('/unused'),'normal');f.root=Path('/ROOT');i=f.info();i['State']['Running']=False;i['SizeRw']=100
 m.inventory_guard([],RID)
 # Four retained records must refuse before allocation; a duplicate existing own run refuses.
 expect(lambda:m.inventory_guard([i]*4,RID));expect(lambda:m.inventory_guard([i],RID))
 for field in ['name','task','running','size','logs']:
  x=json.loads(json.dumps(i));x['Config']['Labels']['aeris.run']='s'+'c'*20;x['Name']='/aeris-beta06g4-s'+'c'*20
  if field=='name':x['Name']='/aeris-beta06g3-s'+'c'*20
  if field=='task':x['Config']['Labels']['aeris.task']='beta06g3'
  if field=='running':x['State']['Running']=True
  if field=='size':x['SizeRw']=64*2**20+1
  if field=='logs':x['HostConfig']['LogConfig']['Type']='unbounded'
  expect(lambda:m.inventory_guard([x],RID))
def metadata():
 f=Runner(Path('/unused'),'normal');f.root=Path('/ROOT');i=f.info();m.identity(i,CID,RID,f.root/'.local/beta06g3/arducopter')
 for change in [lambda x:x.update(Id='b'*64),lambda x:x.update(Name='/aeris-beta06g3-'+RID),lambda x:x['Config']['Labels'].update({'aeris.task':'beta06g3'}),lambda x:x['HostConfig'].update(AutoRemove=True),lambda x:x['HostConfig'].update(Memory=512*2**20),lambda x:x['Config'].update(Env=['AERIS_DIRECT_TRACE=1'])]:
  x=json.loads(json.dumps(i));change(x);expect(lambda:m.identity(x,CID,RID,f.root/'.local/beta06g3/arducopter'))
for name,fn in [('runtime_actual_split_stream_fixture_exactproof_andG4namespace',positive),('runtime_complete_stale_text_with_deadattach_never_ready',lambda:negative('dead-with-complete-text')),('runtime_attachdies_during_runninginspect_never_ready',lambda:negative('dies-during-inspect')),('runtime_wrong_live_CID_never_launches_and_owned_cleanupretained',lambda:negative('wrong-live-cid')),('runtime_crossstream_fragments_timeout_no_ready_no_retries',lambda:negative('cross-stream',True)),('G4explicit_four_retained_duplicate_namespace_log_size_guards',retained),('G4explicit_exactCID_task_profile_and_resource_rejection',metadata)]:test(name,fn)
# Confirm security/retention/deadline/capture functions are text-exact after namespace normalization.
g3=(R/'pilot/beta06g3/flight/runtime.py').read_text();g4=(R/'pilot/beta06g4/flight/runtime.py').read_text();t3=ast.parse(g3);t4=ast.parse(g4)
nodes=lambda tree:{n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
n3,n4=nodes(t3),nodes(t4)
def normalized():
 for name in ['sha','put','utc','qualify','Budget','Capture','Runner']:
  assert ast.dump(n3[name],include_attributes=False)==ast.dump(n4[name],include_attributes=False),name
 for name in ['identity','request_cap','inventory_guard']:
  a=ast.get_source_segment(g3,n3[name]).replace('beta06g3','beta06g4').replace('G3','G4');b=ast.get_source_segment(g4,n4[name]);assert a==b,name
 # Closure, resource guards and reboot blocks remain literal G3 after exact namespace normalization.
 for start,end in [("  rebooted=False;next_inspect=0",' except BaseException as ex:error=str(ex)'),(' except BaseException as ex:error=str(ex)',"if __name__=='__main__':")]:
  assert g3[g3.index(start):g3.index(end)].replace('.local/beta06g3/arducopter','__FROZEN_EXECUTABLE__').replace('generation03','generation04').replace('beta06g3','beta06g4').replace('__FROZEN_EXECUTABLE__','.local/beta06g3/arducopter')==g4[g4.index(start):g4.index(end)]
test('normalized_capture_qualification_identity_resource_reboot_cleanup_unchanged',normalized)
report={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_INDEPENDENT_SOURCE_MOCK_G4_CORRECTION_ONLY'if all(r['status']=='PASS'for r in rows)else'FAIL','classification':'SOURCE_MOCK_ONLY_NOT_RUNTIME_NOT_WIRED','sources':{str(p.relative_to(R)):sha(p.read_bytes())for p in [R/'pilot/beta06g4/flight/runtime.py',R/'pilot/beta06g4/flight/readiness.py',R/'planning/beta06g4/test_runtime_integration.py']},'rows':rows,'actualRegressionInputs':{'stdout':{'bytes':len(stdout),'sha256':sha(stdout)},'stderr':{'bytes':len(stderr),'sha256':sha(stderr)}},'limits':['Pure marker tests use alive=True as a mock argument, not actual guest proof.','Runtime injection reuses Builder G3/G4 fake Docker record schema; independent injections/assertions verify provenance/death/CID/retention. No real process/command.','The2excluded Builder regression methods are explicitly replaced here with G4 retained-cap and exact-metadata cases.','No actual G4request, pins, app/controllerwiring, AP/Android/Docker/listener or flight acceptance.']}
out=E/'qa-correction-review02.json'
with out.open('x')as f:json.dump(report,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
print(json.dumps({'status':report['status'],'groups':len(rows),'failed':[r for r in rows if r['status']=='FAIL']}));assert report['status'].startswith('PASS')
