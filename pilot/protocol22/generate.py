"""Bounded definitions/oracle from pinned official XML; never edits services/.
The C oracle packs fields using upstream selected headers, not this JS serializer.
"""
import xml.etree.ElementTree as E,json,pathlib,hashlib,re,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2];HERE=ROOT/'pilot/protocol22';REF=ROOT/'reference/protocol22'
WANTED={0,76,77,259,260,262,263,269,270,280,281,285,287}
SIZE={'char':1,'uint8_t':1,'int8_t':1,'uint16_t':2,'int16_t':2,'uint32_t':4,'int32_t':4,'uint64_t':8,'int64_t':8,'float':4,'double':8}
def crc(data):
 c=65535
 for b in data:
  t=b^(c&255);t^=(t<<4)&255;c=((c>>8)^(t<<8)^(t<<3)^(t>>4))&65535
 return c
defs={};xmlpins=[];enums={}
for filename in ['minimal.xml','common.xml']:
 file=REF/filename;xmlpins.append({'path':str(file.relative_to(ROOT)),'sha256':hashlib.sha256(file.read_bytes()).hexdigest()});tree=E.parse(file)
 for enum in tree.findall('./enums/enum'):
  enums[enum.attrib['name']]={entry.attrib['name']:int(entry.attrib['value']) for entry in enum.findall('entry')}
 for m in tree.findall('./messages/message'):
  mid=int(m.attrib['id'])
  if mid not in WANTED:continue
  base=[];ext=[];extension=False
  for f in m:
   if f.tag=='extensions':extension=True
   if f.tag!='field':continue
   t=f.attrib['type'].replace('uint8_t_mavlink_version','uint8_t');n=int(t.split('[')[1][:-1]) if '[' in t else 0;t=t.split('[')[0]
   (ext if extension else base).append(dict(name=f.attrib['name'],type=t,array=n,extension=extension,unit=f.attrib.get('units')))
  xmlfields=[*base,*ext];base.sort(key=lambda f:-SIZE[f['type']]);raw=(m.attrib['name']+' ').encode()
  for f in base:
   raw+=(f['type']+' '+f['name']+' ').encode()
   if f['array']:raw+=bytes([f['array']])
  c=crc(raw);offset=0
  for f in [*base,*ext]:f['offset']=offset;offset+=SIZE[f['type']]*(f['array'] or 1)
  minimum=sum(SIZE[f['type']]*(f['array'] or 1) for f in base)
  header=REF/'c'/('minimal' if mid==0 else 'common')/('mavlink_msg_'+m.attrib['name'].lower()+'.h');h=header.read_text()
  for key,value in [('CRC',(c&255)^(c>>8)),('LEN',offset),('MIN_LEN',minimum)]:assert re.search(r'#define MAVLINK_MSG_ID_'+m.attrib['name']+'_'+key+r'\s+'+str(value)+r'\b',h),('XML/header disagreement',mid,key)
  defs[mid]=dict(name=m.attrib['name'],crc=(c&255)^(c>>8),min=minimum,max=offset,fields=[*base,*ext],xmlOrder=[f['name'] for f in xmlfields])
assert set(defs)==WANTED
(HERE/'definitions.mjs').write_text('// Selected pinned official XML derivative. See generate.py and reference/protocol22.\nexport const DEFINITIONS='+json.dumps(defs,indent=2)+';\n')
selected={key:enums[key] for key in ['MAV_CMD','MAV_RESULT','MAV_TYPE','CAMERA_CAP_FLAGS','GIMBAL_MANAGER_CAP_FLAGS','GIMBAL_DEVICE_FLAGS','GIMBAL_DEVICE_ERROR_FLAGS','CAMERA_ZOOM_TYPE','SET_FOCUS_TYPE']}
(HERE/'enums.json').write_text(json.dumps(selected,indent=2)+'\n');(REF/'xml-pins.json').write_text(json.dumps(xmlpins,indent=2)+'\n')
# Reference program reads decimal fields on stdin, outputs a reference-v2 packet.
src='#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <math.h>\n#define MAVLINK_MAX_PAYLOAD_LEN 255\n#define MAVLINK_STX 253\n#define MAVLINK_COMMAND_24BIT 1\n#define MAVLINK_CRC_EXTRA 1\n#define MAVLINK_ALIGNED_FIELDS 1\n#define MAVLINK_ENDIAN MAVLINK_LITTLE_ENDIAN\n'
table=[]
for mid,d in sorted(defs.items()):
 target={f['name']:f['offset'] for f in d['fields']};flag=3 if 'target_system' in target and 'target_component' in target else 0
 table.append('{'+','.join(map(str,[mid,d['crc'],d['min'],d['max'],flag,target.get('target_system',0),target.get('target_component',0)]))+'}')
src+='#define MAVLINK_MESSAGE_CRCS {'+','.join(table)+'}\n#include "protocol.h"\n'
for mid,d in sorted(defs.items()):src+='#include "'+('minimal' if mid==0 else 'common')+'/mavlink_msg_'+d['name'].lower()+'.h"\n'
src+='static double num(){char b[128];if(scanf("%127s",b)!=1)exit(2);return strtod(b,0);}\nstatic unsigned long long wide(){char b[128];if(scanf("%127s",b)!=1)exit(2);return strtoull(b,0,10);}\nint main(){unsigned id,sys,comp,seq;if(scanf("%u %u %u %u",&id,&sys,&comp,&seq)!=4)return 2;mavlink_message_t msg;mavlink_status_t st={0};st.current_tx_seq=seq;switch(id){\n'
for mid,d in sorted(defs.items()):
 src+=f'case {mid}:{{\n';fields={f['name']:f for f in d['fields']}
 for name in d['xmlOrder']:
  f=fields[name];t=f['type'];n=f['array'];declaration=t+' '+name
  if n:
   src+=declaration+f'[{n}]={{0}};\n'
   if t=='char':src+=f'char in_{name}[512];if(scanf("%511s",in_{name})!=1)return 2;if(strcmp(in_{name},"_")!=0)strncpy({name},in_{name},{n});\n'
   else:src+=f'for(int i=0;i<{n};i++){name}[i]=({t})'+('wide()' if t=='uint64_t' else 'num()')+';\n'
  else:src+=declaration+f'=({t})'+('wide()' if t=='uint64_t' else 'num()')+';\n'
 args=[name for name in d['xmlOrder'] if not(mid==0 and name=='mavlink_version')]
 src+='mavlink_msg_'+d['name'].lower()+'_pack_status(sys,comp,&st,&msg,'+','.join(args)+');break;}\n'
src+='default:return 2;}uint8_t b[280];unsigned n=mavlink_msg_to_send_buffer(b,&msg);for(unsigned i=0;i<n;i++)printf("%02x",b[i]);puts("");return 0;}\n'
(HERE/'oracle.c').write_text(src)
print('Generated',len(defs),'definitions; selected C macros agree with XML')
