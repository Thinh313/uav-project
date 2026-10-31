"""Read-only verification with previously pinned upstream generated Python dialect, separate from JS runtime framer."""
import sys,importlib.util,json,struct,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];E=R/'evidence/native93';run=sys.argv[1];assert len(run)==21 and run.startswith('s')
p=R/'pilot/apstream40/oracle-v2.py';spec=importlib.util.spec_from_file_location('native91_upstream',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
rx=m.MAVLink(None);tx=m.MAVLink(None);rx.robust_parsing=True;incoming=[];outgoing=[];bad=[]
rows=[json.loads(x)for x in(E/'runs'/run/'raw.jsonl').read_text().splitlines()]
for row in rows:
 if row['kind']not in ['RX_RAW','TX_RAW']:continue
 decoder=rx if row['kind']=='RX_RAW'else tx
 for f in decoder.parse_buffer(bytes.fromhex(row['data']['rawHex']))or[]:
  if f.get_type()=='BAD_DATA':bad.append({'record':row['n'],'reason':f.reason});continue
  (incoming if row['kind']=='RX_RAW'else outgoing).append((row['n'],f))
assert all(f.get_srcSystem()==255 and f.get_srcComponent()==190 for n,f in outgoing)
assert not any(f.get_msgId()in [23,24] for n,f in outgoing)
assert all(f.get_msgId()==0 or getattr(f,'target_system',None)==42 and getattr(f,'target_component',None)==1 for n,f in outgoing)
plan=json.loads((E/'runs'/run/'plan.json').read_text());sent=[f for n,f in outgoing if f.get_type()=='MISSION_ITEM_INT'];expected=plan['compiled']['items'];size=len(expected);assert size>0 and len(sent)==size
float32=lambda n:struct.unpack('<f',struct.pack('<f',n))[0]
for f,item in zip(sent,expected):
 for k in ['seq','command','frame','x','y','autocontinue','mission_type']:assert getattr(f,k)==item[k],k
 for k in ['param1','param2','param3','param4','z']:assert getattr(f,k)==float32(item[k]),k
read=[f for n,f in incoming if f.get_type()=='MISSION_ITEM_INT'and f.get_srcSystem()==42 and f.get_srcComponent()==1 and f.target_system==255 and f.target_component==190]
assert len(read)==2*size
for cycle in [read[:size],read[size:]]:
 for f,item in zip(cycle,expected):
  assert f.seq==item['seq']and f.command==item['command']
  if f.seq==0:continue # Observed Home normalization checked separately by independent JS raw verifier.
  assert f.frame in [item['frame'],{6:3,5:0}.get(item['frame'],item['frame'])] or (item['frame']==2 and f.frame==0 and f.command in [178,206,20] and f.x==f.y==f.z==0), 'FRAME_SEMANTICS'
  for k in ['x','y']:assert getattr(f,k)==item[k]
  for k in ['param1','param2','param3','param4','z']:assert abs(getattr(f,k)-float32(item[k]))<1e-5
camera=[f for f in sent if f.command==206];expected_camera=[i for i in expected if i['command']==206];assert len(camera)==len(expected_camera)>0 and sum(f.param1>0 for f in camera)==sum(i['param1']>0 for i in expected_camera)
commands=[f.command for n,f in outgoing if f.get_type()=='COMMAND_LONG'];assert 400 in commands and 176 in commands
assert any(f.get_type()=='HEARTBEAT'and f.get_srcSystem()==42 and f.custom_mode==3 and f.base_mode&128 for n,f in incoming)
result={'status':'PASS','run':run,'upstreamDialectSha256':hashlib.sha256(p.read_bytes()).hexdigest(),'txFrames':len(outgoing),'rxFrames':len(incoming),'missionItems':size,'readbackCycles':2,'cameraCommands':len(camera),'parameterWrites':0,'startupNonMavlinkRecords':bad,'scope':'UPSTREAM_PYTHON_CRC_TARGET_MISSION_FLOAT32_CAMERA_CHECK_NOT_HERA_OR_IMAGE_EXECUTION'}
(E/('upstream-raw-oracle'+('-'+sys.argv[2]if len(sys.argv)>2 else'')+'.json')).open('x').write(json.dumps(result,indent=2));print({k:v for k,v in result.items()if k!='startupNonMavlinkRecords'})
