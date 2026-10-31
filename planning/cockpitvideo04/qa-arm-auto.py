"""Root QA: observed-coordinate readonly preflight/arm, then strict visible AUTO OCR.
No flight POST, no TTL extension, no automatic retry. Prior screenshot required.
"""
from pathlib import Path
import importlib.util,json,time,sys,subprocess,re,math
s=importlib.util.spec_from_file_location('q',Path(__file__).with_name('qa-android.py'));q=importlib.util.module_from_spec(s);s.loader.exec_module(q)
a,reference,prefY,armY=sys.argv[1:];prefY,armY=int(prefY),int(armY);q.owned(a);assert(q.E/reference).is_file();v=q.state();run=v['flight']['run'];assert run and v['flight']['mode']=='sitl'and v['flight']['authority'];out=q.E/f'qa-arm-auto-{a}-{run}.json';assert not out.exists();log={'run':run,'reference':reference,'coordinates':{'preflight':[862,prefY],'arm':[1057,armY]},'controlHTTP':False}
def observe():
 v=q.state();f=v['flight'];assert f['run']==run and f['mode']=='sitl'
 if f['error']:raise RuntimeError(f['error'])
 return v,f
try:
 q.adb('shell','input','tap',862,prefY);end=time.monotonic()+20
 while time.monotonic()<end:
  v,f=observe()
  if not f['busy']and f['live']['preflight63']['ready']:break
  time.sleep(.1)
 assert f['live']['preflight63']['ready'];time.sleep(.35);q.capture(a,'android-before-arm-'+a);q.adb('shell','input','tap',1057,armY);end=time.monotonic()+15
 while time.monotonic()<end:
  v,f=observe()
  if not f['busy']and f['live']['stage']=='ARMED_HOME_REVIEW':break
  time.sleep(.1)
 assert f['live']['stage']=='ARMED_HOME_REVIEW';home=f['live']['homeReview']['postArmHome'];assert math.hypot((home['lat']-10.854)*111319,(home['lon']-106.807)*109300)<=1 and abs(home['amsl']-10)<=.5
 im=q.capture(a,'android-post-arm-home-'+a);rows=json.loads(subprocess.check_output([str(q.R/'.local/cockpitvideo04/qa-ocr-fast'),str(im)],timeout=2));log['ocrRows']=rows;hits=[r for r in rows if r['confidence']>=.45 and r['x']>=740 and 140<=r['y']<=650 and re.search(r'^\s*5',r['text'])and'AUTO'in r['text'].upper()];assert len(hits)==1,hits;r=hits[0];v,f=observe();assert f['autoGate']['eligible']and f['autoGate']['effectiveRemainingMs']>1800;log['homeReview']=f['live']['homeReview'];log['autoGateBeforeTap']=f['autoGate'];log['autoButton']=r;q.adb('shell','input','tap',round(r['x']+r['width']/2),round(r['y']+r['height']/2));end=time.monotonic()+15
 while time.monotonic()<end:
  v,f=observe()
  if f['live'].get('autoObserved')or f['live'].get('completion',{}).get('autoObserved'):break
  time.sleep(.1)
 assert f['live'].get('autoObserved')or f['live'].get('completion',{}).get('autoObserved');log['status']='AUTO_OBSERVED_REQUIRES_RAW_REPLAY';log['after']=v;q.capture(a,'android-auto-observed-'+a)
except BaseException as e:log['status']='PARTIAL_NO_RETRY';log['error']=str(e);raise
finally:
 with out.open('x')as f:json.dump(log,f,indent=2);f.write('\n')
 print(json.dumps({'status':log['status'],'run':run,'error':log.get('error')}))
