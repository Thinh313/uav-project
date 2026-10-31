"""Derive full include closure; independent CRC/layout cross-check; upstream test oracles."""
from pathlib import Path
import json,sys,xml.etree.ElementTree as X,re,importlib.util
from guard import R,H,E,sha,free,FLOOR,BUDGET,append
sys.dont_write_bytecode=True
assert free()>=FLOOR+BUDGET+64*2**20
assert not (H/'definitions.mjs').exists(),'never replace generated pins'
base=R/'runtime/sim32-instrument01-build/ardupilot/modules/mavlink';xmlroot=base/'message_definitions/v1.0'
sys.path.insert(0,str(base))
from pymavlink.generator import mavparse,mavgen_python
sizes={'char':1,'uint8_t':1,'int8_t':1,'uint16_t':2,'int16_t':2,'uint32_t':4,'int32_t':4,'uint64_t':8,'int64_t':8,'float':4,'double':8}
def crc(data):
 c=65535
 for b in data:
  t=b^(c&255);t^=(t<<4)&255;c=((c>>8)^(t<<8)^(t<<3)^(t>>4))&65535
 return c
visited=set();paths=[]
def visit(name):
 assert re.fullmatch(r'[A-Za-z0-9]+\.xml',name)
 if name in visited:return
 visited.add(name);p=xmlroot/name;t=X.parse(p)
 for inc in t.findall('include'):visit(inc.text.strip())
 paths.append(p)
visit('ardupilotmega.xml');definitions={};parsed=[];pins={str(p.relative_to(R)):sha(p) for p in paths}
for p in paths:
 u=mavparse.MAVXML(str(p),wire_protocol_version='2.0');u.enum=[];parsed.append(u);byid={m.id:m for m in u.message}
 for m in X.parse(p).findall('./messages/message'):
  mid=int(m.attrib['id']);assert mid not in definitions,'duplicate dialect id';basefields=[];extensions=[];extended=False
  for f in m:
   if f.tag=='extensions':extended=True
   if f.tag!='field':continue
   raw=f.attrib['type'].replace('uint8_t_mavlink_version','uint8_t');array=int(raw.split('[')[1][:-1]) if '[' in raw else 0
   (extensions if extended else basefields).append({'name':f.attrib['name'],'type':raw.split('[')[0],'array':array,'extension':extended,'unit':f.attrib.get('units'),'invalid':f.attrib.get('invalid'),'multiplier':f.attrib.get('multiplier')})
  basefields.sort(key=lambda f:-sizes[f['type']]);checksum=(m.attrib['name']+' ').encode();offset=0
  for f in basefields:
   checksum+=(f['type']+' '+f['name']+' ').encode()
   if f['array']:checksum+=bytes([f['array']])
  for f in basefields+extensions:f['offset']=offset;offset+=sizes[f['type']]*(f['array'] or 1)
  cc=crc(checksum);d={'name':m.attrib['name'],'crc':(cc&255)^(cc>>8),'min':sum(sizes[f['type']]*(f['array'] or 1) for f in basefields),'max':offset,'fields':basefields+extensions}
  upstream=byid[mid];assert (upstream.crc_extra,upstream.wire_min_length,upstream.wire_length)==(d['crc'],d['min'],d['max']) and upstream.ordered_fieldnames==[f['name'] for f in d['fields']]
  assert 0<=mid<=16777215 and 0<offset<=255;definitions[mid]=d
for file in ['mavparse','mavgen_python','mavtemplate','mavcrc']:pins[str((base/f'pymavlink/generator/{file}.py').relative_to(R))]=sha(base/f'pymavlink/generator/{file}.py')
oldtext=(R/'pilot/mavflight37/definitions.mjs').read_text();old=json.loads(oldtext.split('export const DEFINITIONS=',1)[1].rstrip().rstrip(';'))
overlap=[]
sig=lambda fs:[{k:f[k] for k in ['name','type','array','extension','offset']} for f in fs]
for id,d in old.items():
 current=definitions[int(id)];assert all(current[k]==d[k] for k in ['name','crc','min']) and sig([f for f in current['fields'] if not f['extension']])==sig([f for f in d['fields'] if not f['extension']]),'base wire mapping changed'
 overlap.append({'id':int(id),'oldMax':d['max'],'fullMax':current['max'],'sameFullDefinition':current=={k:d[k] for k in current},'baseLayoutCRCMatches':True})
assert definitions[22]['max']==25 and definitions[148]['max']==78 and definitions[148]['crc']==178
append('overlap',{'scope':'Runtime-tree full dialect and older captured subset are distinct XML snapshots; base mapping matches, no history edited','messages':overlap,'initialPrepareFailure':'Strict full-definition equality rejected different snapshots before generating artifacts; no physical firmware cause inferred'})
with (H/'definitions.mjs').open('x') as f:f.write('// Full pinned XML closure; see evidence/apstream40/schema1.json.\nexport const DEFINITIONS='+json.dumps(definitions,separators=(',',':'))+';\n')
mavgen_python.generate(str(H/'oracle-v2.py'),parsed)
parsed1=[]
for p in paths:
 u=mavparse.MAVXML(str(p),wire_protocol_version='1.0');u.enum=[];u.message=[m for m in u.message if m.id<=255];parsed1.append(u)
mavgen_python.generate(str(H/'oracle-v1.py'),parsed1)
vectors=[]
for ver in [1,2]:
 spec=importlib.util.spec_from_file_location('aeris_apstream40_oracle'+str(ver),H/f'oracle-v{ver}.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 for id,d in sorted(definitions.items()):
  if ver==1 and id>255:continue
  cls=module.mavlink_map[id]
  for pattern in [0,1]:
   fields={}
   for k,field in enumerate(d['fields']):
    if field['name'] not in cls.fieldnames:continue
    def value(n):
     if not pattern:return 0
     if field['type'] in ['float','double']:return (k+n+1)/4
     if '64' in field['type']:return 9007199254740993+k+n
     return (k+n+1)%32
    if field['type']=='char':fields[field['name']]=b'TEST'[:field['array']] if pattern else b''
    elif field['array']:fields[field['name']]=[value(n) for n in range(field['array'])]
    else:fields[field['name']]=value(0)
   if id==0:fields['mavlink_version']=3
   msg=cls(**fields);sender=module.MAVLink(None,srcSystem=1,srcComponent=1);sender.seq=(id+pattern)%256;raw=msg.pack(sender)
   decoded=module.MAVLink(None).parse_char(raw).to_dict();decoded.pop('mavpackettype',None)
   def safe(field,value):
    if field['type']=='char':return value.decode('ascii') if isinstance(value,bytes) else value
    if '64' in field['type']:return [str(x) for x in value] if isinstance(value,list) else str(value)
    return value
   fdict={field['name']:field for field in d['fields']}
   # v1 generated oracle has no extension fields; full decoder must zero-pad those.
   expected={k:safe(fdict[k],v) for k,v in decoded.items()}
   for field in d['fields']:
    if field['name'] not in expected:
     z='' if field['type']=='char' else '0' if '64' in field['type'] else 0
     expected[field['name']]=[z]*field['array'] if field['array'] and field['type']!='char' else z
   vectors.append({'id':id,'version':ver,'pattern':pattern,'rawHex':raw.hex(),'expected':expected})
append('schema',{'dialect':'ardupilotmega','xmlFiles':len(paths),'messages':len(definitions),'messageIds':sorted(definitions),'allLayoutCRCMatches':len(definitions),'old18BaseLayoutCRCMatch':True,'fullSubsetSnapshotEquality':False,'pins':pins,'oracleLicense':'UPSTREAM_GENERATED_PYTHON_GPL-3.0-or-later_TEST_ONLY','xmlLicense':'reference/mavlink/COPYING','runtimeBinaryAssociation':'NOT_CHECKED','builds':0,'installs':0})
append('oracle-vectors',{'origin':'UPSTREAM_PINNED_TEST_SERIALIZER','vectors':vectors,'oracleHashes':{str((H/f'oracle-v{v}.py').relative_to(R)):sha(H/f'oracle-v{v}.py') for v in [1,2]},'pins':pins})
print(json.dumps({'messages':len(definitions),'xmlFiles':len(paths),'vectors':len(vectors),'v1Messages':sum(id<=255 for id in definitions)}))
