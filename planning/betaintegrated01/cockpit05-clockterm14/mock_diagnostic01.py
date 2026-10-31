"""Source-bound diagnostic enum seam; synthetic numbers, no device/IO timing claim."""
from pathlib import Path
from importlib import import_module
import json,hashlib,copy
R=Path(__file__).resolve().parents[3]
D=import_module('planning.betaintegrated01.cockpit05-clockterm14.flight.diagnostic')
def main():
 context={'run':'synthetic-diagnostic','epoch':'unit'};source='a'*64
 phases=sorted(D.PHASES)
 queue=dict(kind='SAMPLER_UI_LIVENESS',threadId=2,serial=1,producerElapsedNs=100,offerElapsedNs=101,consumeElapsedNs=102,depth=0,queueDwellThreadCPU=None,queueDwellMeaning='ELAPSED_WALL_ONLY_NO_CROSS_THREAD_CPU_SUBTRACTION')
 value=dict(format='aeris-native-io-diagnostics',version=1,context=context,APKSourceSHA256=source,cpuUnavailableOperations=0,measurementErrors=0,threadCpuClock='android.os.Debug.threadCpuTimeNanos_CURRENT_THREAD',wallClockDomain='ANDROID_ELAPSED_REALTIME_NS_CALLER_CLOCK',diagnosticNotAuthorityOrFlightProof=True,nonCPUWallCause='UNKNOWN_NOT_EXCLUSIVE_FILESYSTEM_OR_SCHEDULER',terminalStateSHA256='b'*64,ringCapacity=256,maximumMessagesPerOuterLoop=16)
 value['recentSpans']=[dict(phase=p,beginElapsedNs=1,endElapsedNs=2,wallNs=1,threadCpuNs=1,threadId=2)for p in phases]
 value['phaseSummary']=[dict(phase=p,count=1,wallTotalNs=1,wallMaxNs=1,cpuKnownCount=1,cpuTotalKnownNs=1,cpuMaxKnownNs=1,wallHistogram=[1,0,0,0,0,0,0,0])for p in phases]
 value.update(spanCount=len(phases),recentQueueEvents=[queue],queueEventCount=1)
 cases=[]
 for kind,expected in [('OFFER_RELEASE_NOTICE',True),('CONSUME_RELEASE_NOTICE',True),('OFFER_RELEASE',False),('CONSUME_UNKNOWN',False)]:
  v=copy.deepcopy(value);q=dict(queue,kind=kind,serial=-1)
  if kind.startswith('OFFER_'):q['consumeElapsedNs']=-1
  v['recentQueueEvents'].append(q);v['queueEventCount']=2
  error=None
  try:D.validate(json.dumps(v).encode(),context,source);accepted=True
  except ValueError as e:accepted=False;error=str(e)
  cases.append(dict(kind=kind,expected=expected,accepted=accepted,error=error));assert accepted is expected
 owner=R/'native/betaintegrated01/ioadmit13-core/src/vn/rtr/aeris/control01/ControlOwner.java'
 assert 'offer("RELEASE_NOTICE"'in owner.read_text()
 result=dict(status='PASS',cases=cases,provenance='SYNTHETIC_DIAGNOSTIC_SCHEMA_ONLY_NOT_ANDROID_MEASUREMENTS',sourceSHA256={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in(owner,Path(D.__file__))},deviceCommands=False,runtimeExecuted=False)
 out=R/'evidence/betaintegrated01-cockpit05-clockterm14/host/diagnostic-enum01.json'
 out.open('x').write(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':'PASS','cases':len(cases)}))
if __name__=='__main__':main()
