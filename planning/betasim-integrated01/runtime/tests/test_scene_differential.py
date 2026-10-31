"""Real unchanged model and frame journal, mock clock/send, optional pipe peer.
No AP/Android. Sensor bytes and admitted frame counts must remain identical.
"""
from pathlib import Path
import json,os,shutil,sys,time
HERE=Path(__file__).resolve();ROOT=HERE.parents[1];REPO=ROOT.parents[2];sys.path[:0]=[str(ROOT/'source'),str(REPO)]
from aeris_runtime.scene_channel import ScenePublisher,ScenePipeReader
from aeris_runtime.foundation.frame_adapter import FrameAdapter,SERVO
from pilot.betaintegrated01.runtime.physics import Model,profile
LAB=REPO/'evidence/betasim-integrated01/runtime/.scene'
C={'run':'scene','epoch':'epoch','boot':'boot','profileId':'WORKBENCH_SIM_V1'}
P={k:'a'*64 for k in('backendSourceSHA256','modelSourceSHA256','profileSHA256','journalPolicySHA256')}
class Clock:
 def dispatch(self,bracket,fn):return fn(time.monotonic_ns())
def clock():
 t=time.monotonic_ns();return{'id':1,'hostReceiveNs':t,'offsetLowNs':0,'offsetHighNs':0,'clockPublicationSequence':1,'publicationCompleteHostNs':t}
def run(name,enabled):
 root=LAB/name;root.mkdir();origin=time.monotonic_ns();publisher=reader=None;apAt=[origin]
 if enabled:
  rd,wr=os.pipe();reader=ScenePipeReader(rd,C,root,P);reader.start();publisher=ScenePublisher(wr,C,lambda:{'latest':{'HEARTBEAT':{'armed':True,'observedHostNs':apAt[0]}}},P);publisher.start()
 adapter=FrameAdapter(root/'journal','scene','epoch',Model(profile('offset','gust',32)),max_frames=120,maximum_seconds=180,clock_owner=Clock(),origin_ns=origin,scene=publisher);sensors=[]
 try:
  for frame in range(120):
   apAt[0]=time.monotonic_ns();pwm=[1460+frame%15,1480-frame%13,1440+frame%9,1470-frame%11]+[1000]*12;adapter.receive(SERVO.pack(18458,1200,frame,*pwm),('127.0.0.1',9000),lambda b:(sensors.append(b)or len(b)),clock_read=clock)
  assert adapter.frames==adapter.stage_rows==120
  if publisher:
   end=time.monotonic()+1
   while reader.received==0 and reader.failure is None and time.monotonic()<end:time.sleep(.005)
   assert reader.received>0 and reader.failure is None,(reader.received,reader.failure,publisher.failure);snapshot=reader.snapshot();assert snapshot['available']and snapshot['frame']['poseSource']=='ROOT_DURABLE_FDM_STATE'and snapshot['frame']['sourceBinding']==P
  return sensors,adapter.model.snapshot(),{'frames':adapter.frames,'stageRows':adapter.stage_rows,'visual':reader.received if reader else 0}
 finally:
  # Mock differential only: preserve real journal close without flight claim.
  adapter.journal.abort('MOCK_DIFFERENTIAL_TEST_TERMINAL_NOT_FLIGHT')
  if publisher:publisher.close();time.sleep(.01);reader.close()
def main():
 assert not LAB.exists();LAB.mkdir(parents=True)
 try:
  a,ma,ra=run('off',False);b,mb,rb=run('on',True);assert a==b and ma==mb;out={'status':'PASS_MODEL_SENSOR_DIFFERENTIAL_MOCK_NOT_SITL','framesPerVariant':120,'sameSensorBytes':True,'sameModelState':True,'sameFrameStageCounts':ra['frames']==rb['frames']==ra['stageRows']==rb['stageRows'],'committedSceneViews':rb['visual'],'sourcePins':P,'pinsAreMockFixture':True,'actualAndroidAP':False,'scratchRemoved':str(LAB)}
 finally:shutil.rmtree(LAB)
 (REPO/'evidence/betasim-integrated01/runtime/scene-differential-mock.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'status':out['status'],'frames':120,'visualViews':rb['visual']}))
if __name__=='__main__':main()
