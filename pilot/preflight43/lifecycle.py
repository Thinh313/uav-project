import subprocess,json,sys,socket,time
from datetime import datetime,timezone
from guard import R,H,E,sha,free,FLOOR,HEADROOM,BUDGET,check
NAME='aeris-preflight43';PORT=5798;IMAGE='ubuntu@sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55'
runid=sys.argv[2];assert runid in ['run01','run02','run03'];O=E/runid;S=R/'.local/preflight43'/runid

def put(n,o):
 O.mkdir(parents=True,exist_ok=True)
 with (O/n).open('x') as f:json.dump(o,f,indent=2);f.write('\n')
def cmd(a):
 p=subprocess.run(a,text=True,capture_output=True,timeout=40)
 if p.returncode:
  n=1
  while (O/f'command-failure{n}.json').exists():n+=1
  put(f'command-failure{n}.json',{'command':a,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr});raise RuntimeError(p.stderr)
 return p.stdout.strip()
def inspect():
 i=json.loads(cmd(['docker','inspect',NAME]))[0];l=json.loads((O/'launch.json').read_text());assert i['Id']==l['containerId'] and i['Config']['Labels'].get('aeris.task')=='preflight43' and i['Image']==l['imageId'];return i
mode=sys.argv[1]
if mode=='start':
 check();assert free()>=FLOOR+HEADROOM+BUDGET;assert subprocess.run(['docker','inspect',NAME],capture_output=True).returncode!=0
 with socket.socket() as s:s.bind(('127.0.0.1',PORT))
 i=json.loads(cmd(['docker','image','inspect',IMAGE]))[0];assert i['Id']==IMAGE.split('@')[1];assert sha(R/'runtime/sitl/arducopter')=='011627d41dd95640c3aca02d45283474be48721c8b1bb7a4b234d38b69063482'
 O.mkdir(parents=True,exist_ok=True);S.mkdir(parents=True,exist_ok=True);assert not any(S.iterdir()) and not (O/'launch.json').exists()
 inputs={str(p.relative_to(R)):sha(p) for p in [R/'runtime/sitl/arducopter',R/'runtime/sitl/copter.parm',R/'runtime/sitl/firmware-version.txt',R/'runtime/sitl/git-version.txt',H/'sitl.parm']}
 a=['docker','run','--rm','-d','--name',NAME,'--label','aeris.task=preflight43','--platform','linux/amd64','--cpus','1','--memory','256m','--cap-drop','ALL','--security-opt','no-new-privileges','--log-opt','max-size=2m','--log-opt','max-file=2','-p',f'127.0.0.1:{PORT}:5760','-v',str(R/'runtime/sitl')+':/aeris:ro','-v',str(H)+':/task:ro','-v',str(S)+':/state','-w','/state',IMAGE,'/aeris/arducopter','-w','--model','quad','--home','10.854,106.807,10,0','--defaults','/aeris/copter.parm,/task/sitl.parm','--speedup','1']
 cid=cmd(a);put('launch.json',{'at':datetime.now(timezone.utc).isoformat(),'containerId':cid,'imageId':i['Id'],'inputHashes':inputs,'command':a,'scope':'READONLY_PREFLIGHT43','port':PORT});put('inspect-start.json',inspect());print(cid)
elif mode=='inspect':
 i=inspect();n=sys.argv[3];assert n in ['before-qa','after-reboot','after-qa'];put('inspect-'+n+'.json',i);put('top-'+n+'.json',{'top':cmd(['docker','top',NAME,'-eo','pid,args'])});print(json.dumps({'cid':i['Id'],'pid':i['State']['Pid'],'startedAt':i['State']['StartedAt'],'running':i['State']['Running']}))
elif mode=='restart':
 before=inspect();put('restart-before.json',before);assert free()>=FLOOR+HEADROOM;cmd(['docker','restart','-t','3',NAME]);after=inspect();put('restart-after.json',after);assert before['State']['Pid']!=after['State']['Pid'] and before['State']['StartedAt']!=after['State']['StartedAt'];print(json.dumps({'cid':after['Id'],'pid':after['State']['Pid'],'startedAt':after['State']['StartedAt']}))
elif mode=='stop':
 i=inspect();put('inspect-final.json',i);logs=cmd(['docker','logs',NAME]);assert len(logs.encode())<8*2**20
 with (O/'console-final.txt').open('x') as f:f.write(logs)
 cmd(['docker','stop','-t','3',NAME]);deadline=time.monotonic()+10
 while subprocess.run(['docker','inspect',NAME],capture_output=True).returncode==0:
  assert time.monotonic()<deadline,'pending removal; no stop retry';time.sleep(.2)
 prune=cmd(['docker','image','prune','-f']);put('cleanup.json',{'containerStoppedRemoved':i['Id'],'imagePrune':prune,'freeBytes':free(),'stateBytes':sum(p.stat().st_size for p in S.rglob('*') if p.is_file())});print(json.dumps({'removed':i['Id'],'freeGiB':free()/2**30}))
else:raise ValueError(mode)
