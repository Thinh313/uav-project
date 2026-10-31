"""One explicit loss intent, public BAPI payloadonly, realAndroid Home; no retries."""
from android_qa import *
from b_rpc import call,state
import importlib.util,signal,sys
owned();run=sys.argv[1];out=E/'runs'/run
sp=importlib.util.spec_from_file_location('m',R/'pilot/apstream40/oracle-v2.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
end=time.monotonic()+45
while time.monotonic()<end:
 parser=m.MAVLink(None);parser.robust_parsing=True;last={}
 for line in(out/'observer.jsonl').read_bytes().splitlines():
  r=json.loads(line)
  for f in parser.parse_buffer(bytes.fromhex(r['hex']))or[]:
   if f.get_srcSystem()==42 and f.get_srcComponent()==1:last[f.get_msgId()]=(int(r['hostMonoNs']),f)
 if all(k in last and time.monotonic_ns()-last[k][0]<2e9 for k in[0,33,245])and last[0][1].base_mode&128 and last[245][1].landed_state==2 and last[33][1].relative_alt>4000:break
 time.sleep(.25)
else:raise AssertionError('NO_FRESH_AIRBORNE_WITNESS_NO_CUT')
proof={str(k):{'hostMonoNs':str(at),'frame':f.to_dict()}for k,(at,f)in last.items()if k in[0,33,245]}
for op,res,a,b in [('claim','gimbal:center',0,0),('authority','gimbal:center',0,0),('gimbal','gimbal:center',-57,72),('claim','camera:center',0,0),('zoom','camera:center',58,0),('capture','camera:center',0,0),('claim','camera:front',0,0),('capture','camera:front',0,0)]:
 call('action',{'operation':op,'resource':res,'a':a,'b':b,'to':''});time.sleep(.3)
s=state();s.pop('csrf',None);assert s['connected']and s['authenticated']and s['state']['self']['alive']and s['state']['self']['joined'];capture(run+'-before-pilot-home')
# Refresh observer immediately before the fault, after payload actions and screenshot.
parser=m.MAVLink(None);parser.robust_parsing=True;last={}
for line in(out/'observer.jsonl').read_bytes().splitlines():
 r=json.loads(line)
 for f in parser.parse_buffer(bytes.fromhex(r['hex']))or[]:
  if f.get_srcSystem()==42 and f.get_srcComponent()==1:last[f.get_msgId()]=(int(r['hostMonoNs']),f)
assert all(k in last and time.monotonic_ns()-last[k][0]<2e9 for k in[0,33,245])and last[0][1].base_mode&128 and last[245][1].landed_state==2 and last[33][1].relative_alt>4000,'NO_FRESH_AIRBORNE_AT_CUT'
proof={str(k):{'hostMonoNs':str(at),'frame':f.to_dict()}for k,(at,f)in last.items()if k in[0,33,245]}
q={'atHostMonoNs':str(time.monotonic_ns()),'airborneObserver':proof,'B':s,'fault':'ACTUAL_ANDROID_KEYCODE_HOME','BHeartbeatIsOwnRuntime':True,'automaticRetry':False};(out/'pilot-loss-intent.json').open('x').write(json.dumps(q,indent=2));adb('shell','input','keyevent','KEYCODE_HOME');time.sleep(.8);capture(run+'-pilot-background')
s=state();s.pop('csrf',None);(out/'B-after-pilot-home.json').open('x').write(json.dumps(s,indent=2));print('ACTUAL_PILOT_BACKGROUND_WITH_B_ACTIVE',flush=True)
