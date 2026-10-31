"""Operate only the exact locally owned disarmed SITL container. No pull/build."""
import subprocess,json,sys,socket,hashlib,os
from pathlib import Path
from datetime import datetime,timezone
from guard import R,H,E,sha,free,FLOOR,HEADROOM
NAME='aeris-sitldiscovery41';PORT=5794;IMAGE='ubuntu@sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55'
ATTEMPT=sys.argv[2] if len(sys.argv)>2 else 'run02';assert ATTEMPT in ['run01','run02','run03']
STATE=R/'.local/sitldiscovery41'/ATTEMPT;OUT=E/ATTEMPT
def run(args):
 p=subprocess.run(args,capture_output=True,text=True,timeout=40)
 if p.returncode:
  OUT.mkdir(parents=True,exist_ok=True);n=1
  while (OUT/f'command-failure{n}.json').exists():n+=1
  with (OUT/f'command-failure{n}.json').open('x') as f:json.dump({'command':args,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr},f,indent=2)
  raise RuntimeError(p.stderr)
 return p.stdout.strip()
def put(name,obj):
 with (OUT/name).open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
def inspect():
 info=json.loads(run(['docker','container','inspect',NAME]))[0];launch=json.loads((OUT/'launch.json').read_text())
 assert info['Id']==launch['containerId'] and info['Config']['Labels'].get('aeris.task')=='sitldiscovery41'
 return info
mode=sys.argv[1]
if mode=='start':
 assert free()>=FLOOR+HEADROOM,'budget/floor'
 assert subprocess.run(['docker','container','inspect',NAME],capture_output=True).returncode!=0,'owned name already exists'
 with socket.socket() as s:s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);s.bind(('127.0.0.1',PORT))
 image=json.loads(run(['docker','image','inspect',IMAGE]))[0]
 assert image['Id']=='sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55'
 OUT.mkdir(parents=True,exist_ok=True);STATE.mkdir(parents=True,exist_ok=True);assert not any(STATE.iterdir()) and not (OUT/'launch.json').exists()
 inputs={str(p.relative_to(R)):sha(p) for p in [R/'runtime/sitl/arducopter',R/'runtime/sitl/copter.parm',R/'runtime/sitl/firmware-version.txt',R/'runtime/sitl/git-version.txt',H/'sitl.parm']}
 assert inputs['runtime/sitl/arducopter']=='011627d41dd95640c3aca02d45283474be48721c8b1bb7a4b234d38b69063482'
 cmd=['docker','run','--rm','-d','--name',NAME,'--label','aeris.task=sitldiscovery41','--platform','linux/amd64','--network','bridge','--cpus','1','--memory','256m','--cap-drop','ALL','--security-opt','no-new-privileges','--log-opt','max-size=2m','--log-opt','max-file=2','-p',f'127.0.0.1:{PORT}:5760','-v',str(R/'runtime/sitl')+':/aeris:ro','-v',str(H)+':/task:ro','-v',str(STATE)+':/state','-w','/state',IMAGE,'/aeris/arducopter','-w','--model','quad','--home','10.854,106.807,10,0','--defaults','/aeris/copter.parm,/task/sitl.parm','--speedup','1']
 cid=run(cmd);put('launch.json',{'at':datetime.now(timezone.utc).isoformat(),'containerId':cid,'imageId':image['Id'],'command':cmd,'inputHashes':inputs,'port':PORT,'state':str(STATE.relative_to(R)),'scope':'OWNED_DISARMED_REAL_SITL_ONLY'});put('inspect-start.json',inspect());print(cid)
elif mode=='inspect':
 info=inspect();name=sys.argv[3];assert name in ['before-reboot','after-reboot','before-reboot-attempt02','after-reboot-attempt02'];put('inspect-'+name+'.json',info);put('top-'+name+'.json',{'top':run(['docker','top',NAME,'-eo','pid,args'])});print(json.dumps({'cid':info['Id'],'guestVMInitPid':info['State']['Pid'],'startedAt':info['State']['StartedAt']}))
elif mode=='restart':
 assert free()>=FLOOR+HEADROOM;before=inspect();put('restart-before.json',before);run(['docker','restart','-t','3',NAME]);after=inspect();put('restart-after.json',after);assert after['State']['Pid']!=before['State']['Pid'] and after['State']['StartedAt']!=before['State']['StartedAt'];print(json.dumps({'sameContainer':after['Id']==before['Id'],'oldPid':before['State']['Pid'],'newPid':after['State']['Pid']}))
elif mode=='stop':
 info=inspect();put('inspect-final.json',info);log=run(['docker','logs',NAME]);(OUT/'console-final.txt').write_text(log);assert len(log.encode())<8*2**20
 run(['docker','stop','-t','3',NAME]);assert subprocess.run(['docker','container','inspect',NAME],capture_output=True).returncode!=0
 prune=run(['docker','image','prune','-f']);put('cleanup.json',{'at':datetime.now(timezone.utc).isoformat(),'containerStoppedRemoved':info['Id'],'imagePrune':prune,'stateRetained':str(STATE.relative_to(R)),'freeBytes':free()});print(json.dumps({'stopped':info['Id'],'freeGiB':free()/2**30}))
elif mode=='finalize':
 launch=json.loads((OUT/'launch.json').read_text());p=subprocess.run(['docker','container','inspect',NAME],capture_output=True,text=True)
 if p.returncode==0:
  info=json.loads(p.stdout)[0];assert info['Id']==launch['containerId'] and not info['State']['Running'],'owned process still running or wrong identity'
 else:info=None
 assert p.returncode!=0,'auto-remove still pending; read again later, no stop retry'
 prune=run(['docker','image','prune','-f']);put('cleanup-final.json',{'at':datetime.now(timezone.utc).isoformat(),'containerStoppedRemoved':launch['containerId'],'imagePrune':prune,'stateRetained':str(STATE.relative_to(R)),'freeBytes':free(),'initialStopCheck':'Immediate auto-remove check raced daemon cleanup; stop already returned, no stop retry'});print(json.dumps({'removed':launch['containerId'],'freeGiB':free()/2**30}))
else:raise ValueError('mode')
