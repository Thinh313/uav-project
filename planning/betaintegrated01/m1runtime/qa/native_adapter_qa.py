from pathlib import Path
import datetime,hashlib,json,os,shutil,subprocess,sys
R=Path(__file__).resolve().parents[4]
out=R/('evidence/betaintegrated01-m1runtime/qa/native-adapter'+sys.argv[1]);out.mkdir()
classes=R/'native/betaintegrated01/.build/qa-runtime';classes.mkdir()
source=R/'native/betaintegrated01/runtime/src'
files=list((source/'vn/rtr/aeris/native98').glob('*.java'))+[source/'vn/rtr/aeris/beta01runtime'/n for n in ['NativeSegments.java','RuntimeSession.java','FlightReadiness.java','Mavlink.java','Values.java']]
files.extend(R/'native/betaintegrated01/src/vn/rtr/aeris/betaintegrated01'/n for n in ['RunLifecycle.java','ProviderDescriptor.java'])
files.append(Path(__file__).with_name('NativeAdapterQA.java'))
pins=lambda:{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
before=pins();j=Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home/bin')
commands=[]
try:
 c=subprocess.run([str(j/'javac'),'--release','8','-d',str(classes),*map(str,files)],capture_output=True,text=True,timeout=60)
 commands.append({'kind':'javac','exit':c.returncode,'stdout':c.stdout,'stderr':c.stderr})
 if c.returncode==0:
  run=subprocess.run([str(j/'java'),'-cp',str(classes),'NativeAdapterQA',str(out/'fixtures')],capture_output=True,text=True,timeout=60)
  commands.append({'kind':'java','exit':run.returncode,'stdout':run.stdout,'stderr':run.stderr})
  result=json.loads(run.stdout) if run.returncode==0 else {'results':[]}
 else:result={'results':[]}
finally:
 count=len(list(classes.rglob('*.class')));shutil.rmtree(classes)
receipt={'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceBefore':before,'sourceAfter':pins(),'sourceChanged':before!=pins(),'commands':commands,'results':result['results'],'classFilesRemoved':count,'classPathExistsAfter':classes.exists(),'APAndroidSocketRuntimeLaunches':0,'artifactBuildsOrSignings':0}
receipt['status']='PASS' if receipt['results'] and all(r['pass'] for r in receipt['results']) and before==pins() else 'FAIL'
(out/'results.json').open('x').write(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'status':receipt['status'],'checks':len(receipt['results']),'failed':[r['id'] for r in receipt['results'] if not r['pass']],'sourceChanged':receipt['sourceChanged'],'removedClassFiles':count}))
