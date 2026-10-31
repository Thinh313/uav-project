"""Owned, bounded internal-physics mission SITL. No external sensor backend."""
from pathlib import Path
import sys,json,hashlib,shutil,socket,subprocess,time,datetime,signal
DOCKER='/usr/local/bin/docker'
R=Path(__file__).resolve().parents[3];P=R/'pilot/field02/flight';E=R/'evidence/field02/flight';NAME='aeris-field02';IMAGE='ubuntu@sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55';BINARY='011627d41dd95640c3aca02d45283474be48721c8b1bb7a4b234d38b69063482'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def put(p,d):
 with p.open('x')as f:json.dump(d,f,indent=2);f.flush();__import__('os').fsync(f.fileno())
def command(a):return subprocess.check_output(a,text=True,stderr=subprocess.STDOUT,timeout=30).strip()
rid=sys.argv[1];assert rid.isalnum()and len(rid)<32;out=E/'runs'/rid;assert out.is_dir();generation02=R/'evidence/field02/cockpitvideo04/generation02-flight-pins.json';assert (out/'source-pins.json').read_bytes()==generation02.read_bytes(),'EXACT_GENERATION02_PIN_MANIFEST';pins=json.loads(generation02.read_text())['files'];assert all(sha(R/n)==h for n,h in pins.items()),'SOURCE_PIN'
admission=json.loads((out/'admission.json').read_text());assert len(admission['samples'])==31 and all(s['freeBytes']>=29*2**30 for s in admission['samples']) and admission['durationMs']>=30000,'STABLE_31_SAMPLES_29GIB';assert shutil.disk_usage(R).free>=29*2**30,'FIELD02_ADMISSION_29GIB';assert sum(json.loads(p.read_text()).get('mode')=='sitl' for p in(E/'runs').glob('*/request.json'))<=11,'MAX_ELEVEN_DISTINCT_ATTEMPTS'
assert sha(R/'runtime/sitl/arducopter')==BINARY
assert subprocess.run([DOCKER,'inspect',NAME],capture_output=True).returncode!=0,'OWNED_CONTAINER_ALREADY_EXISTS'
with socket.socket()as s:s.bind(('127.0.0.1',5972))
assert sum(q.stat().st_size for q in (R/'evidence/field02').rglob('*') if q.is_file())<512*2**20,'AGGREGATE_EVIDENCE_QUOTA'
i=json.loads(command([DOCKER,'image','inspect',IMAGE]))[0];assert i['Id']==IMAGE.split('@')[1];state=out/'ap-state';state.mkdir();stopped=False;owner_parent=__import__('os').getppid()
signal.signal(signal.SIGTERM,lambda *_:globals().__setitem__('stopped',True));signal.signal(signal.SIGINT,lambda *_:globals().__setitem__('stopped',True))
a=[DOCKER,'run','--rm','-d','--name',NAME,'--label','aeris.task=field02','--label','aeris.run='+rid,'--platform','linux/amd64','--pull','never','--network','bridge','--cpus','1','--memory','256m','--cap-drop','ALL','--security-opt','no-new-privileges','--log-opt','max-size=2m','--log-opt','max-file=2','-p','127.0.0.1:5972:5760','-v',str(R/'runtime/sitl')+':/aeris:ro','-v',str(P)+':/task:ro','-v',str(state)+':/state','-w','/state',IMAGE,'/aeris/arducopter','-w','--model','quad','--home','10.854,106.807,10,0','--defaults','/aeris/copter.parm,/task/sitl.parm','--speedup','1']
cid=command(a);failure=None
try:
 observed=json.loads(command([DOCKER,'inspect',NAME]))[0];assert observed['Id']==cid and observed['State']['Running']
 deadline=time.monotonic()+25
 while True:
  logtext=command([DOCKER,'logs',NAME])
  if 'Waiting for connection' in logtext and 'SERIAL0 on TCP port 5760' in logtext:break
  assert time.monotonic()<deadline,'GUEST_SERIAL_READY_DEADLINE'
  assert json.loads(command([DOCKER,'inspect',NAME]))[0]['State']['Running'],'GUEST_EXIT_BEFORE_READY'
  time.sleep(.2)
 (out/'guest-before-connect.txt').write_text(logtext)
 put(out/'guest-ready.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'containerId':cid,'serial0ListeningObserved':True,'basis':'GUEST_SERIAL0_LISTEN_CONSOLE_BEFORE_ONE_HOST_CONNECTION','logSha256':sha(out/'guest-before-connect.txt'),'noTCPProbeOrRetry':True})
 put(out/'launch.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'containerId':cid,'imageId':i['Id'],'pid':observed['State']['Pid'],'startedAt':observed['State']['StartedAt'],'command':a,'binarySha256':BINARY,'port':5972,'physics':'ARDUPILOT_INTERNAL_QUAD_NOT_SIM32_OR_HERA','speedup':1,'freeBytes':shutil.disk_usage(R).free,'forecastBytes':256*2**20,'hardDeadlineS':540,'attemptTotalMaximumS':600,'ownerParentPid':owner_parent})
 started=time.monotonic();fault_handled=False
 while not stopped and not(out/'stop-request.json').exists():
  if (out/'fault-request.json').exists() and not fault_handled:
   fault=json.loads((out/'fault-request.json').read_text());assert fault=={'kind':'REBOOT_OWNED_AP_PROCESS','run':rid},'FAULT_REQUEST_BOUND';fault_handled=True
   before=json.loads(command([DOCKER,'inspect',NAME]))[0];assert before['Id']==cid and before['Config']['Labels']['aeris.run']==rid
   put(out/'reboot-intent.json',{'containerId':cid,'beforePid':before['State']['Pid'],'beforeStartedAt':before['State']['StartedAt'],'at':datetime.datetime.now(datetime.timezone.utc).isoformat()})
   command([DOCKER,'restart','-t','2',NAME]);after=json.loads(command([DOCKER,'inspect',NAME]))[0];assert after['Id']==cid and after['State']['Running'] and after['State']['Pid']!=before['State']['Pid'],'OWNED_PROCESS_RESTART_NOT_OBSERVED'
   (out/'reboot-guest-console.txt').write_text(command([DOCKER,'logs',NAME]));put(out/'reboot-observation.json',{'restarted':True,'containerId':cid,'beforePid':before['State']['Pid'],'afterPid':after['State']['Pid'],'beforeStartedAt':before['State']['StartedAt'],'afterStartedAt':after['State']['StartedAt'],'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':'DOCKER_ACTUAL_OWNED_AP_PROCESS_RESTART','noReconnect':True,'mavlinkNewBootObserved':False})
  if __import__('os').getppid()!=owner_parent:raise RuntimeError('APP_PARENT_LOST_CLOSE_OWNED_SIMULATOR')
  if time.monotonic()-started>540:raise RuntimeError('OWNED_SIMULATOR_DEADLINE')
  if shutil.disk_usage(R).free<21*2**30:raise RuntimeError('RESOURCE_HEADROOM_LOST')
  if sum(p.stat().st_size for p in state.rglob('*')if p.is_file())>64*2**20:raise RuntimeError('AP_STATE_QUOTA')
  if sum(p.stat().st_size for p in (R/'evidence/field02').rglob('*')if p.is_file())>512*2**20:raise RuntimeError('FIELD02_EVIDENCE_QUOTA')
  time.sleep(.2)
except BaseException as e:failure=str(e)
finally:
 try:
  observed=json.loads(command([DOCKER,'inspect',NAME]))[0];assert observed['Id']==cid and observed['Config']['Labels']['aeris.run']==rid
  put(out/'inspect-before-stop.json',observed);(out/'ap-console.txt').write_text(command([DOCKER,'logs',NAME]));command([DOCKER,'stop','-t','3',NAME]);deadline=time.monotonic()+10
  while subprocess.run([DOCKER,'inspect',NAME],capture_output=True).returncode==0:
   assert time.monotonic()<deadline,'CONTAINER_REMOVAL_TIMEOUT';time.sleep(.2)
 except BaseException as e:failure=(failure+'; 'if failure else'')+str(e)
 (out/'docker-image-prune.txt').write_text(command([DOCKER,'image','prune','-f']))
 put(out/'closure.json',{'containerId':cid,'stopped':failure is None,'error':failure,'explicitStop':stopped or(out/'stop-request.json').exists(),'freeBytes':shutil.disk_usage(R).free,'stateRetained':True,'notFlightCompletion':True})
if failure:raise SystemExit(1)
