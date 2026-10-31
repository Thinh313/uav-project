"""Loopback PHONE06 challenge service. Not cryptographic/hardware attestation; never sends MAVLink."""
from pathlib import Path
import json,time,hashlib,socket,sys,ipaddress,re,os,signal,secrets
sys.dont_write_bytecode=True
from phase06 import validate_phase,read_json,unique,AP_SHA,R
from rig06 import derived

def guest_ready(raw,port=5766):
 if not isinstance(raw,bytes)or not 1<=len(raw)<=262144:raise ValueError('PHONE_NATIVE_LISTENER_BOUND')
 lines=raw.decode('ascii','strict').splitlines()
 if not 1<=len(lines)<=4097 or 'local_address'not in lines[0]:raise ValueError('PHONE_NATIVE_LISTENER_SCHEMA')
 ready=False
 for line in lines[1:]:
  p=line.split()
  if not p:continue
  if len(p)<10 or not re.fullmatch('[0-9]+:',p[0])or not re.fullmatch('[A-Fa-f0-9]{8}:[A-Fa-f0-9]{4}',p[1])or not re.fullmatch('[A-Fa-f0-9]{8}:[A-Fa-f0-9]{4}',p[2])or not re.fullmatch('[A-Fa-f0-9]{2}',p[3]):raise ValueError('PHONE_NATIVE_LISTENER_SCHEMA')
  address,n=p[1].split(':');ip=ipaddress.ip_address(bytes.fromhex(address)[::-1]);ready|=int(n,16)==port and p[3].upper()=='0A'and not ip.is_loopback
 return {'ready':ready,'port':port,'family':4,'source':'EXACT_OWNED_GUEST_PROC_NET_TCP','sha256':hashlib.sha256(raw).hexdigest()}

def answer(q,phase,launch,state,guest,now_ns):
 keys={'format','nonce','activityBoot','sourceId','run','containerId','binarySha256'}
 if set(q)!=keys or q['format']!='aeris-phone06-challenge'or not re.fullmatch('[a-f0-9-]{36}',q['nonce'])or not re.fullmatch('[a-f0-9-]{36}',q['activityBoot']):raise ValueError('PHONE_CHALLENGE_SCHEMA')
 for k,expected in [('run',launch['run']),('containerId',launch['containerId']),('binarySha256',AP_SHA),('sourceId',phase['nativeSourceId'])]:
  if q[k]!=expected:raise ValueError('PHONE_CHALLENGE_BINDING:'+k)
 if not state['Running']or state['OOMKilled']or state['Error']or state['RestartCount']or state['Pid']!=launch['pid']or state['StartedAt']!=launch['startedAt']or not guest['ready']:raise ValueError('PHONE_CURRENT_OWNED_AP_NOT_READY')
 started=launch.get('hostStartedMonoNs')
 if not isinstance(started,str)or not re.fullmatch('[0-9]{1,20}',started)or now_ns<int(started):raise ValueError('PHONE_HOST_LAUNCH_CLOCK')
 remaining=900000-(now_ns-int(started))//1000000
 if not 1<=remaining<=900000:raise ValueError('PHONE_CAMPAIGN_EXPIRED')
 # Issuing qualification permission requires actual unavailable proof; no flag promotes it.
 return {**q,'format':'aeris-phone06-admission','ok':True,'simulationOnly':True,'hardwareAuthenticated':False,'remainingDurationMs':remaining,'manualActualQualified':False,'neutralProbeAllowed':False,'qualificationIssuance':'UNSUPPORTED_PENDING_ACTUAL_PROOF'}

def main():
 import argparse,types
 a=argparse.ArgumentParser();a.add_argument('--admission',type=Path,required=True);a.add_argument('--launch',type=Path,required=True);args=a.parse_args();phase=validate_phase(args.admission);launch=read_json(args.launch);run=launch['run'];root=R/'evidence/phone06/runtime/runs'/run
 if run not in phase['allowedRuns']or args.launch.resolve()!=root/'launch.json':raise ValueError('PHONE_TICKET_RUN_ROOT')
 helper,_,_=derived();m=types.ModuleType('phone06_bootstrap_owned');exec(compile(helper,'<pinned-phone06-bootstrap>','exec'),m.__dict__);probe=m.DockerProbe04(launch['containerId'],run);seen=set();counter=0;head='';stop=False
 def stopped(*_):nonlocal stop;stop=True
 for sig in(signal.SIGINT,signal.SIGTERM):signal.signal(sig,stopped)
 with(root/'ticket-service.jsonl').open('xb')as log,socket.socket()as server:
  server.bind(('127.0.0.1',5961));server.listen(2);server.settimeout(.5)
  while not stop:
   if __import__('shutil').disk_usage(R).free<21*2**30:raise ValueError('PHONE_TICKET_RESOURCE_STOP')
   if time.monotonic_ns()-int(launch['hostStartedMonoNs'])>=900000000000:break
   try:connection,_=server.accept()
   except socket.timeout:continue
   with connection:
    counter+=1
    if counter>4:raise ValueError('PHONE_TICKET_ATTEMPT_QUOTA')
    requestDeadline=time.monotonic()+3;connection.settimeout(3);data=bytearray();q=None
    try:
     while not data.endswith(b'\n'):
      remaining=requestDeadline-time.monotonic()
      if remaining<=0:raise ValueError('PHONE_CHALLENGE_ABSOLUTE_DEADLINE')
      connection.settimeout(remaining);b=connection.recv(1)
      if not b:raise ValueError('PHONE_CHALLENGE_EOF')
      data.extend(b)
      if len(data)>4096:raise ValueError('PHONE_CHALLENGE_BYTE_BOUND')
     q=json.loads(data,object_pairs_hook=unique)
     if q.get('nonce')in seen:raise ValueError('PHONE_CHALLENGE_REPLAY')
     seen.add(q.get('nonce'));phase=validate_phase(args.admission);before=probe.inspect(.7);guest=guest_ready(probe.runner(['docker','exec',launch['containerId'],'cat','/proc/net/tcp'],.7,262144));after=probe.inspect(.7)
     if before!=after:raise ValueError('PHONE_OWNED_AP_CHANGED_DURING_ADMISSION')
     response=answer(q,phase,launch,after,guest,time.monotonic_ns());secretRoot=R/'.local/phone06/secrets';secretRoot.mkdir(parents=True,exist_ok=True,mode=0o700);os.chmod(secretRoot,0o700);cap=secrets.token_hex(32);secretPath=secretRoot/(run+'.cap');temp=secretRoot/(run+'.new');fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
     with os.fdopen(fd,'w')as secretFile:secretFile.write(cap);secretFile.flush();os.fsync(secretFile.fileno())
     os.replace(temp,secretPath);response['observerReadCapability']=cap
    except Exception as e:response={'ok':False,'error':str(e)[:240],'noRetry':True}
    body={'n':counter,'previous':head,'hostMonoNs':str(time.monotonic_ns()),'request':q,'response':{**{k:v for k,v in response.items()if k!='observerReadCapability'},**({'observerCapabilitySha256':hashlib.sha256(response['observerReadCapability'].encode()).hexdigest()}if 'observerReadCapability'in response else{})},'hostGCSCommandBytes':0};raw=json.dumps(body,separators=(',',':')).encode();head=hashlib.sha256(raw).hexdigest();line=raw[:-1]+b',"sha256":"'+head.encode()+b'"}\n';log.write(line);log.flush();os.fsync(log.fileno());connection.sendall(json.dumps(response).encode()+b'\n')
if __name__=='__main__':main()
