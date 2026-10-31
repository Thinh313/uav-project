from pathlib import Path
import subprocess,json,sys,socket,time,os,shutil,hashlib,threading,importlib.util,signal
sys.dont_write_bytecode=True
from bootstrap04 import DockerProbe04, ReadinessJournal04, bootstrap_stream04, stop_owned04, CID04
R=Path(__file__).resolve().parents[3];run=sys.argv[1];case=sys.argv[2];assert __import__('re').fullmatch('s[a-f0-9]{20}',run)and case in ['nominal','loss'];E=R/'evidence/integration03-runtime/runs'/run;
if E.exists():assert sorted(x.name for x in E.iterdir())==['ap-state'] and not any((E/'ap-state').iterdir()),'EXISTING_RUN_EVIDENCE_NO_RESTART'
else:E.mkdir(parents=True)
S=E/'ap-state';S.mkdir(exist_ok=True);NAME='aeris-integration03';IMAGE='ubuntu@sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55';admission=json.loads((R/'evidence/integration03-runtime'/os.environ.get('INTEGRATION03_ADMISSION','admission.json')).read_text());assert admission['status']=='PHASE_ADMITTED' and run in admission['allowedRuns'];assert shutil.disk_usage(R).free>=admission['minAdmissionBytes']
for port in[5937,5938,5939,5940,5941]:
 with socket.socket()as s:s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);s.bind(('127.0.0.1',port))
def cmd(a):return subprocess.check_output(a,text=True,stderr=subprocess.STDOUT,timeout=20).strip()
def put(n,v):
 with(E/n).open('x')as f:json.dump(v,f,indent=2);f.flush();os.fsync(f.fileno())
assert subprocess.run(['docker','inspect',NAME],capture_output=True).returncode!=0;binary=hashlib.sha256((R/'runtime/sitl/arducopter').read_bytes()).hexdigest();assert binary=='011627d41dd95640c3aca02d45283474be48721c8b1bb7a4b234d38b69063482'
a=['docker','run','--rm','-d','--name',NAME,'--label','aeris.task=integration03','--label','aeris.run='+run,'--platform','linux/amd64','--pull','never','--network','bridge','--cpus','2','--memory','512m','--cap-drop','ALL','--security-opt','no-new-privileges','--log-opt','max-size=2m','--log-opt','max-file=2']
for host,guest in[(5937,5766),(5938,5762),(5939,5763),(5940,5767),(5941,5760)]:a+=['-p',f'127.0.0.1:{host}:{guest}']
a+=['-v',str(R/'runtime/sitl')+':/aeris:ro','-v',str(R/'planning/integration03/runtime')+':/task:ro','-v',str(R/'pilot/auto63')+':/baseline:ro','-v',str(S)+':/state','-w','/state',IMAGE,'/aeris/arducopter','-w','--model','quad','--home','10.854,106.807,10,0','--defaults','/aeris/copter.parm,/baseline/sitl-v4.parm,/task/sitl.parm','--serial1=tcp:5762:nowait','--serial2=tcp:5763:nowait','--serial4=tcp:5766:nowait','--serial5=tcp:5767:nowait','--speedup','1'];__import__('shutil').copyfile(R/'native/native98/message-intervals-chan3.txt',S/'message-intervals-chan4.txt');cid=cmd(a);assert CID04.fullmatch(cid),'OWNED_DOCKER_RUN_CID'
launch_info04=lambda:json.loads(cmd(['docker','inspect',cid]))[0]
stopping=False;bootstrapSocket=None;bootstrapThread=None;bootstrapError=None;bootstrapRecords=0;peer=None;observer=None;obs=None;error=None;head='';count=0;lastHB=None;lastLand=None;lastPosition=None;everArmed=False;free=[];obs_error=None
try:
 info=launch_info04();put('launch.json',{'containerId':cid,'pid':info['State']['Pid'],'startedAt':info['State']['StartedAt'],'run':run,'command':a,'binarySha256':binary,'controllerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'parameterSha256':hashlib.sha256((R/'planning/integration03/runtime/sitl.parm').read_bytes()).hexdigest(),'case':case,'hostGCSController':False,'speedup':1,'nativeOnlyGCS':True,'nativeSerial':4,'observerSerial':5,'bootstrapSerial':0,'bootstrapTXBytes':0,'hostGCSCommandBytes':0});print('AP_CREATED_NOT_READY_FOR_ANDROID',flush=True)
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
 bootstrapProgress04={'status':'NOT_STARTED','connectAttempts':0,'txBytes':0}
 readiness04=None
 probe04=DockerProbe04(cid,run)
 def bootstrap():
  global bootstrapSocket,bootstrapError,bootstrapRecords,readiness04
  try:
   readiness04=ReadinessJournal04(E/'bootstrap-readiness04.jsonl')
   with(E/'bootstrap-readonly.jsonl').open('xb')as out:
    def chunk04(b):
     global bootstrapRecords
     bootstrapRecords+=1;line=json.dumps({'n':bootstrapRecords,'hostMonoNs':str(time.monotonic_ns()),'hex':b.hex(),'txBytes':0}).encode()+b'\n';out.write(line);out.flush();os.fsync(out.fileno());assert out.tell()<2**20,'BOOTSTRAP_CAPTURE_BOUND'
    def socket04(value):
     global bootstrapSocket
     bootstrapSocket=value
    bootstrap_stream04(probe04,readiness04.append,chunk04,lambda:stopping,bootstrapProgress04,on_socket=socket04)
  except Exception as e:
   if not stopping:
    bootstrapError=str(e);bootstrapProgress04['status']='FAILED';bootstrapProgress04['error']=bootstrapError
    try:
     if readiness04:readiness04.append({'kind':'BOOTSTRAP_FAILURE','hostMonoNs':str(time.monotonic_ns()),'error':bootstrapError,'progress':dict(bootstrapProgress04),'txBytes':0})
    except Exception:pass
  finally:
   if readiness04:
    try:readiness04.close()
    except Exception as e:bootstrapProgress04['readinessCloseError']=str(e)[:240]
 bootstrapThread=threading.Thread(target=bootstrap,daemon=True);bootstrapThread.start()
 start=time.monotonic();signals=lambda *_:globals().__setitem__('stopping',True);signal.signal(signal.SIGTERM,signals);signal.signal(signal.SIGINT,signals)
 while not stopping:
  free.append(shutil.disk_usage(R).free);assert free[-1]>=admission['runtimeGuardBytes'] and time.monotonic()-start<900,'RESOURCE_OR_DEADLINE'
  if peer is None and 'SERIAL5 on TCP port 5767'in cmd(['docker','logs',cid]):
   f=(E/'peer-console.txt').open('x');peer=subprocess.Popen(['node','planning/integration03/runtime/peers.mjs',run,case],cwd=R,env={**os.environ,'CREW02_EVIDENCE_ROOT':str(E)},stdout=f,stderr=subprocess.STDOUT);observer=threading.Thread(target=observe,daemon=True);observer.start();put('peers-launch.json',{'pid':peer.pid,'scriptSha256':hashlib.sha256((R/'planning/integration03/runtime/peers.mjs').read_bytes()).hexdigest(),'hostGCSCommandBytes':0,'evidenceRoot':str(E)})
  if peer:assert peer.poll()is None,'PEER_DIED'
  if obs_error:raise RuntimeError(obs_error)
  if bootstrapError:raise RuntimeError(bootstrapError)
  if(E/'stop-request.json').exists():
   if lastHB and lastLand and time.monotonic()-lastHB[0]<3 and time.monotonic()-lastLand[0]<3 and not lastHB[1]&128 and lastLand[1]==1:break
  assert sum(p.stat().st_size for p in S.rglob('*')if p.is_file())<64*2**20,'AP_STORAGE_BOUND';time.sleep(.2)
except Exception as e:error=str(e)
finally:
 requested04=stopping or(E/'stop-request.json').exists()
 stopping=True
 cleanupErrors04=[]
 def attempt04(label,fn):
  try:fn()
  except Exception as e:cleanupErrors04.append(label+':'+str(e)[:240])
 def capture04(value):
  value['bootstrapProgress']=dict(globals().get('bootstrapProgress04',{}));value['stopTrigger']=error or('CONTROLLER_SIGNAL'if requested04 and not(E/'stop-request.json').exists()else'SAFE_GROUND_STOP_REQUEST');put('prestop-diagnostics04.json',value)
 probe04=globals().get('probe04')or DockerProbe04(cid,run)
 # Capture state/guest/logs BEFORE any managedAPstop. Other owned-process cleanup
 # cannot suppress the originalreason or prevent the subsequent exactCIDstop.
 def stop_all_owned04(owned):
  if bootstrapSocket:
   attempt04('BOOTSTRAP_SHUTDOWN',lambda:bootstrapSocket.shutdown(socket.SHUT_RDWR));attempt04('BOOTSTRAP_CLOSE',bootstrapSocket.close)
  if bootstrapThread:attempt04('BOOTSTRAP_JOIN',lambda:bootstrapThread.join(3))
  if peer:
   attempt04('PEER_TERMINATE',peer.terminate)
   try:peer.wait(timeout=5)
   except Exception as e:
    cleanupErrors04.append('PEER_WAIT:'+str(e)[:240]);attempt04('PEER_KILL',peer.kill);attempt04('PEER_FINAL_WAIT',lambda:peer.wait(timeout=2))
   if 'f'in globals():attempt04('PEER_CONSOLE_CLOSE',f.close)
  if obs:
   attempt04('OBSERVER_SHUTDOWN',lambda:obs.shutdown(socket.SHUT_RDWR));attempt04('OBSERVER_CLOSE',obs.close)
  if observer:attempt04('OBSERVER_JOIN',lambda:observer.join(3))
  return cmd(['docker','stop','--time','3',owned])
 stop04=stop_owned04(probe04,error,requested04,capture04,stop_all_owned04)
 prelogs04=stop04['preStop']['probes'].get('logs',{})
 if prelogs04.get('ok'):attempt04('LOG_COPY',lambda:(E/'guest-console.txt').write_text(prelogs04['value']['text']))
 cleanupErrors04.extend(stop04['cleanupErrors'])
 closure04={'stopped':stop04['stopSucceeded'],'containerId':cid,'bootstrapTXBytes':0,'bootstrapRecords':bootstrapRecords,'bootstrapError':bootstrapError,'error':error,'originalErrorPreserved':True,'externalStopRequested':requested04,'controllerStopInitiated':True,'stopTrigger':error or('CONTROLLER_SIGNAL'if requested04 and not(E/'stop-request.json').exists()else'SAFE_GROUND_STOP_REQUEST'),'observerError':obs_error,'observerHead':head,'observerRecords':count,'hostGCSCommandBytes':0,'everArmed':everArmed,'lastHeartbeat':lastHB,'lastLand':lastLand,'lastPosition':lastPosition,'minFreeBytes':min(free)if free else None,'cleanupErrors':cleanupErrors04,'bootstrapProgress04':globals().get('bootstrapProgress04',{})}
 attempt04('CLOSURE_WRITE',lambda:put('closure.json',closure04));print('CLOSED '+str(error),flush=True)
