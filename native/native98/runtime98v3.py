from pathlib import Path
import subprocess,json,sys,socket,time,os,shutil,hashlib,threading,importlib.util,signal
sys.dont_write_bytecode=True;R=Path(__file__).resolve().parents[2];run=sys.argv[1];case=sys.argv[2];assert __import__('re').fullmatch('s[a-f0-9]{20}',run)and case in ['nominal','loss'];E=R/'evidence/native98/runs'/run;E.mkdir(parents=True);S=E/'ap-state';S.mkdir();NAME='aeris-native98';IMAGE='ubuntu@sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55';assert shutil.disk_usage(R).free>=26*2**30
for port in[5937,5938,5939,5940]:
 with socket.socket()as s:s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);s.bind(('127.0.0.1',port))
def cmd(a):return subprocess.check_output(a,text=True,stderr=subprocess.STDOUT,timeout=20).strip()
def put(n,v):
 with(E/n).open('x')as f:json.dump(v,f,indent=2);f.flush();os.fsync(f.fileno())
assert subprocess.run(['docker','inspect',NAME],capture_output=True).returncode!=0;binary=hashlib.sha256((R/'runtime/sitl/arducopter').read_bytes()).hexdigest();assert binary=='011627d41dd95640c3aca02d45283474be48721c8b1bb7a4b234d38b69063482'
a=['docker','run','--rm','-d','--name',NAME,'--label','aeris.task=native98','--label','aeris.run='+run,'--platform','linux/amd64','--pull','never','--network','bridge','--cpus','2','--memory','512m','--cap-drop','ALL','--security-opt','no-new-privileges','--log-opt','max-size=2m','--log-opt','max-file=2']
for host,guest in[(5937,5760),(5938,5762),(5939,5763),(5940,5766)]:a+=['-p',f'127.0.0.1:{host}:{guest}']
a+=['-v',str(R/'runtime/sitl')+':/aeris:ro','-v',str(R/'native/native98')+':/task:ro','-v',str(R/'pilot/auto63')+':/baseline:ro','-v',str(S)+':/state','-w','/state',IMAGE,'/aeris/arducopter','-w','--model','quad','--home','10.854,106.807,10,0','--defaults','/aeris/copter.parm,/baseline/sitl-v4.parm,/task/sitl98.parm','--serial1=tcp:5762:nowait','--serial2=tcp:5763:nowait','--serial4=tcp:5766:nowait','--speedup','1'];__import__('shutil').copyfile(R/'native/native98/message-intervals-chan3.txt',S/'message-intervals-chan3.txt');cid=cmd(a);info=json.loads(cmd(['docker','inspect',NAME]))[0];put('launch.json',{'containerId':cid,'pid':info['State']['Pid'],'startedAt':info['State']['StartedAt'],'run':run,'command':a,'binarySha256':binary,'controllerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'parameterSha256':hashlib.sha256((R/'native/native98/sitl98.parm').read_bytes()).hexdigest(),'case':case,'hostGCSController':False,'speedup':1,'nativeOnlyGCS':True,'hostGCSCommandBytes':0});print('AP97_WAITING_NATIVE_SERIAL0',flush=True)
stopping=False;peer=None;observer=None;obs=None;error=None;head='';count=0;lastHB=None;lastLand=None;lastPosition=None;everArmed=False;free=[];obs_error=None
spec=importlib.util.spec_from_file_location('m97',R/'pilot/apstream40/oracle-v2.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def observe():
 global obs,head,count,lastHB,lastLand,lastPosition,everArmed,obs_error
 try:
  obs=socket.create_connection(('127.0.0.1',5940),3);obs.settimeout(.5);parser=m.MAVLink(None);parser.robust_parsing=True;started=False;prefix=bytearray()
  with(E/'observer.jsonl').open('xb')as out:
   while not stopping:
    try:b=obs.recv(4096)
    except socket.timeout:continue
    if not b:raise RuntimeError('OBSERVER_EOF')
    body={'n':count+1,'previous':head,'hostMonoNs':str(time.monotonic_ns()),'hex':b.hex()};raw=json.dumps(body,separators=(',',':')).encode();head=hashlib.sha256(raw).hexdigest();out.write(raw[:-1]+b',"sha256":"'+head.encode()+b'"}\n');out.flush();os.fsync(out.fileno());count+=1;assert out.tell()<8*2**20
    if not started:
     k=next((i for i,v in enumerate(b)if v in[253,254]),-1);prefix.extend(b if k<0 else b[:k]);assert len(prefix)<=1024 and all(v in[9,10,13]or 32<=v<=126 for v in prefix)
     if k<0:continue
     b=b[k:];started=True
    for f in parser.parse_buffer(b)or[]:
     assert f.get_type()!='BAD_DATA','OBSERVER_CRC'
     if f.get_srcSystem()==42 and f.get_srcComponent()==1:
      if f.get_msgId()==0:lastHB=(time.monotonic(),f.base_mode,f.custom_mode);everArmed|=bool(f.base_mode&128)
      if f.get_msgId()==245:lastLand=(time.monotonic(),f.landed_state)
      if f.get_msgId()==33:lastPosition=(time.monotonic(),f.lat,f.lon,f.relative_alt)
 except Exception as e:
  if not stopping:obs_error=str(e)
start=time.monotonic();signals=lambda *_:globals().__setitem__('stopping',True);signal.signal(signal.SIGTERM,signals);signal.signal(signal.SIGINT,signals)
try:
 while not stopping:
  free.append(shutil.disk_usage(R).free);assert free[-1]>=20.5*2**30 and time.monotonic()-start<900,'RESOURCE_OR_DEADLINE'
  if peer is None and 'SERIAL4 on TCP port 5766'in cmd(['docker','logs',NAME]):
   f=(E/'peer-console.txt').open('x');peer=subprocess.Popen(['node','native/native98/peers98.mjs',run,case],cwd=R,stdout=f,stderr=subprocess.STDOUT);observer=threading.Thread(target=observe,daemon=True);observer.start();put('peers-launch.json',{'pid':peer.pid,'scriptSha256':hashlib.sha256((R/'native/native98/peers98.mjs').read_bytes()).hexdigest(),'hostGCSCommandBytes':0})
  if peer:assert peer.poll()is None,'PEER_DIED'
  if obs_error:raise RuntimeError(obs_error)
  if(E/'stop-request.json').exists():
   if lastHB and lastLand and time.monotonic()-lastHB[0]<3 and time.monotonic()-lastLand[0]<3 and not lastHB[1]&128 and lastLand[1]==1:break
  assert sum(p.stat().st_size for p in S.rglob('*')if p.is_file())<64*2**20,'AP_STORAGE_BOUND';time.sleep(.2)
except Exception as e:error=str(e)
finally:
 stopping=True
 if peer:
  peer.terminate();peer.wait(timeout=5);f.close()
 if obs:
  try:obs.shutdown(socket.SHUT_RDWR)
  except Exception:pass
  obs.close()
 if observer:observer.join(3)
 info=json.loads(cmd(['docker','inspect',NAME]))[0];assert info['Id']==cid;(E/'guest-console.txt').write_text(cmd(['docker','logs',NAME]));cmd(['docker','stop','--time','3',NAME]);put('closure.json',{'stopped':True,'error':error,'observerError':obs_error,'observerHead':head,'observerRecords':count,'hostGCSCommandBytes':0,'everArmed':everArmed,'lastHeartbeat':lastHB,'lastLand':lastLand,'lastPosition':lastPosition,'minFreeBytes':min(free)});print('CLOSED '+str(error),flush=True)
