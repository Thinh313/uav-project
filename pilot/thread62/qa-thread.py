from pathlib import Path
import time,os,json,struct,collections,threading
import thread_sampler as t
from instrument import IOTrace
R=Path(__file__).resolve().parents[2];E=R/'evidence/thread62';out=E/'mock/thread01';out.mkdir();checks=[]
def ck(n,v):checks.append({'name':n,'pass':bool(v)});assert v,n
def load(d):
 b=(d/'thread-samples.bin').read_bytes();magic,n,w=struct.unpack('<8sQQ',b[:24]);assert magic==b'AERIST62'and w==15 and len(b)==24+n*w*8
 rows=list(struct.iter_unpack('<15q',b[24:]));return rows
h=t.start(out);trace=IOTrace(20)
idle=[time.monotonic_ns()];time.sleep(.08);idle.append(time.monotonic_ns());busy=[time.monotonic_ns()];end=time.monotonic()+.08
while time.monotonic()<end:sum(i*i for i in range(100))
busy.append(time.monotonic_ns())
trace.call('fsync','INTENT',7,0,0,lambda:time.sleep(.04));t.seal(h,out);rows=load(out);meta=json.loads((out/'thread-samples.json').read_text())
ck('external child targets exact parent main unique thread ID',meta['target']['pid']==os.getpid() and meta['target']['nativeThreadId']==threading.get_native_id() and meta['observerPid']!=os.getpid())
ck('ABI112bytes all queries / states / monotonic CPU',all(r[4]==112 and r[5]==0 and r[8]in range(1,6)for r in rows)and all(b[6]>=a[6]and b[7]>=a[7]for a,b in zip(rows,rows[1:])))
ck('absolute deadline missed ranges retained',all(b[0]==a[0]+(a[3]+1)*t.PERIOD for a,b in zip(rows,rows[1:])))
def span(a,b):return[r for r in rows if a<=r[1]<=r[2]<=b]
i=span(*idle);b=span(*busy);io=trace.data[:12];f=span(io[6],io[7])
ck('idle shows waiting samples and low target CPU',len(i)>4 and any(r[8]==3 for r in i)and(i[-1][6]+i[-1][7]-i[0][6]-i[0][7])<20_000_000)
ck('busy target sampled independently of target GIL',len(b)>4 and any(r[8]==1 for r in b)and(b[-1][6]+b[-1][7]-b[0][6]-b[0][7])>20_000_000)
ck('injected fsync wrapper wait correlated by full query brackets',len(f)>2 and any(r[8]==3 for r in f)and io[7]-io[6]>35_000_000)
ck('observer sealed before target exits',meta['stoppedBySignal']and meta['status']=='PASS_BOUNDED_THREAD_SAMPLES'and h[0].returncode==0)
q=t.Reader(os.getpid(),0).query();ck('wrong thread ID fails query not redirected',q[2]!=112)
d=out/'overflow';d.mkdir();h=t.start(d,1);time.sleep(.04)
try:t.seal(h,d);raise AssertionError('overflow accepted')
except RuntimeError:pass
m=json.loads((d/'thread-samples.json').read_text());ck('capacity overflow fail loud no overwrite / raw retained',m['status']=='FAILED'and m['rows']==1 and m['error']=='THREAD_TRACE_CAPACITY_BEFORE_QUERY'and len(load(d))==1)
trace.seal(out/'syscalls.bin',out/'syscalls-meta.json')
with(E/'qa-thread.json').open('x')as f:json.dump({'status':'PASS_SCOPED_THREAD_MOCK','checks':checks,'phaseSpans':{'idle':idle,'busy':busy,'injectedFsync':[io[6],io[7]]},'samples':len(rows),'states':dict(collections.Counter(r[8]for r in rows)),'scope':'Synthetic CPU / sleep injection validates observation, not real filesystem wait cause.'},f,indent=2)
print(json.dumps({'checks':len(checks),'samples':len(rows)}))
