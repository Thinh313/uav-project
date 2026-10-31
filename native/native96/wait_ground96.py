from pathlib import Path
import sys,time,json,importlib.util
sys.dont_write_bytecode=True;R=Path(__file__).resolve().parents[2];D=R/'evidence/native96/runs'/sys.argv[1];s=importlib.util.spec_from_file_location('m',R/'pilot/apstream40/oracle-v2.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);end=time.monotonic()+180
while time.monotonic()<end:
 p=m.MAVLink(None);p.robust_parsing=True;latest={};armed=False
 for l in(D/'observer.jsonl').read_text().splitlines():
  r=json.loads(l)
  for f in p.parse_buffer(bytes.fromhex(r['hex']))or[]:
   if f.get_srcSystem()==42 and f.get_srcComponent()==1:
    latest[f.get_msgId()]=(int(r['hostMonoNs']),f)
    if f.get_msgId()==0:armed|=bool(f.base_mode&128)
 if armed and all(k in latest and time.monotonic_ns()-latest[k][0]<3e9 for k in[0,33,245])and not latest[0][1].base_mode&128 and latest[245][1].landed_state==1 and abs(latest[33][1].relative_alt)<1000:print('PASSIVE_FRESH_GROUND_DISARMED');break
 assert not(D/'closure.json').exists(),'RUNTIME_CLOSED_BEFORE_GROUND';time.sleep(1)
else:raise AssertionError('PASSIVE_GROUND_DEADLINE')
