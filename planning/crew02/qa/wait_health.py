from ui98 import *
import importlib.util
owned();run=sys.argv[1];out=E/'runs'/run;sp=importlib.util.spec_from_file_location('m',R/'pilot/apstream40/oracle-v2.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);end=time.monotonic()+80
while time.monotonic()<end:
 rows=rows98(run)
 closed=[r for r in rows if r['kind']=='CLOSED']
 if closed:raise AssertionError('CLOSED:'+base64.b64decode(closed[-1]['dataBase64']).decode())
 p=m.MAVLink(None);p.robust_parsing=True;latest={}
 for r in rows:
  if r['kind']!='RX':continue
  for f in p.parse_buffer(base64.b64decode(r['dataBase64']))or[]:
   if f.get_srcSystem()==42 and f.get_srcComponent()==1:latest[f.get_msgId()]=(r['elapsedMs'],f)
 now=float(adb('shell','cat','/proc/uptime').split()[0])*1000
 if all(k in latest and now-latest[k][0]<2500 for k in[0,1,24,33,193,242,245]):
  sysf=latest[1][1];ekf=latest[193][1]
  if sysf.onboard_control_sensors_health&268435456 and ekf.flags&63==63 and not ekf.flags&(128|1024):
   (out/'native-readonly-health.json').open('x').write(json.dumps({'status':'PASS','atAndroidMs':now,'latest':{str(k):{'atMs':at,'frame':f.to_dict()}for k,(at,f)in latest.items()if k in[0,1,24,33,193,242,245]},'note':'Passive wait only, not a replacement for fresh preflight cohort'},indent=2));print('NATIVE_PASSIVE_HEALTH_READY');break
 time.sleep(1)
else:raise AssertionError('HEALTH_WARMUP_DEADLINE_NO_GRANT')
