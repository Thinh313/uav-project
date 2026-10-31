"""Bracket-contained per-thread state samples; never integrate states as wait time."""
from pathlib import Path
import sys,json,struct,collections,bisect,hashlib
from analyze import stats
R=Path(__file__).resolve().parents[2];E=R/'evidence/thread62'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def load(out):
 meta=json.loads((out/'thread-samples.json').read_text());assert meta['status']=='PASS_BOUNDED_THREAD_SAMPLES'and meta['error']is None and meta['stoppedBySignal']
 b=(out/'thread-samples.bin').read_bytes();magic,n,w=struct.unpack('<8sQQ',b[:24]);assert magic==b'AERIST62'and w==15 and n==meta['rows']and 0<n<=meta['capacity']and len(b)==24+n*w*8
 rows=list(struct.iter_unpack('<15q',b[24:]));assert all(r[0]<=r[1]<=r[2]and r[4]==112 and r[5]==0 and 1<=r[8]<=5 and r[3]==max(0,(r[1]-r[0])//meta['periodNs'])for r in rows)
 for a,b in zip(rows,rows[1:]):
  assert b[0]==a[0]+(a[3]+1)*meta['periodNs']and b[1]>=a[2]and b[6]>=a[6]and b[7]>=a[7]and b[14]>=a[14],'THREAD_COUNTER_OR_DEADLINE_REGRESSION'
 ready=json.loads((out/'thread-observer-ready.json').read_text());target=json.loads((out/'thread-target.json').read_text());backend=json.loads((out/'backend-ready.json').read_text());assert target==meta['target']==ready['target']and target['pid']==backend['pid']==ready['parentPid']and meta['observerPid']==ready['pid']and target['role']=='BACKEND_MAIN_THREAD'
 return meta,rows

def run(rid):
 out=E/'runs'/rid;meta,rows=load(out);starts=[r[1]for r in rows];ends=[r[2]for r in rows]
 def window(a,b):
  lo=bisect.bisect_left(starts,a);hi=bisect.bisect_right(starts,b);contained=[r for r in rows[lo:hi]if r[2]<=b]
  left=max(0,bisect.bisect_right(ends,a)-1);right=min(len(rows)-1,bisect.bisect_left(starts,b));x,y=rows[left],rows[right]
  return {'completeQuerySamples':len(contained),'sampledStates':dict(collections.Counter(str(r[8])for r in contained)),'coveringQueryWindowNs':[x[1],y[2]],'coversSpan':x[1]<=a<=b<=y[2],'sampledCpuDeltaNs':{'user':y[6]-x[6],'system':y[7]-x[7]},'cpuDeltaScope':'Covering query window includes outside span; not exact syscall/frame CPU, no runnable-wait duration.'}
 worst=json.loads((out/'io-analysis.json').read_text())['worstFrames'];details=[]
 with(out/'syscalls.bin').open('rb')as f:
  magic,n,w=struct.unpack('<8sQQ',f.read(24));assert magic==b'AERISIO9'and w==12
  io=list(struct.iter_unpack('<12q',f.read()));assert len(io)==n
 for frame in worst[:20]:
  ops=[r for r in io if r[3]==frame['frame']and r[1]in[1,2]]
  details.append({'frame':frame['frame'],'receiveNs':frame['receiveNs'],'sendNs':frame['sendNs'],'backendWallMs':frame['wallMs'],'backendThreadCpuMs':frame['threadCpuMs'],'threadSamples':window(frame['receiveNs'],frame['sendNs']),'filesystemCalls':[{'sequence':r[0],'operation':r[1],'kind':r[2],'wallMs':(r[7]-r[6])/1e6,'threadCpuMs':(r[9]-r[8])/1e6,**window(r[6],r[7])}for r in ops]})
 calls=[]
 for op,label in [(1,'write'),(2,'fsync')]:
  selected=[r for r in io if r[1]==op];slow=sorted(selected,key=lambda r:r[7]-r[6],reverse=True)[:15]
  calls.append({'operation':label,'count':len(selected),'wallMs':stats([(r[7]-r[6])/1e6 for r in selected]),'threadCpuMs':stats([(r[9]-r[8])/1e6 for r in selected]),'slowest':[{'sequence':r[0],'frame':r[3],'kind':r[2],'startNs':r[6],'endNs':r[7],'wallMs':(r[7]-r[6])/1e6,'threadCpuMs':(r[9]-r[8])/1e6,**window(r[6],r[7])}for r in slow]})
 report={'status':'PASS_SCOPED_PER_THREAD_CORRELATION_NOT_CAUSAL_PROOF','run':rid,'identity':meta['target'],'observerPid':meta['observerPid'],'samples':len(rows),'periodNs':meta['periodNs'],'missedDeadlines':sum(r[3]for r in rows),'queryLatencyMs':stats([(r[2]-r[1])/1e6 for r in rows]),'wakeLatenessMs':stats([(r[1]-r[0])/1e6 for r in rows]),'states':dict(collections.Counter(str(r[8])for r in rows)),'stateLabels':meta['states'],'sampledTargetCpuNs':{'user':rows[-1][6]-rows[0][6],'system':rows[-1][7]-rows[0][7]},'observerCpuNs':meta['observerCpuNs'],'filesystem':calls,'worstFrames':details,'scope':'Samples are sparse state observations with explicit query brackets, not integrated duration or filesystem wait reason. RUNNING can be runnable. Direct syscall CPU/wall differ from sampled counter windows. No timing cost subtraction, no precise host runqueue wait or one-way guest latency claim.','filesSha256':{p.name:sha(p)for p in [out/'thread-target.json',out/'thread-observer-ready.json',out/'thread-samples.bin',out/'thread-samples.json',out/'syscalls.bin',out/'backend-stages.json',out/'backend-cpu-stages.json']}}
 with(out/'thread-analysis.json').open('x')as f:json.dump(report,f,indent=2)
 print(json.dumps({'run':rid,'samples':len(rows),'states':report['states'],'queryMs':report['queryLatencyMs'],'worst':details[0]},indent=2))
if __name__=='__main__':run(sys.argv[1])
