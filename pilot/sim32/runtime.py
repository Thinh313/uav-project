"""Explicit owned simulator lifecycle, no image pulls/automatic restart/old state writes."""
from pathlib import Path
import subprocess,json,sys,shutil,socket,hashlib,time,os,signal,datetime
R=Path(__file__).resolve().parents[2];M=R/'pilot/sim32';E=R/'evidence/sim32/runs';NAME='aeris-sim32-sitl';IMAGE='ubuntu@sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55'
def run(a):
 p=subprocess.run([str(x)for x in a],capture_output=True,text=True)
 if p.returncode:raise RuntimeError(p.stdout+p.stderr)
 return p.stdout.strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 mode,rid=sys.argv[1:3]
 if not rid.isalnum()or len(rid)>32:raise ValueError('Run ID')
 out=E/rid;state=R/'.local/sim32'/rid
 if mode=='start':
  load,wind=sys.argv[3:5]
  engine=os.environ.get('SIM32_ENGINE','optimized');speedup=os.environ.get('SIM32_SPEEDUP','1')
  if engine not in ['baseline','optimized'] or speedup not in ['1','1.05','1.10']:raise ValueError('Declared performance configuration allowlist')
  if load not in ['empty','central','offset']or wind not in ['calm','crosswind','gust']:raise ValueError('Profile allowlist')
  if out.exists()or state.exists():raise ValueError('Prior ID exists; preserve')
  assert shutil.disk_usage(R).free>20*1024**3+640*1024**2,'Resource peak admission'
  run(['docker','image','inspect',IMAGE]);assert subprocess.run(['docker','container','inspect',NAME],capture_output=True).returncode!=0,'Owned name occupied'
  for port,kind in [(5784,socket.SOCK_STREAM),(5785,socket.SOCK_STREAM),(5786,socket.SOCK_STREAM),(9002,socket.SOCK_DGRAM)]:
   with socket.socket(socket.AF_INET,kind)as s:s.bind(('127.0.0.1',port))
  E.mkdir(parents=True,exist_ok=True);log=(E/(rid+'-backend-console.txt')).open('x');child=subprocess.Popen([sys.executable,'-B',str(M/'backend.py'),rid,load,wind],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);log.close();cid=None
  try:
   for _ in range(50):
    if (out/'backend-identity.json').exists():break
    if child.poll()is not None:raise RuntimeError('Backend failed admission/start')
    time.sleep(.1)
   assert (out/'backend-identity.json').exists(),'Backend identity timeout'
   cmd=['docker','run','--rm','-d','--name',NAME,'--label','aeris.task=sim32','--label','aeris.run='+rid,'--platform','linux/amd64','--pull','never','--network','bridge','--cpus','2','--memory','384m','--cap-drop','ALL','--security-opt','no-new-privileges','--log-opt','max-size=2m','--log-opt','max-file=2','-p','127.0.0.1:5784:5760','-p','127.0.0.1:5785:5762','-p','127.0.0.1:5786:5763','-v',str(R/'runtime/sitl')+':/aeris:ro','-v',str(M)+':/sim32:ro','-v',str(state)+':/state','-w','/state',IMAGE,'/aeris/arducopter','-w','--model','JSON:192.168.65.254','--home','10.854,106.807,10,0','--defaults','/aeris/copter.parm,/sim32/sitl.parm','--serial1=tcp:5762:nowait','--serial2=tcp:5763:nowait','--rate','1200','--speedup',speedup]
   cid=run(cmd);receipt={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'run':rid,'containerId':cid,'backendPid':child.pid,'imageId':run(['docker','image','inspect',IMAGE,'--format','{{.Id}}']),'binarySha256':sha(R/'runtime/sitl/arducopter'),'modulePins':{str(p.relative_to(R)):sha(p)for p in sorted(p for p in M.rglob('*') if p.is_file() and p.suffix in ['.py','.mjs','.parm','.js','.css','.html','.c','.so'])},'command':cmd,'resourceAdmissionFreeBytes':shutil.disk_usage(R).free,'runtimeConfiguration':{'engine':engine,'requestedSpeedup':float(speedup),'rateHz':1200,'lockstep':True,'referencePhysicsSha256':sha(R/'evidence/sim32/source-final/pilot/sim32/physics.py')},'scope':'Owned actual ArduPilot JSON external provisional physics; simulated flight only'};(out/'launch.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
  except Exception:
   if cid:subprocess.run(['docker','stop','-t','3',cid],capture_output=True)
   if child.poll()is None:child.terminate();child.wait(timeout=5)
   raise
 elif mode=='stop':
  launch=json.loads((out/'launch.json').read_text());info=json.loads(run(['docker','container','inspect',NAME]))[0]
  assert info['Id']==launch['containerId']and info['Config']['Labels'].get('aeris.task')=='sim32'and info['Config']['Labels'].get('aeris.run')==rid,'Owned container identity'
  (out/'sitl-console.txt').write_text(run(['docker','logs',NAME]));(out/'container-before-stop.json').write_text(json.dumps(info,indent=2)+'\n');pid=launch['backendPid'];ps=subprocess.run(['ps','-p',str(pid),'-o','command='],capture_output=True,text=True).stdout
  if '/pilot/sim32/backend.py '+rid+' 'in ps:os.kill(pid,signal.SIGTERM)
  for _ in range(50):
   if (out/'backend-summary.json').exists():break
   time.sleep(.1)
  assert (out/'backend-summary.json').exists(),'Backend did not seal summary'
  run(['docker','stop','-t','3',NAME])
  assert not list(state.glob('*.BIN')),'Unexpected flight binary logs'
  shutil.rmtree(state);(out/'closure.json').write_text(json.dumps({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'ownedContainerStopped':True,'backendSummaryPresent':True,'removedState':str(state.relative_to(R)),'freeBytes':shutil.disk_usage(R).free},indent=2)+'\n');print(run(['docker','image','prune','-f']))
 else:raise ValueError('start|stop only')
if __name__=='__main__':main()
