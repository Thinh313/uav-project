from ui98 import *
import importlib.util
owned();run=sys.argv[1];out=E/'runs'/run;sp=importlib.util.spec_from_file_location('m',R/'pilot/apstream40/oracle-v2.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);meta=events98(run,'META')[0][1];needed={i['seq']for i in meta['document']['compiled']['plan']['compiled']['items']if i['seq']>0 and i['command']==16};end=time.monotonic()+200
from observer_tail03 import ObserverTail03
observer03=ObserverTail03(R,run)
while time.monotonic()<end:
 latest=observer03.read()
 if observer03.everArmed and needed<=observer03.reached and all(k in latest and time.monotonic_ns()-latest[k][0]<3e9 for k in[0,245,33])and not latest[0][1].base_mode&128 and latest[245][1].landed_state==1 and abs(latest[33][1].relative_alt)<1000:break
 if(out/'closure.json').exists():raise AssertionError('RUNTIME_CLOSED')
 time.sleep(.5)
else:raise AssertionError('OBSERVER_NOMINAL_GROUND_DEADLINE')
tap94('Preflight / Fly SITL');capture(run+'-ground');tap94('complete83');wait98(run,'CLOSED',seconds=6);capture(run+'-review-saved');journal(run+'-workspace-closed')
b=raw98(run);(out/'android-raw.jsonl').open('xb').write(b);raw=adb('exec-out','tar','-C','/data/user/0/'+P+'/files','-cf','-','workspaces','crew02','direct95/'+run);assert len(raw)<64*2**20;(out/'private-closed.tar').open('xb').write(raw);(out/'private-snapshot-scope.json').open('x').write(json.dumps({'scope':'Selected current-run full raw, all workspaces and crew public/audit files; excludes other already preserved runs and volatile UI logs','members':['workspaces','crew02','direct95/'+run],'allAppPrivateFiles':False,'rawFramesTruncated':False},indent=2))
with tarfile.open(fileobj=io.BytesIO(raw))as t:
 reviews=[]
 for e in t.getmembers():
  if e.isfile()and '/sitl/'in e.name and e.name.endswith('.bin'):
   q=json.loads(t.extractfile(e).read().split(b'\n',6)[6])
   if q['run']==run:reviews.append(q)
 assert len(reviews)==1 and reviews[0]['accepted']is True;assert reviews[0]['authorityRestorable']is False;(out/'review.json').open('x').write(json.dumps(reviews[0],ensure_ascii=False,indent=2))
(out/'stop-request.json').open('x').write('{"reason":"Nominal complete/raw and review saved; observer ground-disarm"}');print('NOMINAL_REVIEW_SAVED',flush=True)
