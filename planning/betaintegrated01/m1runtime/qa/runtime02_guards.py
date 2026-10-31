"""Independent mathematical guard + explicit-intent JVM unit review. No runtime."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,shutil,subprocess,sys
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R))
source=R/'pilot/betaintegrated01/runtime02/journal/admission.py';spec=importlib.util.spec_from_file_location('guard02_independent',source);g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
out=R/('evidence/betaintegrated01-m1runtime/qa/runtime02-guards'+sys.argv[1]);out.mkdir();results=[]
sources=[source,R/'native/betaintegrated01/runtime02/src/vn/rtr/aeris/beta01runtime/PendingExplicitAction.java',R/'native/betaintegrated01/runtime02/src/vn/rtr/aeris/beta01runtime/RuntimeActivity.java']
pins=lambda:{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sources};before=pins()
def test(name,f):
 try:results.append({'id':name,'pass':True,'detail':f()})
 except Exception as e:results.append({'id':name,'pass':False,'error':type(e).__name__+':'+str(e)})
def primed():
 w=g.ForecastWindow()
 for i in range(151):w.observe(i*100000000,23*2**30-i*1000000,priming=True)
 assert w.primed;return w
def cadence():
 w=primed()
 for i in range(50000):w.observe(15000000000+i*1000,23*2**30-150000000)
 d=w.diagnostic();assert d['sampleCount']<=192 and d['historySpanNs']>=15000000000 and d['oldestSampleNs']==0
 return {'perRecordChecks':50000,'sampleCount':d['sampleCount'],'retainedSpanNs':d['historySpanNs']}
test('G01_50K_RECORD_CHECKS_KEEP_15S_HISTORY',cadence)
def burst():
 w=primed();d=w.observe(15000001000,23*2**30-250000000);assert d['reason']is None and d['forecastFreeBytes']>10*2**30+256*2**20;return d
test('G02_100MB_BURST_USES_FULL_WINDOW',burst)
def decline():
 w=primed()
 try:w.observe(15000001000,12*2**30);raise AssertionError('forecast accepted')
 except g.DiskGuardError as e:assert 'FORECAST15' in str(e);return e.diagnostic
test('G03_SUSTAINED_DECLINE_STILL_REJECTS',decline)
def floor():
 w=primed()
 try:w.observe(15000001000,10*2**30+256*2**20-1);raise AssertionError('floor accepted')
 except g.DiskGuardError as e:assert 'FLOOR10' in str(e);return e.diagnostic['reason']
test('G04_FLOOR_UNCHANGED',floor)
def unprimed():
 w=g.ForecastWindow()
 try:w.observe(0,23*2**30);raise AssertionError('unprimed accepted')
 except g.DiskGuardError as e:assert 'NOT_REAL_15S_PRIMED' in str(e);return str(e)
test('G05_UNPRIMED_REFUSES',unprimed)
def gap():
 w=primed()
 try:w.observe(18000000001,23*2**30);raise AssertionError('gap accepted')
 except g.DiskGuardError as e:assert 'OBSERVATION_GAP' in str(e);return str(e)
test('G06_GAP_REFUSES',gap)
classes=R/'native/betaintegrated01/.build/qa-runtime';classes.mkdir();jdk=Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home/bin');logs=[]
try:
 c=subprocess.run([str(jdk/'javac'),'--release','8','-d',str(classes),str(sources[1]),str(Path(__file__).with_name('PendingActionQA.java'))],capture_output=True,text=True,timeout=60);logs.append({'kind':'javac','exit':c.returncode,'stdout':c.stdout,'stderr':c.stderr})
 assert c.returncode==0,c.stderr
 r=subprocess.run([str(jdk/'java'),'-cp',str(classes),'PendingActionQA'],capture_output=True,text=True,timeout=60);logs.append({'kind':'java','exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr});results.append({'id':'P_JVM_PENDING_8_GROUPS','pass':r.returncode==0,'detail':json.loads(r.stdout)if r.returncode==0 else r.stderr})
finally:removed=len(list(classes.rglob('*.class')));shutil.rmtree(classes)
activity=sources[2].read_text();new_intent=next(l for l in activity.splitlines()if'void onNewIntent' in l);pause=next(l for l in activity.splitlines()if'void onPause' in l)
results.append({'id':'P_ACTIVITY_SOURCE_WIRING_ONLY','pass':'queueExplicit(intent)'in new_intent and 'action('not in new_intent and 'post(this::drainExplicit)'in activity and 'onPostResume' in activity and 'foreground=false' in pause and 'pendingActions.cancel' in pause and 'if(b==null)queueExplicit'in activity and 'FLAG_ACTIVITY_LAUNCHED_FROM_HISTORY'in activity,'scope':'Static source check, Android lifecycle behavior requires actual root replay'})
report={'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceBefore':before,'sourceAfter':pins(),'sourceChanged':before!=pins(),'results':results,'commands':logs,'classFilesRemoved':removed,'classPathExistsAfter':classes.exists(),'APAndroidSocketRuntimeLaunches':0,'realDiskGuardPrimingAttempted':False,'scope':'Synthetic ForecastWindow math only; actual DiskGuard not monkeypatched/injected; cached JDK purehelper execution. Not ART or15s actual priming proof'}
report['status']='PASS'if all(r['pass']for r in results)and before==pins()else'FAIL'
(out/'results.json').open('x').write(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'groups':len(results),'failed':[r['id']for r in results if not r['pass']],'sourceChanged':report['sourceChanged'],'classFilesRemoved':removed}))
