"""Sequential six declared cases. One attempt per case; stop immediately on failure."""
import importlib.util,json,subprocess,sys,time
from pathlib import Path
spec=importlib.util.spec_from_file_location('q',Path(__file__).with_name('android-journey.py'));q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
owner=json.loads((q.R/'.local/missionbeta01/active/owner.json').read_text());host=str(Path(owner['run'])/'host');results=[]
try:
 for kind in ['polygon','corridor']:
  for i in [1,2,3]:
   run=q.nominal(kind,i)
   target=q.E/('receiver-'+run+'.json')
   with target.open('x')as f:subprocess.run(['node','pilot/missionbeta01/receiver.mjs',str(q.E/'history01'/(run+'.json'))],cwd=q.R,stdout=f,check=True)
   subprocess.run([sys.executable,'-B','planning/missionbeta01/independent-oracle.py',host,run],cwd=q.R,check=True)
   results.append({'kind':kind,'index':i,'run':run,'status':'PASS','sourcePins':'source-pins07.json'});q.log('FINAL_CASE_VERIFIED',results[-1]);print(json.dumps(results[-1]),flush=True)
except BaseException as e:
 q.log('CAMPAIGN_STOP_ON_FAILURE',{'error':repr(e),'completed':results});raise
finally:
 p=q.E/'final-campaign05.json'
 with p.open('x')as f:json.dump({'results':results,'status':'PASS'if len(results)==6 else'NOT_READY','noAutomaticRetry':True,'host':host,'actualImages':0},f,indent=2)
