"""Owned AP ground process reboot only. Host sockets are passive and transmit no MAVLink payload."""
from pathlib import Path
import json,sys,time,subprocess,socket,hashlib,importlib.util,os
sys.dont_write_bytecode=True;R=Path(__file__).resolve().parents[2];D=R/'evidence/native96/runs'/sys.argv[1];run=D.name;launch=json.loads((D/'launch.json').read_text());NAME='aeris-native96'
def cmd(a):return subprocess.check_output(a,text=True,stderr=subprocess.STDOUT,timeout=30).strip()
def put(n,v):
 with(D/n).open('x')as f:json.dump(v,f,indent=2);f.flush();os.fsync(f.fileno())
spec=importlib.util.spec_from_file_location('reboot_oracle96',R/'pilot/apstream40/oracle-v2.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);p=m.MAVLink(None);p.robust_parsing=True;latest={}
for l in(D/'observer.jsonl').read_text().splitlines():
 r=json.loads(l)
 for f in p.parse_buffer(bytes.fromhex(r['hex']))or[]:
  if f.get_srcSystem()==42 and f.get_srcComponent()==1:latest[f.get_msgId()]=(int(r['hostMonoNs']),f)
assert all(k in latest and time.monotonic_ns()-latest[k][0]<3e9 for k in[0,33,245]);assert not latest[0][1].base_mode&128 and latest[245][1].landed_state==1 and abs(latest[33][1].relative_alt)<1000;oldboot=latest[33][1].time_boot_ms
before=json.loads(cmd(['docker','inspect',NAME]))[0];assert before['Id']==launch['containerId']and before['State']['Pid']==launch['pid']and before['Config']['Labels']['aeris.run']==run
put('reboot-precondition.json',{'groundDisarmed':True,'oldBootMs':oldboot,'beforeHostMonoNs':time.monotonic_ns(),'containerId':before['Id']})
cmd(['docker','restart','--time','2',NAME]);after=json.loads(cmd(['docker','inspect',NAME]))[0];assert after['Id']==before['Id']and after['State']['Pid']!=before['State']['Pid'];put('reboot-identity.json',{'containerId':after['Id'],'pid':after['State']['Pid'],'startedAt':after['State']['StartedAt'],'oldPid':before['State']['Pid'],'oldStartedAt':before['State']['StartedAt'],'hostMonoNs':time.monotonic_ns(),'scope':'EXPLICIT_GROUND_REBOOT_NOT_FLIGHT_RECOVERY'})
end=time.monotonic()+25
while 'Waiting for connection'not in cmd(['docker','logs','--since',after['State']['StartedAt'],NAME]):assert time.monotonic()<end;time.sleep(.2)
s0=socket.create_connection(('127.0.0.1',5907),3);s0.settimeout(.5)
while 'SERIAL1 on TCP port 5762'not in cmd(['docker','logs','--since',after['State']['StartedAt'],NAME]):assert time.monotonic()<end;time.sleep(.2)
s1=socket.create_connection(('127.0.0.1',5908),3);s1.settimeout(.5);parser=m.MAVLink(None);parser.robust_parsing=True;head='';count=0;latestnew={};prefix=bytearray();started=False;out=(D/'reboot-observer-new-epoch.jsonl').open('xb');deadline=time.monotonic()+20
try:
 while time.monotonic()<deadline:
  try:b=s1.recv(4096)
  except socket.timeout:continue
  assert b,'NEW_EPOCH_EOF';ns=time.monotonic_ns();body={'n':count+1,'previous':head,'hostMonoNs':str(ns),'hex':b.hex()};encoded=json.dumps(body,separators=(',',':')).encode();head=hashlib.sha256(encoded).hexdigest();out.write(encoded[:-1]+b',"sha256":"'+head.encode()+b'"}\n');out.flush();os.fsync(out.fileno());count+=1
  feed=b
  if not started:
   k=next((i for i,v in enumerate(feed)if v in[253,254]),-1);prefix.extend(feed if k<0 else feed[:k]);assert len(prefix)<=1024 and all(v in[9,10,13]or 32<=v<=126 for v in prefix)
   if k<0:continue
   started=True;feed=feed[k:]
  for f in parser.parse_buffer(feed)or[]:
   assert f.get_type()!='BAD_DATA','NEW_EPOCH_CRC'
   if f.get_srcSystem()==42 and f.get_srcComponent()==1:latestnew[f.get_msgId()]=f
  if all(k in latestnew for k in[0,33,245])and latestnew[33].time_boot_ms>=3000:break
 assert all(k in latestnew for k in[0,33,245])and not latestnew[0].base_mode&128 and latestnew[245].landed_state==1
 assert latestnew[33].time_boot_ms<oldboot
 put('reboot-new-boot.json',{'oldBootMs':oldboot,'newBootMs':latestnew[33].time_boot_ms,'transmittedPayloadBytes':0,'groundDisarmed':True,'observerRecords':count,'observerHead':head,'startupPrefixHex':prefix.hex(),'newEpochNeverSplicedWithOld':True,'passiveSerial0OpenedToAllowAPStartup':True})
 print('GROUND_REBOOT_NEW_BOOT_VERIFIED_ZERO_HOST_TX',flush=True)
finally:s0.close();s1.close();out.close()
