"""Read-only G0 inventory; never launches a simulator or changes system settings."""
from pathlib import Path
import json,subprocess,datetime,hashlib,sys,shutil
R=Path(__file__).resolve().parents[2];E=R/'evidence/simtrain52'
def cmd(a):
 p=subprocess.run(a,capture_output=True,text=True,timeout=20);return {'args':a,'exit':p.returncode,'stdout':p.stdout[:12000],'stderr':p.stderr[:1000]}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert shutil.disk_usage(R).free>20*2**30+32*2**20
 machine={n:cmd(a)for n,a in {'model':['sysctl','-n','hw.model'],'memory':['sysctl','-n','hw.memsize'],'cpu':['sysctl','-n','hw.ncpu'],'gpu':['system_profiler','SPDisplaysDataType','-json'],'power':['pmset','-g','batt'],'os':['sw_vers'],'docker':['docker','version','--format','{{json .}}']}.items()}
 free=shutil.disk_usage(R).free
 # Inherited minimum from sim32-pipe03 is retained; not optimized down to fit current disk.
 cases={'foundation':{'taskBytes':32*2**20,'runtimeBytes':0,'marginBytes':32*2**20},'short_live_inherited':{'taskBytes':1024*2**20,'runtimeBytes':0,'marginBytes':512*2**20},'council18min_illustrative':{'rawBytes':5308416000,'walBytes':5308416000,'videoBytes':1080000000,'imagesBytes':1200000000,'exportStageBytes':6508416000,'runtimeBytes':256*2**20,'marginBytes':1024*2**20}}
 admission={n:{'components':c,'peakBytes':sum(c.values()),'requiredFreeBytes':20*2**30+sum(c.values()),'admitted':free>=20*2**30+sum(c.values()),'deficitBytes':max(0,20*2**30+sum(c.values())-free),'qualification':'foundation gate only'if n=='foundation'else'inherited short-launch minimum'if n=='short_live_inherited'else'illustrative pessimistic case; not measured workload'}for n,c in cases.items()}
 pins={str(p.relative_to(R)):sha(p)for p in [R/'pilot/sim32/physics.py',R/'evidence/sim32/source-final/pilot/sim32/physics.py',R/'pilot/sim32-pipe03/fast_physics.py',R/'pilot/sim32/_sim32_kernel.cpython-314-darwin.so',R/'runtime/sim32-pipe03-build/host-native/_sim32_integrator.cpython-314-darwin.so',R/'runtime/sim32-instrument01-build/ardupilot/build/sitl/bin/arducopter',R/'pilot/sim32/viewer/vendor/three.core.js',R/'pilot/sim32/viewer/vendor/three.module.js',R/'pilot/sim32/viewer/vendor/THREE-LICENSE.txt']}
 out={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'FOUNDATION_ADMITTED_LIVE_BLOCKED'if not admission['short_live_inherited']['admitted']else'RESOURCE_ADMISSION_ONLY_NOT_LIVE_ACCEPTANCE','machine':machine,'freeBytes':free,'admission':admission,'pins':pins,'liveStarted':False,'g0':'PARTIAL_PROJECTOR_INPUT_NOT_CHECKED','g1':'NOT_RUN_RESOURCE_GATE','actualProjector':'NOT_CONNECTED_AT_OBSERVATION','gamepad':'NOT_CHECKED','herespecificProfile':'NOT_CALIBRATED_REFERENCE_QUAD_X','noSystemSettingsChanged':True}
 with(E/'admission1.json').open('x')as f:json.dump(out,f,indent=2);f.write('\n')
 print(json.dumps({'status':out['status'],'freeGiB':round(free/2**30,3),'shortLiveDeficitGiB':round(admission['short_live_inherited']['deficitBytes']/2**30,3)}))
if __name__=='__main__':main()
