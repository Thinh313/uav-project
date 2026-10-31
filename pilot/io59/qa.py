"""Bounded real UDP/mock faults, exact original numeric oracle and durable barrier."""
from pathlib import Path
import socket,struct,subprocess,time,sys,json,os,signal,importlib.util
R=Path(__file__).resolve().parents[2];E=R/'evidence/io59';attempt=sys.argv[1];assert attempt.isalnum();sys.path[:0]=[str(R/'pilot/simtrain53'),str(R/'pilot/sim32-journal04')]
from readback import records
from wal_journal import encode,unpack_intent
from instrument import TimedWal as Wal
sys.path.insert(0,str(R/'pilot/pace58'))
from tuning import encoder
checks=[]
def ck(name,value):
 checks.append({'name':name,'pass':bool(value)});assert value,name
def probe(rid,mode,variant='normal'):
 rid=attempt+rid;out=E/'mock'/rid;out.mkdir(parents=True);(out/'request.json').write_text(json.dumps({'load':'offset','wind':'gust','mode':mode}))
 log=(out/'console.txt').open('x');p=subprocess.Popen([sys.executable,'-B','pilot/io59/backend.py','mock',rid],cwd=R,stdout=log,stderr=subprocess.STDOUT)
 try:
  deadline=time.monotonic()+4
  while not(out/'backend-ready.json').exists():
   assert p.poll() is None,(out/'console.txt').read_text();assert time.monotonic()<deadline;time.sleep(.02)
  replies=[]
  with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as s:
   s.bind(('127.0.0.1',0));s.settimeout(2)
   # Verify native receive timeout does not terminate the epoch while idle.
   time.sleep(.25)
   for frame in range(2400 if variant=='normal' else 4):
    n=frame if variant!='gap' or frame<3 else 5
    pwm=[1750+(frame*17+i*13)%70 for i in range(4)]+[1000]*12
    s.sendto(struct.pack('<HHI16H',18458,1200,n,*pwm),('127.0.0.1',9002))
    if variant=='gap' and frame==3:break
    replies.append(s.recvfrom(8192)[0])
  if variant=='normal':p.terminate()
  p.wait(timeout=5);result=json.loads((out/'backend-result.json').read_text());rows=list(records(out/'frames.wal'))
  if variant=='gap':
   ck(mode+' gap fails without echo/send of invalid frame',result['error']=='FRAME_GAP_OR_DUPLICATE' and result['frames']==3 and p.returncode==1 and rows[-1]['kind']=='RX');return
  ck(mode+' clean signal closure retains every admitted frame',p.returncode==0 and result['frames']==2400 and rows[-1]['kind']=='CLOSE')
  ck(mode+' no frame dropped in RX/INTENT/SENT',all(sum(r['kind']==k for r in rows)==2400 for k in ['RX','INTENT','SENT']))
  spec=importlib.util.spec_from_file_location('oracle58',R/'evidence/sim32/source-final/pilot/sim32/physics.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);model=mod.Model(mod.profile('offset','gust'));intents=[r for r in rows if r['kind']=='INTENT']
  for frame,(response,rec) in enumerate(zip(replies,intents)):
   body,snap=unpack_intent(rec['body']);row=json.loads(body);pwm=struct.unpack('<HHI16H',bytes.fromhex(row['servoHex']))[3:];expected='\n'+json.dumps(model.step(pwm,1/1200),separators=(',',':'),allow_nan=False)+'\n'
   assert response==expected.encode()==row['sensorUtf8'].encode() and json.dumps(model.snapshot(),separators=(',',':'))==json.dumps(row['modelAux'],separators=(',',':'))
  ck(mode+' original sensor+aux bytes exact for2400 dynamic frames',True)
  return replies
 finally:
  if p.poll() is None:p.terminate();p.wait(timeout=5)
  log.close()
try:
 a=probe('mockbase01','baseline');b=probe('mockopt01','optimized');ck('all baseline/optimized UDP payloads byte-identical',a==b)
 probe('gapopt01','optimized','gap')
 d=E/'mock'/(attempt+'barrier');d.mkdir();events=[]
 def hook(stage,kind,*a):
  events.append([stage,kind])
  if stage=='wal-flush' and kind=='INTENT':raise OSError('INJECTED_FSYNC_FAILURE')
 wal=Wal(d,{},hook=hook);wal.append('RX',0,encode({'rawHex':'00'}));sent=False
 try:wal.append('INTENT',0,b'fixture',flush=True);sent=True
 except OSError:pass
 finally:wal.close()
 ck('fsync failure blocks publication and preserves emergency attempted bytes',not sent and (d/'wal-failure-2.bin').exists())
 ck('reused stdlib encoder preserves Vietnamese/float/null encoding',all(encoder.encode(v)==json.dumps(v,separators=(',',':'),allow_nan=False)for v in [{'a':'Điều khiển','b':None,'c':-0.0},[1.0,1e-12,True]]))
 for value in [float('nan'),float('inf')]:
  try:encoder.encode(value);raise AssertionError('nonfinite accepted')
  except ValueError:pass
 ck('nonfinite values fail before send',True)
 with(E/f'qa-backend-{attempt}.json').open('x')as f:json.dump({'status':'PASS_SCOPED_MOCK','checks':checks,'actualAP':False,'framesOriginalOracle':4800},f,indent=2);f.write('\n')
 print(json.dumps({'status':'PASS','checks':len(checks)}))
except Exception as error:
 with(E/f'qa-backend-failure-{attempt}.json').open('x')as f:json.dump({'status':'FAIL','error':str(error),'checks':checks},f,indent=2)
 raise
