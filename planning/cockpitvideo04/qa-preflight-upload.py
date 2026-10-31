"""Root-only observed UI taps, with readonly state gates. No flight control HTTP."""
from pathlib import Path
import importlib.util,json,time,sys
s=importlib.util.spec_from_file_location('q',Path(__file__).with_name('qa-android.py'));q=importlib.util.module_from_spec(s);s.loader.exec_module(q)
a,reference,prefY,grantY,uploadY=sys.argv[1:];prefY,grantY,uploadY=map(int,[prefY,grantY,uploadY]);q.owned(a);assert(q.E/reference).is_file();f=q.state()['flight'];run=f['run'];assert run and f['mode']=='sitl'and not f['authority'];out=q.E/f'qa-preflight-upload-{a}-{run}.json';assert not out.exists();log={'run':run,'reference':reference,'coordinates':{'preflight':[862,prefY],'grant':[1057,grantY],'upload':[862,uploadY]},'controlHTTP':False}
def wait(pred,limit):
 end=time.monotonic()+limit
 while time.monotonic()<end:
  v=q.state();f=v['flight'];assert f['run']==run and f['mode']=='sitl'
  if f['error']:raise RuntimeError(f['error'])
  if pred(f):return v
  time.sleep(.15)
 raise TimeoutError('NO_AUTOMATIC_RETRY')
try:
 q.adb('shell','input','tap',862,prefY);log['preflight']=wait(lambda f:not f['busy']and f['live']['preflight63']['ready'],95);time.sleep(.35);q.capture(a,'android-before-grant-'+a);q.adb('shell','input','tap',1057,grantY);log['grant']=wait(lambda f:bool(f['authority']),3);time.sleep(.35);q.capture(a,'android-before-upload-'+a);q.adb('shell','input','tap',862,uploadY);log['readback']=wait(lambda f:not f['busy']and bool(f['live'].get('readback63')),30);q.capture(a,'android-readback-'+a);log['status']='OBSERVED_EXACT_READBACK_REQUIRES_RAW_REPLAY'
except BaseException as e:log['status']='PARTIAL_NO_RETRY';log['error']=str(e);raise
finally:
 with out.open('x')as f:json.dump(log,f,indent=2);f.write('\n')
 print(json.dumps({'status':log['status'],'run':run,'error':log.get('error')}))
