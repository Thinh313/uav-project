from pathlib import Path
import sys,json,struct,gc
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'pilot/sim32-journal04'))
from compact import Rows,CompactWal
from gc_observer import GCObserver
from wal_journal import encode,read_wal
e=R/'evidence/pace58/qa-compact';e.mkdir()
r=Rows(10000,6)
for i in range(10000):r.append([i,i+1,i+2,i+3,i+4,i+5])
assert len(r)==10000 and all(row==[i,i+1,i+2,i+3,i+4,i+5]for i,row in enumerate(r))
try:r.append([0]*6);raise AssertionError('overflow hidden')
except RuntimeError as exc:assert str(exc)=='TRACE_CAPACITY_NO_DROP'
w=CompactWal(e,{},limit=1048576)
for i in range(100):
 w.append('RX',i,encode({'frame':i}));w.append('INTENT',i,struct.pack('<II',2,0)+b'{}',flush=True);w.append('SENT',i,b'{}')
w.append('CLOSE',0,b'{}',flush=True);w.close();v=read_wal(e/'frames.wal');assert v['error'] is None and len(v['records'])==302 and w.flushes==102 and len(w.append_cost)==302
g=GCObserver();gc.collect();s=g.seal();assert s['events']and not s['overflow'] and all(x['wallNs']>=0 and x['cpuNs']>=0 for x in s['events'])
result={'status':'PASS_SCOPED_MOCK','checks':4,'contiguousRowsExact':10000,'walCRCChainRecords':302,'fsyncCalls':102,'bufferBytes':len(r.data)*r.data.itemsize,'forcedGCOnlyInTest':True,'runtimeGCPolicyUnchanged':True}
with(e/'receipt.json').open('x')as f:json.dump(result,f,indent=2)
print(json.dumps(result))
