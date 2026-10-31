"""Archive/decode the closed QGC03 simulator log, not physical camera evidence."""
from pathlib import Path
import gzip,json,struct,hashlib,collections
root=Path(__file__).resolve().parents[1];out=root/'evidence/qgc03/sitl';p=root/'runtime/sitl/state/logs/00000002.BIN';data=p.read_bytes();formats={128:{'length':89,'name':'FMT'}};pos=0;records=[];counts=collections.Counter()
mapping={'b':('b',1,1),'B':('B',1,1),'h':('h',2,1),'H':('H',2,1),'i':('i',4,1),'I':('I',4,1),'q':('q',8,1),'Q':('Q',8,1),'f':('f',4,1),'d':('d',8,1),'L':('i',4,1e7),'c':('h',2,100),'C':('H',2,100),'e':('i',4,100),'E':('I',4,100),'M':('B',1,1)}
while pos+3<len(data):
 if data[pos:pos+2]!=b'\xa3\x95':pos+=1;continue
 typ=data[pos+2];fmt=formats.get(typ)
 if not fmt:pos+=1;continue
 n=fmt['length']
 if pos+n>len(data):break
 payload=data[pos+3:pos+n]
 if typ==128:
  mid,length,name,types,cols=struct.unpack('<BB4s16s64s',payload);formats[mid]={'length':length,'name':name.decode().strip('\0'),'types':types.decode().strip('\0'),'columns':cols.decode().strip('\0').split(',')}
 elif fmt['name'] in ['CMD','CAM','MODE','ARM','ERR','MSG']:
  rec={};off=0
  for t,c in zip(fmt['types'],fmt['columns']):
   if t in ['n','N','Z']:size={'n':4,'N':16,'Z':64}[t];rec[c]=payload[off:off+size].split(b'\0')[0].decode(errors='replace')
   else:code,size,scale=mapping[t];rec[c]=struct.unpack_from('<'+code,payload,off)[0]/scale
   off+=size
  counts[fmt['name']]+=1;records.append({'type':fmt['name'],**rec})
 pos+=n
archive=out/'sitl-camera.BIN.gz';archive.write_bytes(gzip.compress(data,mtime=0));report={'source':str(p.relative_to(root)),'raw_sha256':hashlib.sha256(data).hexdigest(),'raw_bytes':len(data),'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'counts':dict(counts),'records':records,'scope':'Closed ArduCopter4.7.1 simulator CMD/CAM log. Simulated camera events, no image/hardware claim.'};(out/'dataflash.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'counts':dict(counts),'commands':[r for r in records if r['type']=='CMD'],'arms':[r for r in records if r['type']=='ARM']}))
