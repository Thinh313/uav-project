"""Real 15s DiskGuard priming plus post-SENT stage-I/O failure. No AP/socket."""
from pathlib import Path
import datetime,hashlib,json,sys,time
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R))
from pilot.betaintegrated01.runtime02.frame_adapter import FrameAdapter,SERVO
from pilot.betaintegrated01.runtime02.journal import FileIO,verify_journal
from pilot.betaintegrated01.runtime.physics import Model,profile
out=R/('evidence/betaintegrated01-m1runtime/qa/runtime02-stage-fault'+sys.argv[1]);out.mkdir()
sources=[R/'pilot/betaintegrated01/runtime02'/s for s in ['frame_adapter.py','journal/writer.py','journal/admission.py','journal/receiver.py']]
pins=lambda:{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sources};before=pins()
class StageFault(FileIO):
 def write(self,fd,data):
  if b'"eventKind":"STAGE"'in bytes(data):raise OSError('QA_STAGE_POST_SENT_EIO')
  return super().write(fd,data)
start=time.monotonic_ns();adapter=FrameAdapter(out/'journal','qa-stage','epoch01',Model(profile()),max_frames=16,io=StageFault());primed=time.monotonic_ns();sent=[];error=None
fresh=lambda:{'id':1,'hostReceiveNs':time.monotonic_ns(),'offsetLowNs':0,'offsetHighNs':1}
try:adapter.receive(SERVO.pack(18458,1200,0,*([1000]*16)),('127.0.0.1',45100),lambda body:(sent.append(body)or len(body)),clock_read=fresh)
except OSError as e:error=str(e)
reject=json.loads((out/'journal-rejected.json').read_text());cold=verify_journal(out/'journal','qa-stage','epoch01');manifest=json.loads((out/'journal/manifest.json').read_text());receipt=adapter.journal.guard.prime_receipt
checks={'oneSensorLocalSend':len(sent)==1,'exceptionRetained':error is not None,'completedFramesTruth':adapter.frames==adapter.journal.frames==1,'missingStageExplicit':adapter.stage_rows==0 and reject['completedStageRows']==0,'alreadyAdmittedNotFalse':reject['alreadyAdmitted']is True and reject['rejectionIsNotAdmittedFrame']is False,'SENTAcknowledged':reject['frameAttempt']['SENTGroupAcknowledged']is True and reject['frameAttempt']['localReturnKnown']is True,'attemptedStageRetained':type(reject['frameAttempt']['attemptedStage'])is dict,'incompleteNeverComplete':cold['state']=='INCOMPLETE_RECORDING'and cold['frames']==1 and cold['stageRows']==0,'actualPrime15s':primed-start>=15000000000 and receipt['elapsedRealMonotonicNs']>=15000000000 and receipt['primed']is True,'manifestV2':manifest['version']==2 and manifest['diskGuardPolicy']['horizonNs']==15000000000 and manifest['diskGuardPolicy']['floorBytes']==10*2**30,'policyStill2010':manifest['diskGuardPolicy']['entryBytes']==20*2**30 and manifest['diskGuardPolicy']['reserveBytes']==256*2**20,'sourceStable':before==pins()}
report={'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceBefore':before,'sourceAfter':pins(),'checks':checks,'status':'PASS'if all(checks.values())else'FAIL','primeWallMonotonicNs':primed-start,'guardPrimeReceipt':receipt,'cold':cold,'diagnostic':reject,'APAndroidSocketRuntimeLaunches':0,'realDiskGuardPriming':True,'guardMonkeypatchOrFakeFreeSpace':False,'faultSeam':'FileIO.write raises only STAGE record after real SENT group callback acknowledgment','scope':'Actualhost statvfs/monotonic15s prime +one synthetic servo frame; no AP/drone/Android or flight execution proof'}
(out/'results.json').open('x').write(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'checks':len(checks),'failed':[k for k,v in checks.items()if not v],'primeSeconds':(primed-start)/1e9,'frames':adapter.frames,'stages':adapter.stage_rows}))
