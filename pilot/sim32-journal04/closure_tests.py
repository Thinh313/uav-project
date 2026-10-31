"""Actual owned process signals while waiting/sealing, without SITL."""
from pathlib import Path
import sys,subprocess,socket,time,json,os,signal,struct,hashlib,shutil
from recovery import recover,public
from wal_journal import encode
R=Path(__file__).resolve().parents[2];E=R/'evidence/sim32-journal04';M=R/'pilot/sim32-journal04';results=[]
def wait(fn):
 end=time.monotonic()+4
 while time.monotonic()<end:
  if fn():return
  time.sleep(.005)
 raise RuntimeError('Owned closure observation deadline')
for name,phase,kill in [('stopwaiting03','waiting',False),('stopseal03','seal',False),('killseal03','seal',True)]:
 assert shutil.disk_usage(R).free>20*2**30+768*2**20
 out=E/'cases'/name;out.mkdir();config={'scope':'MOCK_ONLY_NO_SITL'}
 if phase=='seal':config.update(pausePhase='seal',pauseFrame=0)
 (out/'config.json').write_bytes(encode(config));log=(out/'console.txt').open('xb');p=subprocess.Popen([sys.executable,'-B',str(M/'mock_backend.py'),str(out)],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);log.close();received=[]
 try:
  wait(lambda:(out/'ready.json').exists());d=json.loads((out/'ready.json').read_bytes());assert d['pid']==p.pid
  with socket.socket(socket.AF_INET,socket.SOCK_DGRAM)as s:
   s.bind(('127.0.0.1',0));s.settimeout(1)
   if phase=='seal':
    for frame in range(8):
     s.sendto(struct.pack('<HHI16H',18458,1200,frame,*([1150]*4+[1000]*12)),('127.0.0.1',d['port']));packet,addr=s.recvfrom(8192);received.append(packet.decode())
   os.kill(p.pid,signal.SIGTERM)
   if phase=='seal':
    wait(lambda:(out/'paused.json').exists());assert json.loads((out/'paused.json').read_bytes())['pid']==p.pid
    if kill:os.kill(p.pid,signal.SIGKILL)
    else:os.kill(p.pid,signal.SIGINT);os.kill(p.pid,signal.SIGCONT)
   p.wait(timeout=3)
  (out/'receiver.json').write_bytes(encode([{'sensorUtf8':sensor,'source':'MOCK_RECEIVER_OBSERVED','notPhysicalExecution':True}for sensor in received]))
  r=recover(out);assert r['completeAcceptedCapture']is not kill
  assert len(r['sent'])==len(received)and all(x in {i['row']['sensorUtf8']for i in r['intents'].values()}for x in received)
  verdict={'name':name,'status':'PASS','receiverObserved':len(received),'exitCode':p.returncode,'recovery':public(r),'source':'MOCK_ONLY_NO_SITL'};results.append(verdict);(out/'verification.json').write_text(json.dumps(verdict,indent=2)+'\n');print(name,'PASS',flush=True)
 finally:
  if p.poll()is None:os.kill(p.pid,signal.SIGCONT);p.kill();p.wait(timeout=2)
  (out/'closure.json').write_bytes(encode({'ownedPid':p.pid,'processClosed':True,'exitCode':p.returncode,'source':'MOCK_ONLY_NO_SITL'}))
with(E/'closure-tests-receiver-bound.json').open('x')as f:json.dump({'status':'PASS','cases':results},f,indent=2);f.write('\n')
