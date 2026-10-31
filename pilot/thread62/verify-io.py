"""Independent replay of syscall conservation and pre-send durability ordering."""
from pathlib import Path
import sys,json,struct,collections,hashlib
from importlib.util import spec_from_file_location,module_from_spec
R=Path(__file__).resolve().parents[2];E=R/'evidence/thread62';rid=sys.argv[1];out=E/'runs'/rid
spec=spec_from_file_location('walreader',R/'pilot/pace58/readback.py');m=module_from_spec(spec);spec.loader.exec_module(m)
with(out/'syscalls.bin').open('rb')as f:
 magic,n,width=struct.unpack('<8sQQ',f.read(24));assert(magic,width)==(b'AERISIO9',12);rows=[struct.unpack('<12q',f.read(96))for _ in range(n)];assert not f.read(1)
meta=json.loads((out/'syscalls-meta.json').read_text());assert meta['rows']==n and not meta['overflow'];ops=meta['operations'];kinds=meta['kinds'];by=collections.defaultdict(list);position=0;lastEnd=0;counts=collections.Counter()
for i,row in enumerate(rows):
 seq,op,kind,frame,offset,requested,a,b,c,d,returned,err=row;assert seq==i and a>=lastEnd and b>=a and d>=c and err==0;lastEnd=b;counts[(op,kind)]+=1;by[frame].append(row)
 if op==ops['write'] and kind!=kinds['SNAPSHOT']:
  assert offset==position and returned==requested>0;position+=returned
assert position==(out/'frames.wal').stat().st_size
stages=json.loads((out/'backend-stages.json').read_text());result=json.loads((out/'backend-result.json').read_text());assert len(stages)==result['frames']
for frame,rx,a,computed,barrier,sent in stages:
 rs=by[frame]
 for kind in ['RX','INTENT','SENT']:
  v=[v for v in rs if v[1]==ops['write'] and v[2]==kinds[kind]];assert len(v)==1
  if kind=='RX':assert rx<=v[0][6]<=v[0][7]<=a
  elif kind=='INTENT':assert computed<=v[0][6]<=v[0][7]<=barrier
  else:assert v[0][6]>=sent
 flush=[v for v in rs if v[1]==ops['fsync'] and v[2]==kinds['INTENT']];assert len(flush)==1 and computed<=flush[0][6]<=flush[0][7]<=barrier<=sent
records=collections.Counter(r['kind']for r in m.records(out/'frames.wal'))
assert all(records[k]==len(stages)for k in ['RX','INTENT','SENT'])
assert counts[(ops['fsync'],kinds['INTENT'])]==len(stages)
assert counts[(ops['fsync'],kinds['HEADER'])]==counts[(ops['fsync'],kinds['CLOSE'])]==1
report={'status':'PASS_RAW_SYSCALL_CONSERVATION_AND_BARRIER_ORDER','frames':len(stages),'syscallRows':n,'walBytesEveryByteWrittenObserved':position,'fsyncBeforeEverySensorSend':True,'noFrameOrSyscallDropped':True,'scope':'Integrity/order only; no pacing/flight completion/Hera acceptance','checks':6}
with(out/'io-verification.json').open('x')as f:json.dump(report,f,indent=2)
print(json.dumps(report))
