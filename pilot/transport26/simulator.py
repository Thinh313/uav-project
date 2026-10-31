"""Explicit start/stop of ONLY the owned isolated simulator. No auto-restart."""
from pathlib import Path
import subprocess,json,sys,shutil,socket,hashlib,datetime
R=Path(__file__).resolve().parents[2];name='aeris-transport26-sitl';image='ubuntu@sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55';E=R/'evidence/transport26'
def run(a):return subprocess.run(a,check=True,capture_output=True,text=True).stdout.strip()
if sys.argv[1]=='start':
 if shutil.disk_usage('/').free<20*1024**3:raise SystemExit('Disk reserve below20GiB')
 if subprocess.run(['docker','container','inspect',name],capture_output=True).returncode==0:raise SystemExit('Owned name occupied; do not interrupt')
 with socket.socket() as s:s.bind(('127.0.0.1',5772))
 attempt=sys.argv[2] if len(sys.argv)>2 else 'state';
 if attempt not in ['state','state02','state03']:raise SystemExit('Fixed bounded state attempts')
 state=R/'.local/transport26'/attempt;state.mkdir(parents=True,exist_ok=True)
 if any(state.iterdir()):raise SystemExit('Nonempty prior state; do not overwrite')
 cmd=['docker','run','--rm','-d','--name',name,'--label','aeris.task=transport26','--platform','linux/amd64','--network','bridge','--cpus','1','--memory','256m','--cap-drop','ALL','--security-opt','no-new-privileges','-p','127.0.0.1:5772:5760','-v',str(R/'runtime/sitl')+':/aeris:ro','-v',str(R/'pilot/transport26')+':/transport26:ro','-v',str(state)+':/state','-w','/state',image,'/aeris/arducopter','-w','--model','quad','--home','10.854,106.807,10,0','--defaults','/aeris/copter.parm,/transport26/sitl.parm','--speedup','1']
 cid=run(cmd);(E/'simulator-launch.json').write_text(json.dumps({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'containerId':cid,'command':cmd,'imageId':run(['docker','image','inspect',image,'--format','{{.Id}}']),'binarySha256':hashlib.sha256((R/'runtime/sitl/arducopter').read_bytes()).hexdigest(),'scope':'Dedicated disarmed instance; no commands to aircraft'},indent=2)+'\n');print(cid)
elif sys.argv[1]=='stop':
 info=json.loads(run(['docker','container','inspect',name]))[0];launch=json.loads((E/'simulator-launch.json').read_text())
 if info['Id']!=launch['containerId'] or info['Config']['Labels'].get('aeris.task')!='transport26':raise SystemExit('Owned identity mismatch')
 (E/'simulator-log.txt').write_text(run(['docker','logs',name]));(E/'simulator-inspect.json').write_text(json.dumps(info,indent=2)+'\n');print(run(['docker','stop','-t','3',name]));print(run(['docker','image','prune','-f']))
else:raise SystemExit('start|stop only')
