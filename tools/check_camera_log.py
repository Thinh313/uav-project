"""Read official DataFlash FMT/CAM records. Preserve log hash and selected records, no flight data modification."""
import pathlib,struct,hashlib,json,os
root=pathlib.Path(__file__).resolve().parents[1];p=sorted((root/'runtime/sitl/state/logs').glob('*.BIN'))[-1]
data=p.read_bytes();formats={128:{'length':89,'name':'FMT'}};pos=0;records=[];cams=[]
while pos+3<len(data):
 if data[pos:pos+2]!=b'\xa3\x95':pos+=1;continue
 typ=data[pos+2];fmt=formats.get(typ)
 if not fmt:pos+=1;continue
 n=fmt['length']
 if pos+n>len(data):break
 payload=data[pos+3:pos+n]
 if typ==128:
  mid,length,name,types,columns=struct.unpack('<BB4s16s64s',payload)
  formats[mid]={'length':length,'name':name.decode().strip('\0'),'types':types.decode().strip('\0'),'columns':columns.decode().strip('\0').split(',')}
 elif fmt['name']=='CAM':
  out={};offset=0
  mappings={'b':('b',1,1),'B':('B',1,1),'h':('h',2,1),'H':('H',2,1),'i':('i',4,1),'I':('I',4,1),'q':('q',8,1),'Q':('Q',8,1),'f':('f',4,1),'d':('d',8,1),'L':('i',4,1e7),'c':('h',2,100),'C':('H',2,100),'e':('i',4,100),'E':('I',4,100),'M':('B',1,1)}
  for t,c in zip(fmt['types'],fmt['columns']):
   code,size,scale=mappings[t];out[c]=struct.unpack_from('<'+code,payload,offset)[0]/scale;offset+=size
  cams.append(out)
 pos+=n
report={'source_path':str(p.relative_to(root)),'source_sha256':hashlib.sha256(data).hexdigest(),'source_bytes':len(data),'cam_formats':[f for f in formats.values() if f['name']=='CAM'],'cam_count':len(cams),'cam_records':cams,'scope':'ArduPilot simulated camera-trigger DataFlash evidence; no physical images captured'}
(root/os.environ.get('AERIS_EVIDENCE_DIR','evidence/flight01')/'camera-log.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'cam_count':len(cams),'source_bytes':len(data),'cam_formats':report['cam_formats']}))
if not cams:raise SystemExit('No CAM records; camera trigger execution NOT_CHECKED')
