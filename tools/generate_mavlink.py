"""Generate a bounded dialect from pinned official XML. No third-party generator/runtime needed."""
import xml.etree.ElementTree as ET,json,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
WANTED={0,1,20,22,24,30,33,40,41,42,43,44,45,46,47,51,73,74,76,77,148,193,242,245,253}
SIZE={'char':1,'uint8_t':1,'int8_t':1,'uint16_t':2,'int16_t':2,'uint32_t':4,'int32_t':4,'uint64_t':8,'int64_t':8,'float':4,'double':8}
def crc(data):
 c=0xffff
 for b in data:
  t=b^(c&255);t^=(t<<4)&255;c=((c>>8)^(t<<8)^(t<<3)^(t>>4))&65535
 return c
out={}
for file in ['minimal.xml','standard.xml','common.xml','ardupilotmega.xml']:
 for m in ET.parse(ROOT/'reference/mavlink'/file).findall('./messages/message'):
  mid=int(m.attrib['id'])
  if mid not in WANTED:continue
  base=[];ext=[];extensions=False
  for f in m:
   if f.tag=='extensions':extensions=True
   if f.tag!='field':continue
   t=f.attrib['type'].replace('uint8_t_mavlink_version','uint8_t');n=int(t.split('[')[1][:-1]) if '[' in t else 0;t=t.split('[')[0]
   (ext if extensions else base).append({'name':f.attrib['name'],'type':t,'array':n})
  base.sort(key=lambda f:-SIZE[f['type']]);offset=0
  raw=(m.attrib['name']+' ').encode()
  for f in base:
   raw+=(f['type']+' '+f['name']+' ').encode()
   if f['array']:raw+=bytes([f['array']])
  c=crc(raw);minimum=sum(SIZE[f['type']]*(f['array'] or 1) for f in base)
  fields=[]
  for f in base+ext:
   fields.append({**f,'offset':offset});offset+=SIZE[f['type']]*(f['array'] or 1)
  out[mid]={'name':m.attrib['name'],'crc':(c&255)^(c>>8),'min':minimum,'max':offset,'fields':fields}
assert set(out)==WANTED, WANTED-set(out)
generated='// Generated from reference/mavlink XML; regenerate with tools/generate_mavlink.py\nexport const DEFINITIONS='+json.dumps(out,indent=2)+';\n'
target=ROOT/'services/mavlink-definitions.mjs'
if '--check' in sys.argv:
 assert target.read_text()==generated,'Generated protocol differs from pinned XML'
else:target.write_text(generated)
print('Generated',len(out),'official MAVLink message definitions')
