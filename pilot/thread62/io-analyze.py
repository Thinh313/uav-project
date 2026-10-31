"""Read-only raw syscall/wake and frame attribution; never equates offCPU to scheduler wait."""
from pathlib import Path
import sys,json,struct,collections,hashlib,heapq
from analyze import stats
R=Path(__file__).resolve().parents[2];E=R/'evidence/thread62'
def raw(path,magic,width):
 with path.open('rb')as f:
  m,n,w=struct.unpack('<8sQQ',f.read(24));assert(m,w)==(magic,width)
  for i in range(n):
   b=f.read(width*8);assert len(b)==width*8;yield struct.unpack('<'+'q'*width,b)
  assert not f.read(1)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main(rid):
 out=E/'runs'/rid;meta=json.loads((out/'syscalls-meta.json').read_text());assert not meta['overflow']
 ops={v:k for k,v in meta['operations'].items()};kinds={v:k for k,v in meta['kinds'].items()};groups=collections.defaultdict(lambda:{'wall':[],'cpu':[],'offCPU':[]});by=collections.defaultdict(list);slow=[];total=0;errors=[]
 for row in raw(out/'syscalls.bin',b'AERISIO9',12):
  seq,op,kind,frame,offset,requested,a,b,c,d,returned,err=row;assert seq==total and b>=a and d>=c;total+=1
  wall=(b-a)/1e6;cpu=(d-c)/1e6;g=groups[ops[op]+':'+kinds[kind]];g['wall'].append(wall);g['cpu'].append(cpu);g['offCPU'].append(wall-cpu)
  by[frame].append(row)
  if wall>5:slow.append({'frame':frame,'operation':ops[op],'kind':kinds[kind],'startNs':a,'endNs':b,'wallMs':wall,'threadCpuMs':cpu,'nonCpuProxyMs':wall-cpu,'offset':offset,'requestedBytes':requested,'returned':returned,'errno':err})
  if err:errors.append({'seq':seq,'errno':err})
 assert total==meta['rows']
 wake={};wake_rows={}
 for label in ['thread','process']:
  rows=list(raw(out/f'wake-{label}.bin',b'AERISWK9',6));m=json.loads((out/f'wake-{label}.json').read_text());assert not m['error'] and len(rows)==m['count']
  for a,b in zip(rows,rows[1:]):assert b[0]==a[0]+(a[3]+1)*m['periodNs']
  wake[label]={'actualWakes':len(rows),'missedDeadlines':sum(v[3]for v in rows),'latenessMs':stats([(v[1]-v[0])/1e6 for v in rows]),'allOver5ms':[{'scheduledNs':v[0],'actualNs':v[1],'lateMs':(v[1]-v[0])/1e6,'missed':v[3]}for v in rows if v[1]-v[0]>5000000]};wake_rows[label]=rows
 stages=json.loads((out/'backend-stages.json').read_text());cpus=json.loads((out/'backend-cpu-stages.json').read_text());assert len(stages)==len(cpus)
 frames=[]
 for s,c in zip(stages,cpus):
  frame,rx,a,computed,barrier,sent=s;assert c[0]==frame
  parts=[]
  for name,start,end,cs,ce in [('rxToCompute',rx,a,c[1],c[2]),('compute',a,computed,c[2],c[3]),('durableIntent',computed,barrier,c[3],c[4]),('barrierToSend',barrier,sent,c[4],c[5])]:
   calls=[v for v in by[frame]if v[6]>=start and v[7]<=end];sw=sum(v[7]-v[6]for v in calls);sc=sum(v[9]-v[8]for v in calls)
   parts.append({'phase':name,'wallMs':(end-start)/1e6,'threadCpuMs':(ce-cs)/1e6,'syscallWallMs':sw/1e6,'syscallCpuMs':sc/1e6,'outsideMeasuredSyscallWallMs':(end-start-sw)/1e6,'outsideMeasuredSyscallNonCpuProxyMs':(end-start-sw-(ce-cs-sc))/1e6,'calls':[{'operation':ops[v[1]],'kind':kinds[v[2]],'wallMs':(v[7]-v[6])/1e6,'cpuMs':(v[9]-v[8])/1e6}for v in calls]})
  frames.append({'frame':frame,'receiveNs':rx,'sendNs':sent,'wallMs':(sent-rx)/1e6,'threadCpuMs':(c[5]-c[1])/1e6,'parts':parts})
 worst=sorted(frames,key=lambda x:x['wallMs'],reverse=True)[:30]
 for f in worst:
  f['wakeWindows']={k:[{'scheduledNs':v[0],'actualNs':v[1],'lateMs':(v[1]-v[0])/1e6}for v in rows if v[0]<=f['sendNs'] and v[1]>=f['receiveNs']]for k,rows in wake_rows.items()}
 result={'status':'MEASURED_NOT_CAUSAL_SCHEDULER_PROOF','run':rid,'syscallRows':total,'errors':errors,'frames':len(frames),'groups':{k:{metric+'Ms':stats(vals)for metric,vals in v.items()}for k,v in groups.items()},'slowCallsOver5ms':sorted(slow,key=lambda v:v['wallMs'],reverse=True),'wake':wake,'worstFrames':worst,'hostReceiveToSendMs':stats([f['wallMs']for f in frames]),'exclusiveKernelRunnableWait':'UNKNOWN_NO_KERNEL_SCHEDULER_TRACE','interpretation':'syscall wall includes possible preemption and wrapper clock overhead. OffCPU also includes I/O blocking and GIL; wake lateness is contention proxy. No timing subtraction from frames or invented causal root.', 'filesSha256':{p.name:sha(p)for p in [out/'syscalls.bin',out/'syscalls-meta.json',out/'wake-thread.bin',out/'wake-process.bin',out/'backend-stages.json',out/'backend-cpu-stages.json']}}
 with(out/'io-analysis.json').open('x')as f:json.dump(result,f,indent=2)
 print(json.dumps({'run':rid,'rows':total,'frames':len(frames),'worst':worst[0],'groupMaxMs':{k:v['wallMs']['max']for k,v in result['groups'].items()},'wake':{k:{'maxLateMs':v['latenessMs']['max'],'missed':v['missedDeadlines']}for k,v in wake.items()}},indent=2))
if __name__=='__main__':main(sys.argv[1])
