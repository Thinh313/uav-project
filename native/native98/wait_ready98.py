from pathlib import Path
import time,json,sys,importlib.util
sys.dont_write_bytecode=True;R=Path(__file__).resolve().parents[2];out=R/'evidence/native98/runs'/sys.argv[1];sp=importlib.util.spec_from_file_location('m',R/'pilot/apstream40/oracle-v2.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);end=time.monotonic()+60
while time.monotonic()<end:
 file=out/'observer.jsonl'
 if not file.exists():time.sleep(.3);continue
 p=m.MAVLink(None);p.robust_parsing=True;latest={}
 for line in file.read_bytes().splitlines():
  r=json.loads(line)
  for f in p.parse_buffer(bytes.fromhex(r['hex']))or[]:
   if f.get_srcSystem()==42 and f.get_srcComponent()==1:latest[f.get_msgId()]=(int(r['hostMonoNs']),f)
 if all(k in latest and time.monotonic_ns()-latest[k][0]<3e9 for k in [0,24,33,242,245])and latest[24][1].fix_type>=3 and latest[24][1].satellites_visible>=6 and latest[24][1].eph!=65535 and latest[242][1].latitude!=0 and latest[245][1].landed_state==1 and not latest[0][1].base_mode&128:
  (out/'observer-readonly-ready.json').open('x').write(json.dumps({'status':'PASS','hostGCSBytes':0,'latest':{str(k):{'hostMonoNs':n,'frame':f.to_dict()}for k,(n,f)in latest.items()if k in [0,24,33,242,245]}},indent=2));print('PASSIVE_GNSS_HOME_GROUND_READY');break
 if(out/'closure.json').exists():raise AssertionError('RUNTIME_CLOSED')
 time.sleep(.5)
else:raise AssertionError('PASSIVE_READY_DEADLINE_NO_GRANT')
