"""Explicit lifecycle of only the owned APROUTE28 container; no automatic restart."""
from pathlib import Path
import subprocess,json,sys,shutil,socket,hashlib,datetime
R=Path(__file__).resolve().parents[2];E=R/'evidence/aproute28'
NAME='aeris-aproute28-sitl';IMAGE='ubuntu@sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55'
def run(a):return subprocess.run(a,check=True,capture_output=True,text=True).stdout.strip()
mode=sys.argv[1];attempt=sys.argv[2] if len(sys.argv)>2 else 'run01'
if attempt not in ['run01','run02','run03','run04','run05','run06']:raise SystemExit('Bounded explicit attempts only')
out=E/attempt;out.mkdir(exist_ok=True)
if mode=='start':
 if shutil.disk_usage('/').free<20*1024**3:raise SystemExit('Disk reserve below20GiB')
 if subprocess.run(['docker','container','inspect',NAME],capture_output=True).returncode==0:raise SystemExit('Owned name occupied; never take over')
 for port in [5774,5775,5776]:
  with socket.socket() as s:
   s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
   s.bind(('127.0.0.1',port))
 state=R/'.local/aproute28'/attempt;state.mkdir(parents=True,exist_ok=True)
 if any(state.iterdir()) or (out/'simulator-launch.json').exists():raise SystemExit('Prior state/evidence exists; preserve')
 cmd=['docker','run','--rm','-d','--name',NAME,'--label','aeris.task=aproute28','--platform','linux/amd64','--network','bridge','--cpus','1','--memory','256m','--cap-drop','ALL','--security-opt','no-new-privileges','-p','127.0.0.1:5774:5760','-p','127.0.0.1:5775:5762','-p','127.0.0.1:5776:5763','-v',str(R/'runtime/sitl')+':/aeris:ro','-v',str(R/'pilot/aproute28')+':/aproute28:ro','-v',str(state)+':/state','-w','/state',IMAGE,'/aeris/arducopter','-w','--model','quad','--home','10.854,106.807,10,0','--defaults','/aeris/copter.parm,/aproute28/sitl.parm','--serial1=tcp:5762:nowait','--serial2=tcp:5763:nowait','--speedup','1']
 cid=run(cmd);(out/'simulator-launch.json').write_text(json.dumps({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'containerId':cid,'command':cmd,'imageId':run(['docker','image','inspect',IMAGE,'--format','{{.Id}}']),'binarySha256':hashlib.sha256((R/'runtime/sitl/arducopter').read_bytes()).hexdigest(),'configSha256':hashlib.sha256((R/'pilot/aproute28/sitl.parm').read_bytes()).hexdigest(),'scope':'Disarmed actual AP router; synthetic payload ports; no flight'},indent=2)+'\n');print(cid)
elif mode=='stop':
 info=json.loads(run(['docker','container','inspect',NAME]))[0];launch=json.loads((out/'simulator-launch.json').read_text())
 if info['Id']!=launch['containerId'] or info['Config']['Labels'].get('aeris.task')!='aproute28':raise SystemExit('Owned identity mismatch')
 (out/'simulator-log.txt').write_text(run(['docker','logs',NAME]));(out/'simulator-inspect.json').write_text(json.dumps(info,indent=2)+'\n');print(run(['docker','stop','-t','3',NAME]));print(run(['docker','image','prune','-f']))
else:raise SystemExit('start|stop only')
