from android_qa import *
from b_rpc import call,state
import sys,signal
owned();run=sys.argv[1];tag=sys.argv[2];s=state();assert s['pid']==json.loads((E/('companion'+tag)/'launch.json').read_text())['pid'];assert s['connected']and s['state']['phase']=='OPEN'and s['state']['self']['joined'];time.sleep(1.1)
# New explicit capture, separate from prior consent UI capture; max1/s and one attempt.
s=call('action',{'operation':'capture','resource':'camera:front','a':0,'b':0,'to':''});v=s['state'];p=next(p for p in v['payloads']if p['id']=='front');assert p['cameraOwnerSid']==v['self']['session'];assert p['leaseUntilMs']-v['snapshotAtMs']>5000
q={'atHostMonoNs':str(time.monotonic_ns()),'run':run,'pid':s['pid'],'B':s,'fault':'OWNED_B_SIGSTOP_NO_TCP_FIN','receipt':'Explicit new capture then process stop, no repeated RPC or proxy heartbeat'};os.kill(s['pid'],signal.SIGSTOP);q['signalSentAtHostMonoNs']=str(time.monotonic_ns());(E/'b-partition-cut03.json').open('x').write(json.dumps(q,indent=2));time.sleep(3.6);capture(run+'-b-partition-a-remains-foreground');print('B_SIGSTOP_CUT_RECORDED_NO_RETRY',flush=True)
