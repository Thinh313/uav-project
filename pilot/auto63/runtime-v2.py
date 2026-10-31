"""Owned, bounded internal-physics mission SITL. No external sensor backend."""
from pathlib import Path
import sys,json,hashlib,shutil,socket,subprocess,time,datetime,signal
R=Path(__file__).resolve().parents[2];P=R/'pilot/auto63';E=R/'evidence/auto63';NAME='aeris-auto63';IMAGE='ubuntu@sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55';BINARY='011627d41dd95640c3aca02d45283474be48721c8b1bb7a4b234d38b69063482'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def put(p,d):
 with p.open('x')as f:json.dump(d,f,indent=2);f.flush();__import__('os').fsync(f.fileno())
def command(a):return subprocess.check_output(a,text=True,stderr=subprocess.STDOUT,timeout=30).strip()
rid=sys.argv[1];assert rid.isalnum()and len(rid)<32;out=E/'runs'/rid;assert out.is_dir();pins=json.loads((E/'source-pins-v2.json').read_text())['files'];assert all(sha(R/n)==h for n,h in pins.items()),'SOURCE_PIN'
assert shutil.disk_usage(R).free>=int(21.25*2**30),'AUTO63_PEAK_21_25GIB';assert sum(json.loads(p.read_text()).get('mode')=='sitl' for p in(E/'runs').glob('*/request.json'))<=2,'MAX_TWO_ACTUAL_ATTEMPTS'
assert sha(R/'runtime/sitl/arducopter')==BINARY
assert subprocess.run(['docker','inspect',NAME],capture_output=True).returncode!=0,'OWNED_CONTAINER_ALREADY_EXISTS'
with socket.socket()as s:s.bind(('127.0.0.1',5880))
i=json.loads(command(['docker','image','inspect',IMAGE]))[0];assert i['Id']==IMAGE.split('@')[1];state=out/'ap-state';state.mkdir();stopped=False
signal.signal(signal.SIGTERM,lambda *_:globals().__setitem__('stopped',True));signal.signal(signal.SIGINT,lambda *_:globals().__setitem__('stopped',True))
a=['docker','run','--rm','-d','--name',NAME,'--label','aeris.task=auto63','--label','aeris.run='+rid,'--platform','linux/amd64','--pull','never','--network','bridge','--cpus','1','--memory','256m','--cap-drop','ALL','--security-opt','no-new-privileges','--log-opt','max-size=2m','--log-opt','max-file=2','-p','127.0.0.1:5880:5760','-v',str(R/'runtime/sitl')+':/aeris:ro','-v',str(P)+':/task:ro','-v',str(state)+':/state','-w','/state',IMAGE,'/aeris/arducopter','-w','--model','quad','--home','10.854,106.807,10,0','--defaults','/aeris/copter.parm,/task/sitl.parm','--speedup','1']
cid=command(a);failure=None
try:
 observed=json.loads(command(['docker','inspect',NAME]))[0];assert observed['Id']==cid and observed['State']['Running']
 deadline=time.monotonic()+25
 while True:
  logtext=command(['docker','logs',NAME])
  if 'Waiting for connection' in logtext and 'SERIAL0 on TCP port 5760' in logtext:break
  assert time.monotonic()<deadline,'GUEST_SERIAL_READY_DEADLINE'
  assert json.loads(command(['docker','inspect',NAME]))[0]['State']['Running'],'GUEST_EXIT_BEFORE_READY'
  time.sleep(.2)
 (out/'guest-before-connect.txt').write_text(logtext)
 put(out/'guest-ready.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'containerId':cid,'serial0ListeningObserved':True,'basis':'GUEST_SERIAL0_LISTEN_CONSOLE_BEFORE_ONE_HOST_CONNECTION','logSha256':sha(out/'guest-before-connect.txt'),'noTCPProbeOrRetry':True})
 put(out/'launch.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'containerId':cid,'imageId':i['Id'],'pid':observed['State']['Pid'],'startedAt':observed['State']['StartedAt'],'command':a,'binarySha256':BINARY,'port':5880,'physics':'ARDUPILOT_INTERNAL_QUAD_NOT_SIM32_OR_HERA','speedup':1,'freeBytes':shutil.disk_usage(R).free,'forecastBytes':256*2**20,'hardDeadlineS':240})
 started=time.monotonic()
 while not stopped and not(out/'stop-request.json').exists():
  if time.monotonic()-started>240:raise RuntimeError('OWNED_SIMULATOR_DEADLINE')
  if shutil.disk_usage(R).free<20.5*2**30:raise RuntimeError('RESOURCE_HEADROOM_LOST')
  if sum(p.stat().st_size for p in state.rglob('*')if p.is_file())>64*2**20:raise RuntimeError('AP_STATE_QUOTA')
  time.sleep(.2)
except BaseException as e:failure=str(e)
finally:
 try:
  observed=json.loads(command(['docker','inspect',NAME]))[0];assert observed['Id']==cid and observed['Config']['Labels']['aeris.run']==rid
  put(out/'inspect-before-stop.json',observed);(out/'ap-console.txt').write_text(command(['docker','logs',NAME]));command(['docker','stop','-t','3',NAME]);deadline=time.monotonic()+10
  while subprocess.run(['docker','inspect',NAME],capture_output=True).returncode==0:
   assert time.monotonic()<deadline,'CONTAINER_REMOVAL_TIMEOUT';time.sleep(.2)
 except BaseException as e:failure=(failure+'; 'if failure else'')+str(e)
 (out/'docker-image-prune.txt').write_text(command(['docker','image','prune','-f']))
 put(out/'closure.json',{'containerId':cid,'stopped':failure is None,'error':failure,'explicitStop':stopped or(out/'stop-request.json').exists(),'freeBytes':shutil.disk_usage(R).free,'stateRetained':True,'notFlightCompletion':True})
if failure:raise SystemExit(1)
