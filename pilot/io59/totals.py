from pathlib import Path
import sys,json,struct,collections
R=Path(__file__).resolve().parents[2];out=R/'evidence/io59/runs'/sys.argv[1]
stages=json.loads((out/'backend-stages.json').read_text());cpu=json.loads((out/'backend-cpu-stages.json').read_text());meta=json.loads((out/'syscalls-meta.json').read_text());g=collections.defaultdict(lambda:collections.Counter());by=collections.defaultdict(list)
with(out/'syscalls.bin').open('rb')as f:
 _,n,w=struct.unpack('<8sQQ',f.read(24));assert w==12
 for _ in range(n):
  r=struct.unpack('<12q',f.read(96));by[r[3]].append(r)
for s,c in zip(stages,cpu):
 for name,i,j,ci,cj in [('rxToCompute',1,2,1,2),('compute',2,3,2,3),('durableIntent',3,4,3,4),('barrierToSend',4,5,4,5)]:
  calls=[v for v in by[s[0]]if v[6]>=s[i]and v[7]<=s[j]];a=g[name];a['frames']+=1;a['wallNs']+=s[j]-s[i];a['threadCpuNs']+=c[cj]-c[ci];a['syscallWallNs']+=sum(v[7]-v[6]for v in calls);a['syscallCpuNs']+=sum(v[9]-v[8]for v in calls)
for v in g.values():v['outsideSyscallsNonCpuProxyNs']=v['wallNs']-v['syscallWallNs']-v['threadCpuNs']+v['syscallCpuNs']
with(out/'phase-totals.json').open('x')as f:json.dump({'phases':g,'scope':'All admitted frames, raw signed clock noise retained; sums not exclusive scheduler/I/O attribution'},f,indent=2)
print(json.dumps(g))
