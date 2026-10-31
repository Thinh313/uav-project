"""Synthetic full-capture cold oracle probes; no AP or network execution."""
from pathlib import Path
import datetime,hashlib,json,shutil,struct,sys,time
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R))
from pilot.betaintegrated01.runtime.frame_adapter import FrameAdapter,SERVO
from pilot.betaintegrated01.runtime.ap_stage import StageDrainer,EVENT
from pilot.betaintegrated01.runtime.physics import Model,profile
from pilot.betaintegrated01.runtime.verify_capture import verify_capture
from pilot.betaintegrated01.clock.correlation import BoundedCorrelator,Context
out=R/('evidence/betaintegrated01-m1runtime/qa/composed-capture'+sys.argv[1]);out.mkdir()
source=R/'pilot/betaintegrated01/runtime/verify_capture.py';before=hashlib.sha256(source.read_bytes()).hexdigest();results=[]

def make(name,badclock=False):
 p=out/name;p.mkdir();a=FrameAdapter(p/'journal','run01','epoch01',Model(profile()),max_frames=32)
 ctx=Context('run01','epoch01','boot01');c=BoundedCorrelator(ctx,('127.0.0.1',9014),lambda row:a.event('CLOCK',row))
 if badclock:
  a.event('CLOCK',{'kind':'RESPONSE','id':1,'status':'MATCHED','freshCalibration':True,'rawHex':'00','hostReceiveNs':time.monotonic_ns()})
  fresh=lambda:{'id':1,'hostReceiveNs':time.monotonic_ns(),'offsetLowNs':0,'offsetHighNs':1}
 else:
  sent=time.monotonic_ns();c.register(1,sent,ctx);c.receive(struct.pack('<7Q',1,sent-1000000,sent-999990,0,0,0,0),('127.0.0.1',9014),time.monotonic_ns(),ctx)
  fresh=lambda:c.calibration(time.monotonic_ns(),ctx)
 for frame in range(2):a.receive(SERVO.pack(18458,1200,frame,*([1000]*16)),('127.0.0.1',45100),lambda b:len(b),clock_read=fresh)
 host=a.close();d=StageDrainer(p/'ap-stage','run01','epoch01','boot01',events_per_chunk=7,max_events=100)
 seq=0
 for frame in range(2):
  for kind in [10,11,12,13,14,20,21,24]:d.feed(EVENT.pack(seq,frame,kind,4321,seq+1,seq+1,0,0,0));seq+=1
 for kind in [10,11,12]:d.feed(EVENT.pack(seq,2,kind,4321,seq+1,seq+1,0,0,0));seq+=1
 stage=d.finish(ap_exit=-15,eof=True)
 pending={'rawHex':SERVO.pack(18458,1200,2,*([1000]*16)).hex(),'peer':['127.0.0.1',45100],'reason':'UNADMITTED_AT_OWNED_STOP','admittedFrames':2,'run':'run01','epoch':'epoch01','boot':'boot01','modelStepComputed':False,'sensorSent':False}
 (p/'pending-servo.json').write_text(json.dumps(pending))
 return p,host['commitAnchor'],stage['terminalSHA256']

normal,h,s=make('normal')
def check(name,path,want):
 try:
  v=verify_capture(path,'run01','epoch01','boot01',expected_host_anchor=h,expected_stage_anchor=s)
  results.append({'id':name,'pass':want,'unexpectedAcceptance'if not want else'verdict':v})
 except Exception as e:results.append({'id':name,'pass':not want,'rejection':type(e).__name__+':'+str(e)})
check('BASELINE_SYNTHETIC_TWO_FRAMES',normal,True)
mutations=[('FOREIGN_PENDING_RUN','run','foreign'),('FOREIGN_PENDING_EPOCH','epoch','foreign'),('FOREIGN_PENDING_BOOT','boot','foreign'),('PENDING_MODEL_COMPUTED','modelStepComputed',True),('PENDING_WRONG_REASON','reason','FOREIGN_REASON')]
for name,key,value in mutations:
 p=out/name;shutil.copytree(normal,p);pending=json.loads((p/'pending-servo.json').read_text());pending[key]=value;(p/'pending-servo.json').write_text(json.dumps(pending));check(name,p,False)
for name,magic,rate in [('PENDING_WRONG_MAGIC',18459,1200),('PENDING_WRONG_RATE',18458,1199)]:
 p=out/name;shutil.copytree(normal,p);pending=json.loads((p/'pending-servo.json').read_text());pending['rawHex']=SERVO.pack(magic,rate,2,*([1000]*16)).hex();(p/'pending-servo.json').write_text(json.dumps(pending));check(name,p,False)
p,bh,bs=make('unregistered-malformed-clock',True)
try:
 v=verify_capture(p,'run01','epoch01','boot01',expected_host_anchor=bh,expected_stage_anchor=bs);results.append({'id':'MALFORMED_UNREGISTERED_CLOCK_NOT_QUALIFIED','pass':False,'unexpectedAcceptance':v})
except Exception as e:results.append({'id':'MALFORMED_UNREGISTERED_CLOCK_NOT_QUALIFIED','pass':True,'rejection':type(e).__name__+':'+str(e)})
after=hashlib.sha256(source.read_bytes()).hexdigest();data={'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceBefore':before,'sourceAfter':after,'sourceChanged':before!=after,'results':results,'status':'PASS'if all(r['pass']for r in results)and before==after else'FAIL','APAndroidSocketRuntimeLaunches':0,'scope':'Synthetic writer-generated fixtures test independent cold semantics, not actual AP/flight proof'}
(out/'results.json').open('x').write(json.dumps(data,indent=2)+'\n');print(json.dumps({'status':data['status'],'groups':len(results),'failed':[r['id']for r in results if not r['pass']],'sourceChanged':before!=after}))
