"""Scoped source projection. Never executes an old CLI or writes old output paths."""
from pathlib import Path
import hashlib,json,datetime,shutil,time
R=Path(__file__).resolve().parents[2]
from guard import budget
BUDGET=budget();STOP=datetime.datetime.fromisoformat(BUDGET['runtimeStopUTC']).timestamp();MAX_AP_SECONDS=min(300,BUDGET.get('maxAPSeconds',210))
def read(kind):
 p=R/'pilot/simtrain53'/kind;s=p.read_text();return p,s

def backend_source():
 p,s=read('backend.py');s=s.replace('simtrain53','simhand01').replace('SIMTRAIN53','SIMHAND01')
 s=s.replace('frames < 144000','frames < '+str(MAX_AP_SECONDS*1200)).replace('> 150:', '> '+str(MAX_AP_SECONDS)+' or time.time() >= '+repr(STOP)+':')
 s=s.replace('limit=384*2**20','limit='+str(768 if MAX_AP_SECONDS>210 else 512)+'*2**20')
 s=s.replace('20*2**30+512*2**20','10*2**30+256*2**20')
 return p,s

def runtime_source():
 p,s=read('runtime.py');s=s.replace('simtrain53','simhand01')
 start=s.index("    assert shutil.disk_usage(R).free > 24*2**30")
 end=s.index('    image_id = command',start)
 s=s[:start]+'''    from guard import admit_ap
    admit_ap(rid)
    global NAME
    NAME='aeris-simhand01-'+rid
    assert subprocess.run(['docker','container','inspect',NAME],capture_output=True).returncode != 0
    for port, kind in [(9002,socket.SOCK_DGRAM),(9004,socket.SOCK_DGRAM),(9005,socket.SOCK_DGRAM),(5870,socket.SOCK_STREAM)]:
        with socket.socket(socket.AF_INET,kind) as channel: channel.bind(('127.0.0.1',port))
'''+s[end:]
 s=s.replace("['docker','run','--rm','-d'", "['docker','run','-d'")
 s=s.replace('deadline=time.monotonic()+150', 'deadline=min(time.monotonic()+'+str(MAX_AP_SECONDS)+',time.monotonic()+max(0,'+repr(STOP)+'-time.time()))')
 s=s.replace('20*2**30+768*2**20','10*2**30+256*2**20')
 s=s.replace("'backendPid':proc.pid,'containerId':cid", "'backendPid':proc.pid,'containerName':NAME,'containerId':cid")
 s=s.replace("'peakBudgetBytes':2*2**30", "'peakBudgetBytes':512*2**20")
 return p,s

def readback_source():
 p,s=read('readback.py');return p,s.replace('simtrain53','simhand01').replace('SIMTRAIN53','SIMHAND01')

def execute(kind,file):
 p,s={'backend':backend_source,'runtime':runtime_source,'readback':readback_source}[kind]()
 ns={'__name__':'__main__','__file__':str(file)}
 exec(compile(s,str(file)+'#'+hashlib.sha256(s.encode()).hexdigest(),'exec'),ns)
