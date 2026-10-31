from pathlib import Path
import json,time,sys,importlib.util
sys.dont_write_bytecode=True;R=Path(__file__).resolve().parents[2];D=R/'evidence/native96/runs'/sys.argv[1];spec=importlib.util.spec_from_file_location('ready96',R/'pilot/apstream40/oracle-v2.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);end=time.monotonic()+80
while time.monotonic()<end:
 parser=m.MAVLink(None);parser.robust_parsing=True;last={}
 for line in(D/'observer.jsonl').read_text().splitlines():
  row=json.loads(line)
  for f in parser.parse_buffer(bytes.fromhex(row['hex']))or[]:
   if f.get_srcSystem()==42 and f.get_srcComponent()==1:last[f.get_msgId()]=(f,row)
 if all(i in last for i in[0,1,24,33,193,242,245]):
  if last[1][0].onboard_control_sensors_enabled&last[1][0].onboard_control_sensors_health&0x10000000 and last[193][0].flags&55==55 and last[33][0].time_boot_ms>=30000 and not last[0][0].base_mode&128 and all(time.monotonic_ns()-int(last[i][1]['hostMonoNs'])<3e9 for i in[0,1,33,245]):print('PASSIVE_AP_READY');break
 time.sleep(1)
else:raise AssertionError('AP_READONLY_WARMUP_GATE')
