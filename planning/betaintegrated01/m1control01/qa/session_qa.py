from pathlib import Path
import datetime,hashlib,json,shutil,subprocess,sys
R=Path(__file__).resolve().parents[4];out=R/('evidence/betaintegrated01-m1control01/qa/session'+sys.argv[1]);out.mkdir();classes=R/'native/betaintegrated01/.build/qa-control';classes.mkdir()
core=R/'native/betaintegrated01/control01/src/vn/rtr/aeris/control01';base=R/'native/betaintegrated01/runtime/src/vn/rtr/aeris';foundation=R/'native/betaintegrated01/src/vn/rtr/aeris/betaintegrated01'
src=[(R/'native/betaintegrated01/control02/src/vn/rtr/aeris/control01'/n if n=='ControlFlight.java'and len(sys.argv)>2 and sys.argv[2]=='control02'else core/n) for n in ['ControlAuthority.java','ControlFlight.java','ControlSession.java','RcWire.java']]+[base/'beta01runtime'/n for n in ['Values.java','Mavlink.java','NativeSegments.java']]+[base/'native98'/n for n in ['Dialect95.java','Json.java']]+[foundation/n for n in ['RunLifecycle.java','ProviderDescriptor.java']]+[Path(__file__).with_name(n)for n in ['ProfileFixture.java','SessionQA.java']]
pins=lambda:{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in src};before=pins();jdk=Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home/bin');logs=[];results=[]
try:
 c=subprocess.run([str(jdk/'javac'),'--release','8','-d',str(classes),*map(str,src)],capture_output=True,text=True,timeout=60);logs.append({'kind':'javac','exit':c.returncode,'stdout':c.stdout,'stderr':c.stderr})
 if c.returncode==0:
  r=subprocess.run([str(jdk/'java'),'-cp',str(classes),'SessionQA',str(out/'fixtures')],capture_output=True,text=True,timeout=90);logs.append({'kind':'java','exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr});results=json.loads(r.stdout)['results']if r.returncode==0 else[]
finally:count=len(list(classes.rglob('*.class')));shutil.rmtree(classes)
report={'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceBefore':before,'sourceAfter':pins(),'sourceChanged':before!=pins(),'commands':logs,'results':results,'status':'PASS'if results and all(r['pass']for r in results)and before==pins()else'FAIL','classFilesRemoved':count,'classOutputExistsAfter':classes.exists(),'APAndroidSocketLaunches':0,'scope':'Independent actualControlSession/NativeSegments functions withrealfsync andsyntheticAP/mockedSocket; noflight/physicalinput proof'}
(out/'results.json').open('x').write(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'groups':len(results),'failed':[r['id']for r in results if not r['pass']],'sourceChanged':report['sourceChanged']}))
