from pathlib import Path
import json,struct,sys,hashlib
R=Path(__file__).resolve().parents[2];out=R/'evidence/alloc60/runs'/sys.argv[1]
a=json.loads((out/'allocation.json').read_text());req=json.loads((out/'request.json').read_text());v=json.loads((out/'io-verification.json').read_text());meta=json.loads((out/'syscalls-meta.json').read_text());extent=[];magic=[]
with(out/'syscalls.bin').open('rb')as f:
 _,n,w=struct.unpack('<8sQQ',f.read(24));assert w==12
 for i in range(n):
  row=struct.unpack('<12q',f.read(96))
  if row[1]==meta['operations']['preallocate']:extent.append(row)
  if row[1]==meta['operations']['write'] and row[2]==meta['kinds']['MAGIC']:magic.append(row)
assert len(magic)==1 and v['walBytesEveryByteWrittenObserved']==(out/'frames.wal').stat().st_size
if req['allocation']=='preallocate':
 assert a['status']=='EXTENT_RESERVED' and a['requestedBytes']==384*2**20 and a['returnedAllocatedBytes']>=a['requestedBytes']
 assert a['logicalSizeBefore']==a['logicalSizeAfter']==a['positionBefore']==a['positionAfter']==0
 assert not a['fallback'] and a['flags']==4 and a['posmode']==3
 assert len(extent)==1 and extent[0][7]<=magic[0][6] and extent[0][5]==a['requestedBytes'] and extent[0][10]==a['returnedAllocatedBytes'] and extent[0][-1]==0
else:assert a['status']=='DISABLED' and not extent
with(out/'extent-verification.json').open('x')as f:json.dump({'status':'PASS_NATIVE_EXTENT_LOGICAL_EOF_AND_ORDER','allocation':req['allocation'],'physicalBytesAfterClose':(out/'frames.wal').stat().st_blocks*512,'logicalBytesAfterClose':(out/'frames.wal').stat().st_size,'frames':v['frames'],'checks':4,'scope':'Extent/byte/order proof; not pacing or power-loss acceptance'},f,indent=2)
print(req['allocation'],'extent/order/logical EOF PASS')
