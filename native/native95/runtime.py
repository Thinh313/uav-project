"""Only AP physics/autopilot + passive serial1 observer. ZERO GCS/flight payload TX on host."""
from pathlib import Path
import sys,os,json,hashlib,socket,subprocess,time,shutil,signal,datetime,threading
R=Path(__file__).resolve().parents[2];E=R/'evidence/native95';IMAGE='ubuntu@sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55';NAME='aeris-native95';BINARY='011627d41dd95640c3aca02d45283474be48721c8b1bb7a4b234d38b69063482';run=sys.argv[1];assert run.startswith('s')and len(run)==21 and run[1:].isalnum();out=E/'runs'/run;out.mkdir(parents=True,exist_ok=False);assert shutil.disk_usage(R).free>=26*2**30
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(name,d):
 with(out/name).open('x')as f:json.dump(d,f,indent=2);f.flush();os.fsync(f.fileno())
def cmd(a):return subprocess.check_output(a,text=True,stderr=subprocess.STDOUT,timeout=20).strip()
assert sha(R/'runtime/sitl/arducopter')==BINARY
assert subprocess.run(['docker','inspect',NAME],capture_output=True).returncode!=0
for port in[5907,5908]:
 with socket.socket()as s:s.bind(('127.0.0.1',port))
pins=json.loads((E/'runtime-pins.json').read_text());assert all(sha(R/p)==h for p,h in pins['files'].items());put('runtime-pins-at-start.json',pins)
state=out/'ap-state';state.mkdir();args=['docker','run','--rm','-d','--name',NAME,'--label','aeris.task=native95','--label','aeris.run='+run,'--platform','linux/amd64','--pull','never','--network','bridge','--cpus','1','--memory','256m','--cap-drop','ALL','--security-opt','no-new-privileges','--log-opt','max-size=2m','--log-opt','max-file=2','-p','127.0.0.1:5907:5760','-p','127.0.0.1:5908:5762','-v',str(R/'runtime/sitl')+':/aeris:ro','-v',str(R/'pilot/auto63')+':/baseline:ro','-v',str(R/'native/native95')+':/task:ro','-v',str(state)+':/state','-w','/state',IMAGE,'/aeris/arducopter','-w','--model','quad','--home','10.854,106.807,10,0','--defaults','/aeris/copter.parm,/baseline/sitl-v4.parm,/task/serial95.parm','--speedup','1','--serial1=tcp:5762']
cid=cmd(args);i=json.loads(cmd(['docker','inspect',NAME]))[0];stopping=False;signal.signal(signal.SIGTERM,lambda *_:globals().__setitem__('stopping',True));signal.signal(signal.SIGINT,lambda *_:globals().__setitem__('stopping',True));start=time.monotonic();observer=None;obs_socket=None;obs_error=None;obs_count=0;obs_head='';obs_started=False;raw=(out/'observer.jsonl').open('xb');samples=[];failure=None
# Pinned generated upstream Python parser for independent observations, never sends bytes.
import importlib.util
sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('upstream95',R/'pilot/apstream40/oracle-v2.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);parser=m.MAVLink(None);parser.robust_parsing=True;last_hb=None;last_land=None;last_position=None;ever_armed=False

def observe():
 global obs_socket,obs_error,obs_count,obs_head,last_hb,last_land,last_position,ever_armed
 try:
  s=socket.create_connection(('127.0.0.1',5908),timeout=3);obs_socket=s;s.settimeout(.5);put('observer-ready.json',{'endpoint':'127.0.0.1:5908','transmittedPayloadBytes':0,'passive':True})
  while not stopping:
   try:b=s.recv(4096)
   except socket.timeout:continue
   if not b:break
   ns=time.monotonic_ns();body={'n':obs_count+1,'previous':obs_head,'hostMonoNs':str(ns),'hex':b.hex()};encoded=json.dumps(body,separators=(',',':')).encode();h=hashlib.sha256(encoded).hexdigest();raw.write(encoded[:-1]+b',"sha256":"'+h.encode()+b'"}\n');raw.flush();os.fsync(raw.fileno());obs_count+=1;obs_head=h
   if raw.tell()>16*2**20:raise RuntimeError('PASSIVE_RAW_BOUND')
   for f in parser.parse_buffer(b)or[]:
    if f.get_type()=='BAD_DATA':raise RuntimeError('PASSIVE_CRC_BAD_DATA')
    if f.get_srcSystem()!=42 or f.get_srcComponent()!=1:continue
    if f.get_type()=='HEARTBEAT':last_hb=(time.monotonic(),f.base_mode,f.custom_mode);ever_armed|=bool(f.base_mode&128)
    if f.get_type()=='EXTENDED_SYS_STATE':last_land=(time.monotonic(),f.landed_state)
    if f.get_type()=='GLOBAL_POSITION_INT':last_position=(time.monotonic(),f.lat,f.lon,f.relative_alt)
 except Exception as e:obs_error=str(e)
 finally:
  if obs_socket:obs_socket.close()
try:
 deadline=time.monotonic()+25
 while True:
  log=cmd(['docker','logs',NAME])
  if'SERIAL0 on TCP port 5760'in log and'Waiting for connection'in log:break
  assert time.monotonic()<deadline,'AP_SERIAL0_READY_DEADLINE';time.sleep(.2)
 put('launch.json',{'run':run,'containerId':cid,'imageId':i['Image'],'pid':i['State']['Pid'],'startedAt':i['State']['StartedAt'],'binarySha256':BINARY,'command':args,'speedup':1,'nativeEndpoint':'10.0.2.2:5907','source':'ARDUPILOT_INTERNAL_QUAD_NOT_HERA','hostGCSController':False,'hostGCSTransmittedPayloadBytes':0,'freeBytes':shutil.disk_usage(R).free});print(json.dumps({'run':run,'serial0':5907,'serial1Passive':5908}),flush=True)
 while not stopping:
  free=shutil.disk_usage(R).free;samples.append(free);assert free>=20.5*2**30,'HOST_RESERVE';assert time.monotonic()-start<900,'OWNED_RUNTIME_DEADLINE'
  if not obs_started:
   log=cmd(['docker','logs',NAME])
   if'SERIAL1 on TCP port 5762'in log:
    obs_started=True;observer=threading.Thread(target=observe,daemon=True);observer.start()
  if obs_error:raise RuntimeError(obs_error)
  if(out/'stop-request.json').exists():
   if not ever_armed or last_hb and last_land and not(last_hb[1]&128)and last_land[1]==1 and time.monotonic()-last_hb[0]<3 and time.monotonic()-last_land[0]<3:break
  if sum(p.stat().st_size for p in state.rglob('*')if p.is_file())>64*2**20:raise RuntimeError('AP_STORAGE_BOUND')
  time.sleep(.2)
except BaseException as e:failure=str(e)
finally:
 stopping=True
 if obs_socket:
  try:obs_socket.shutdown(socket.SHUT_RDWR)
  except Exception:pass
 if observer:observer.join(timeout=3)
 raw.close();before=json.loads(cmd(['docker','inspect',NAME]))[0];assert before['Id']==cid;logs=cmd(['docker','logs',NAME]);(out/'guest-console.txt').write_text(logs);cmd(['docker','stop','--time','3',NAME]);put('closure.json',{'stopped':True,'error':failure,'observerError':obs_error,'observerRecords':obs_count,'observerHead':obs_head,'observerTransmittedPayloadBytes':0,'everArmedObserved':ever_armed,'lastHeartbeat':last_hb,'lastLanded':last_land,'lastPosition':last_position,'minFreeBytes':min(samples)if samples else shutil.disk_usage(R).free});print('CLOSED '+str(failure),flush=True)
