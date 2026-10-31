"""Single-owner mock process fault matrix; no SITL imports or launches."""
from pathlib import Path
import os,sys,subprocess,json,time,signal,socket,struct,shutil,hashlib,importlib.util
from wal_journal import encode
from recovery import recover,public
R=Path(__file__).resolve().parents[2];E=R/'evidence/sim32-journal04';M=R/'pilot/sim32-journal04';cases=E/'cases';cases.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('immutable_reference',R/'evidence/sim32/source-final/pilot/sim32/physics.py');ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)
results=[];active=None
def wait(fn,seconds=4):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  if fn():return
  time.sleep(.006)
 raise RuntimeError('Mock observation deadline')
def scenario(name,config,action='graceful',frames=12,input_fault=None):
 global active
 assert shutil.disk_usage(R).free>20*2**30+768*2**20
 out=cases/name;out.mkdir();cfg={'scope':'MOCK_ONLY_NO_SITL',**config};(out/'config.json').write_bytes(encode(cfg));log=(out/'console.txt').open('xb');p=subprocess.Popen([sys.executable,'-B',str(M/'mock_backend.py'),str(out)],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);log.close();active=p
 received=[];sender=[];stopped=False;failure=None
 try:
  wait(lambda:(out/'ready.json').exists()or p.poll()is not None);assert p.poll()is None,'Mock backend admission failed'
  ready=json.loads((out/'ready.json').read_bytes());assert ready['pid']==p.pid and ready['source']=='MOCK_ONLY_NO_SITL'
  with socket.socket(socket.AF_INET,socket.SOCK_DGRAM)as s:
   s.bind(('127.0.0.1',0));s.settimeout(.08)
   for index in range(frames):
    if p.poll()is not None:break
    count=index
    if input_fault=='duplicate'and index==3:count=2
    if input_fault=='gap'and index==3:count=4
    if input_fault=='firstnonzero':count=index+2
    raw=struct.pack('<HHI16H',18458,1200,count,*([1150]*4+[1000]*12))
    if input_fault=='malformed'and index==3:raw=raw[:16]
    sender.append({'index':index,'frame':count,'rawHex':raw.hex(),'sendHostNs':time.monotonic_ns(),'source':'MOCK_SENDER_ONLY_NOT_BACKEND_RECEIPT'});s.sendto(raw,('127.0.0.1',ready['port']))
    if cfg.get('pausePhase')and index==cfg.get('pauseFrame',3):
     wait(lambda:(out/'paused.json').exists()or p.poll()is not None);assert p.poll()is None
     paused=json.loads((out/'paused.json').read_bytes());assert paused['pid']==p.pid and paused['phase']==cfg['pausePhase']
     if action=='kill':os.kill(p.pid,signal.SIGKILL);stopped=True
     else:
      if action=='stale-stop':time.sleep(3.2)
      os.kill(p.pid,signal.SIGTERM)
      if action=='repeated':os.kill(p.pid,signal.SIGINT)
      os.kill(p.pid,signal.SIGCONT);stopped=True
    try:
     packet,address=s.recvfrom(8192);assert address==('127.0.0.1',ready['port']);received.append({'frame':count,'sensorUtf8':packet.decode(),'receiverHostNs':time.monotonic_ns(),'domain':'mock-parent-python-monotonic'})
    except socket.timeout:pass
    if stopped or input_fault and index==(0 if input_fault=='firstnonzero'else 3):break
    if config.get('fault')and not received or p.poll()is not None:break
   if not stopped and p.poll()is None:
    time.sleep(.06);os.kill(p.pid,signal.SIGTERM)
   p.wait(timeout=4)
   s.settimeout(.06)
   while True:
    try:packet,address=s.recvfrom(8192);received.append({'frame':'UNASSIGNED_LATE','sensorUtf8':packet.decode(),'receiverHostNs':time.monotonic_ns(),'domain':'mock-parent-python-monotonic'})
    except socket.timeout:break
  before=hashlib.sha256((out/'frames.wal').read_bytes()).hexdigest();r=recover(out);after=hashlib.sha256((out/'frames.wal').read_bytes()).hexdigest();assert before==after
  checks=[]
  def check(label,ok):checks.append({'name':label,'pass':bool(ok)});assert ok,label
  check('read-only recovery',before==after)
  all_sensor={x['row']['sensorUtf8']for x in r['intents'].values()}
  check('every receiver-observed sensor has exact full pre-send WAL intent',all(x['sensorUtf8']in all_sensor for x in received))
  check('no duplicate receiver sensor timestamp',len({json.loads(x['sensorUtf8'])['timestamp']for x in received})==len(received))
  model=ref.Model(json.loads((out/'profile.json').read_bytes()));oracle=0
  for frame,x in sorted(r['intents'].items()):
   _,rate,count,*pwm=struct.unpack('<HHI16H',bytes.fromhex(x['row']['servoHex']));check('unique sequential model frame '+str(frame),count==oracle)
   sensor=model.step(pwm,1/rate);expected='\n'+json.dumps(sensor,separators=(',',':'),allow_nan=False)+'\n';check('immutable exact sensor byte oracle '+str(frame),expected==x['row']['sensorUtf8']);oracle+=1
  fault=config.get('fault');intent_phase=cfg.get('pausePhase')
  expected_complete=action not in ['kill','stale-stop']and not fault or fault in ['wal-short','compressed-short']
  if input_fault or any(k in config for k in ['rawLimit','compressedLimit','walLimit']):expected_complete=False
  check('complete seal only for healthy graceful case',r['completeAcceptedCapture']==expected_complete)
  if action=='kill'and intent_phase in ['intent','wire']:check('unknown send remains unknown after SIGKILL',3 in r['sendOutcomeUnknownFrames'])
  if fault in ['wal-enospc','wal-flush']:check('failed WAL publication barrier blocks target sensor',len(received)==3)
  if fault=='wal-commit':check('sensor survives failure writing send marker',3 in r['intents']and 3 not in r['sent'])
  if action=='stale-stop':check('stale epoch never publishes paused target',len(received)==3)
  if fault in ['queue-full','archive-stall']:check('stalled worker cannot return complete',not r['completeAcceptedCapture'])
  verdict={'name':name,'status':'PASS'if all(x['pass']for x in checks)else'FAIL','checks':checks,'config':cfg,'exitCode':p.returncode,'receiverObservedFrames':len(received),'exactOracleIntentFrames':oracle,'recovery':public(r),'summary':json.loads((out/'summary.json').read_bytes())if(out/'summary.json').exists()else None,'walSha256':before,'freeBytes':shutil.disk_usage(R).free}
  (out/'receiver.json').write_bytes(encode(received));(out/'sender.json').write_bytes(encode(sender));(out/'verification.json').write_text(json.dumps(verdict,indent=2)+'\n');results.append(verdict);print(name,verdict['status'],len(received),r['status'],flush=True)
 except BaseException as e:
  failure=repr(e);(out/'test-failure.json').write_bytes(encode({'error':failure,'source':'MOCK_ONLY_NO_SITL'}));print(name,'FAIL',failure,flush=True);raise
 finally:
  if p.poll()is None:
   os.kill(p.pid,signal.SIGCONT);p.terminate()
   try:p.wait(timeout=2)
   except subprocess.TimeoutExpired:p.kill();p.wait(timeout=2)
  active=None
  (out/'closure.json').write_bytes(encode({'ownedPid':p.pid,'exitCode':p.returncode,'processClosed':True,'faultChild':True,'failedTest':failure,'source':'MOCK_ONLY_NO_SITL'}))
try:
 scenario('healthy08',{},frames=32)
 for phase in ['received','validated','admitted','computed','intent','wire','committed']:
  scenario('stop'+phase+'08',{'pausePhase':phase},action='repeated')
 for phase in ['received','validated','admitted','computed','intent','wire','committed']:
  scenario('kill'+phase+'08',{'pausePhase':phase},action='kill')
 scenario('stalestop08',{'pausePhase':'computed'},action='stale-stop')
 for fault in ['wal-short','wal-zero','compressed-short','compressed-partial','wal-enospc','wal-flush','wal-commit','archive-write','snapshot','archive-close','archive-flush','archive-stall','send-error','send-short']:
  scenario(fault.replace('-','')+'08',{'fault':fault},frames=20)
 scenario('rawquota08',{'rawLimit':12000},frames=20)
 scenario('compressedquota08',{'compressedLimit':131500},frames=20)
 scenario('walquota08',{'walLimit':6500},frames=20)
 scenario('queuefull08',{'fault':'queue-full'},frames=280)
 for invalid in ['duplicate','gap','malformed','firstnonzero']:scenario('input'+invalid+'08',{},input_fault=invalid)
finally:
 (E/'fault-suite-attempt08.json').write_text(json.dumps({'status':'PASS'if len(results)==38 and all(x['status']=='PASS'for x in results)else'PARTIAL','plannedCases':38,'capturedCases':len(results),'cases':[{k:x[k]for k in ['name','status','exitCode','receiverObservedFrames','exactOracleIntentFrames','recovery']}for x in results],'scope':'Mock loopback subprocess fault injection,0SITL; process kill with OS alive, not host power loss','minimumFreeBytes':min([x['freeBytes']for x in results]or[shutil.disk_usage(R).free])},indent=2)+'\n')
