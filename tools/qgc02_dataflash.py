"""Read FMT/MODE/ERR/MSG/CAM from the closed task simulator log; retain gzip and hash."""
import pathlib,struct,hashlib,json,gzip,collections
root=pathlib.Path(__file__).resolve().parents[1];out=root/'evidence/qgc02/failsafe';out.mkdir(parents=True,exist_ok=True)
p=sorted((root/'runtime/sitl/state/logs').glob('*.BIN'))[-1];data=p.read_bytes();formats={128:{'length':89,'name':'FMT'}};pos=0;selected=[];counts=collections.Counter()
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
 elif fmt['name'] in ['MODE','ERR','MSG','CAM']:
  rec={};off=0
  for t,c in zip(fmt['types'],fmt['columns']):
   if t in ['n','N','Z']:size={'n':4,'N':16,'Z':64}[t];rec[c]=payload[off:off+size].split(b'\0')[0].decode(errors='replace')
   else:code,size,scale=mapping[t];rec[c]=struct.unpack_from('<'+code,payload,off)[0]/scale
   off+=size
  counts[fmt['name']]+=1;selected.append({'type':fmt['name'],**rec})
 pos+=n
archive=out/'sitl-failsafe.BIN.gz';archive.write_bytes(gzip.compress(data,mtime=0));report={'source':str(p.relative_to(root)),'raw_sha256':hashlib.sha256(data).hexdigest(),'raw_bytes':len(data),'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'counts':dict(counts),'records':selected,'scope':'Closed simulator log; MODE reason / ERR / MSG / simulated CAM, not hardware images'};(out/'dataflash.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'counts':dict(counts),'modes':[r for r in selected if r['type']=='MODE'],'errors':[r for r in selected if r['type']=='ERR']}))
mode_times={r['TimeUS'] for r in selected if r['type']=='MODE' and r.get('Mode')==6 and r.get('Rsn')==5};error_times={r['TimeUS'] for r in selected if r['type']=='ERR' and r.get('Subsys')==8 and r.get('ECode')==1};
if len(mode_times&error_times)!=3:raise SystemExit('Missing exactly three paired GCS failsafe RTL changes')
