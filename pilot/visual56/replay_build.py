import hashlib,json,struct,zlib
from pathlib import Path
R=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent
header=struct.Struct('<BBHIIQQ');out=[]
for run,label in [('rc0364e5644f5461ebff1','Tải giữa · lặng gió'),('r8dc8fec8bc65440c8f38','Tải lệch · gió giật')]:
 p=R/'evidence/simtrain53/runs'/run/'frames.wal';chain=bytes(32);file_hash=hashlib.sha256();rows=[];sequence=0;intents=0
 with p.open('rb') as f:
  magic=f.read(8);assert magic==b'AERISJ04';file_hash.update(magic)
  while b:=f.read(header.size):
   assert len(b)==header.size
   kind,flags,reserved,frame,n,seq,ns=header.unpack(b);assert n<=16384 and seq==sequence
   body=f.read(n);crc=f.read(4);tail=f.read(32);file_hash.update(b+body+crc+tail)
   assert len(body)==n and zlib.crc32(b+body)==struct.unpack('<I',crc)[0]
   assert hashlib.sha256(chain+b+body).digest()==tail;chain=tail;sequence+=1
   if kind==3:
    intents+=1
    if frame%40:continue
    length,extra=struct.unpack_from('<II',body);d=json.loads(body[8:8+length]);a=d['modelAux']
    rows.append({k:a[k] for k in ['timestamp','position','velocity','quaternion','rpmEstimated','massKg','ground']}|{'frame':frame})
 report={'id':run,'label':label,'mode':'REPLAY_ACTUAL_REFERENCE_SITL','physicsCalibration':'NOT_HERA','source':str(p.relative_to(R)),
         'sourceSha256':file_hash.hexdigest(),'walRecordsVerified':sequence,'originalIntentFrames':intents,
         'renderSelection':'Every40th frame only; original1200Hz WAL is unchanged','sampleHz':30,'samples':rows}
 target=H/'assets'/('replay-'+run+'.json');target.write_text(json.dumps(report,separators=(',',':'))+'\n')
 out.append({k:v for k,v in report.items() if k!='samples'}|{'file':target.name,'duration':rows[-1]['timestamp'],'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
(H/'assets/replay-index.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps([{'id':x['id'],'records':x['walRecordsVerified'],'frames':x['originalIntentFrames']} for x in out]))
